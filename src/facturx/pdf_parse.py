from pathlib import Path
from typing import Final

from ._locale import setup_locale
from .const import (
    URN_BASIC_PROFILE,
    URN_BASIC_WL_PROFILE,
    URN_EN16931_PROFILE,
    URN_EXTENDED_PROFILE,
    URN_MINIMUM_PROFILE,
    URN_XRECHNUNG_PROFILE,
)
from .exc import NoFacturXError
from .model import MinimumInvoice
from .parse import parse_xml
from .pdf_extract import FileRelationship, extract_facturx_from_pdf

_ = setup_locale()


def parse_pdf(
    filename: str | Path, *, country: str | None = None
) -> MinimumInvoice:
    """Parse a Factur-X invoice from a PDF file.

    Set the "country" parameter to an ISO 3166-1 alpha-2 country code to
    validate the invoice according to the country-specific rules,
    """
    data, relationship = extract_facturx_from_pdf(filename)
    invoice = parse_xml(data)
    _validate_relationship(invoice.PROFILE_URN, relationship, country=country)
    return invoice


_VALID_RELATIONSHIPS_FRANCE: Final[dict[str, set[FileRelationship]]] = {
    URN_MINIMUM_PROFILE: {
        FileRelationship.DATA,
    },
    URN_BASIC_WL_PROFILE: {
        FileRelationship.DATA,
    },
    URN_BASIC_PROFILE: {
        FileRelationship.ALTERNATIVE,
        FileRelationship.SOURCE,
        FileRelationship.DATA,
    },
    URN_EN16931_PROFILE: {
        FileRelationship.ALTERNATIVE,
        FileRelationship.SOURCE,
        FileRelationship.DATA,
    },
    URN_EXTENDED_PROFILE: {
        FileRelationship.ALTERNATIVE,
        FileRelationship.SOURCE,
        FileRelationship.DATA,
    },
    URN_XRECHNUNG_PROFILE: set(),
}

_VALID_RELATIONSHIPS_GERMANY: Final[dict[str, set[FileRelationship]]] = {
    URN_MINIMUM_PROFILE: {
        FileRelationship.DATA,
    },
    URN_BASIC_WL_PROFILE: {
        FileRelationship.DATA,
    },
    URN_BASIC_PROFILE: {
        FileRelationship.ALTERNATIVE,
    },
    URN_EN16931_PROFILE: {
        FileRelationship.ALTERNATIVE,
    },
    URN_EXTENDED_PROFILE: {
        FileRelationship.ALTERNATIVE,
    },
    URN_XRECHNUNG_PROFILE: {
        FileRelationship.ALTERNATIVE,
    },
}


def _validate_relationship(
    profile: str,
    relationship: FileRelationship | None,
    *,
    country: str | None = None,
) -> None:
    """Validate that the PDF file relationship matches the Factur-X invoice.

    See Factur-X 1.0.07, section 6.2.2.
    """
    if relationship is None:
        return

    match country:
        case "fr":
            rel_map = _VALID_RELATIONSHIPS_FRANCE
        case "de":
            rel_map = _VALID_RELATIONSHIPS_GERMANY
        case _:
            return

    if relationship not in rel_map[profile]:
        raise NoFacturXError(
            _("Invalid relationship for Factur-X Minimum invoice")
        )
