class FacturXError(Exception):
    """Base class for Factur-X exceptions."""


class ModelError(FacturXError):
    """Raised when a Factur-X model is invalid."""
