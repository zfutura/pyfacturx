class FacturXError(Exception):
    """Base class for Factur-X exceptions."""


class PDFError(FacturXError):
    """Base class for PDF processing exceptions."""


class PDFParseError(FacturXError):
    """Raise when a PDF file cannot be processed."""


class NoFacturXError(PDFParseError):
    """Raised when a PDF file does not contain a Factur-X XML file."""


class ModelError(FacturXError):
    """Raised when a Factur-X model is invalid."""


class FacturXParseError(FacturXError):
    """Base class for Factur-X parsing exceptions."""


class XMLParseError(FacturXParseError):
    """Raised when an XML file cannot be parsed."""


class NotFacturXError(FacturXParseError):
    """Raised when an XML file is not a Factur-X file."""


class UnsupportedProfileError(FacturXParseError):
    """Raised when a Factur-X file uses an unsupported profile."""


class InvalidXMLError(FacturXParseError):
    """Raised when a Factur-X XML file has the wrong structure."""


class InvalidProfileError(FacturXParseError):
    """Raised when a Factur-X file is invalid for the specified profile."""

    def __init__(self, profile_name: str, message: str) -> None:
        super().__init__(message)
        self.profile_name = profile_name
