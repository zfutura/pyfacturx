"""Common types for PyFactur-X."""

from decimal import Decimal
from typing import TypeAlias

from .quantities import QuantityCode
from .type_codes import IdentifierSchemeCode, ReferenceQualifierCode

# (ID, scheme ID)
# The scheme ID must be from the ISO/IEC 6523 list.
ID: TypeAlias = tuple[str, IdentifierSchemeCode | str | None]
Quantity: TypeAlias = tuple[Decimal, QuantityCode]
OptionalQuantity: TypeAlias = tuple[Decimal, QuantityCode | None]
# (content, mime type, filename)
Attachment: TypeAlias = tuple[bytes, str, str]
# (issuer assigned ID, reference type code)
DocRef: TypeAlias = tuple[str | None, ReferenceQualifierCode | None]
