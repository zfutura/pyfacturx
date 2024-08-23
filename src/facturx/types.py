"""Common types for PyFactur-X."""

from decimal import Decimal
from typing import TypeAlias

from .quantities import QuantityCode
from .type_codes import ReferenceQualifierCode

# (ID, scheme ID)
# The scheme ID must be from the ISO/IEC 6523 list.
ID: TypeAlias = tuple[str, str]
Quantity: TypeAlias = tuple[Decimal, QuantityCode]
# (content, mime type, filename)
Attachment: TypeAlias = tuple[bytes, str, str]
# (issuer assigned ID, reference type code)
DocRef: TypeAlias = tuple[str | None, ReferenceQualifierCode | None]
