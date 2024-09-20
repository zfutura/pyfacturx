import sys
from enum import Enum
from pathlib import Path
from typing import Final

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from ._locale import setup_locale
from .exc import NoFacturXError, PDFParseError

_ = setup_locale()

FACTURX_FILENAME: Final = "factur-x.xml"
XRECHNUNG_FILENAME: Final = "xrechnung.xml"


class FileRelationship(Enum):
    """The relationship between a PDF file and an embedded file.

    * DATA: The embedded file contains data that is displayed in the PDF file.
    * SOURCE: The embedded file is the source data for the PDF file.
    * ALTERNATIVE: The embedded file is an alternative representation of
      the PDF file.
    * SUPPLEMENT: The embedded file contains information that supplements
      the data in the PDF file.
    """

    DATA = "Data"
    SOURCE = "Source"
    ALTERNATIVE = "Alternative"
    SUPPLEMENT = "Supplement"


def extract_facturx_from_pdf(
    filename: str | Path,
) -> tuple[str, FileRelationship | None]:
    """Extract the Factur-X XML file from a PDF file.

    If the PDF file cannot be processed, a PDFParseError is raised. If it
    does not contain a Factur-X XML file, a NoFacturXError is raised.
    """

    try:
        pdf = PdfReader(filename)
    except PdfReadError as exc:
        raise PDFParseError(_("Cannot read PDF file: {}").format(exc)) from exc
    try:
        # TODO: Support /Kids nodes
        doc = pdf.trailer["/Root"]["/Names"]["/EmbeddedFiles"]["/Names"]  # type: ignore[index]
        while doc:
            if doc[0] == FACTURX_FILENAME:
                break
        obj = doc[1]
        relationship: FileRelationship | None = None
        rel_s = obj.get("/AFRelationship")
        if rel_s is not None:
            relationship = FileRelationship(obj["/AFRelationship"][1:])
        file = obj["/EF"]["/F"]
        if file["/Subtype"] != "/text/xml":
            raise NoFacturXError(_("No Factur-X invoice found in PDF file"))
    except (KeyError, IndexError, ValueError) as exc:
        raise NoFacturXError(
            _("No Factur-X invoice found in PDF file")
        ) from exc
    return file.get_data().decode("utf-8"), relationship


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} PDF-FILE", file=sys.stderr)
        sys.exit(1)
    stream, relationship = extract_facturx_from_pdf(sys.argv[1])
    print("Relationship:", relationship)
    with open("facturx.xml", "w") as target_stream:
        target_stream.write(stream)


if __name__ == "__main__":
    main()
