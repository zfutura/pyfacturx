"""Common types for PyFactur-X."""

from decimal import Decimal
from typing import TypeAlias

from .quantities import QuantityCode

# (ID, scheme ID)
# The scheme ID must be from the ISO/IEC 6523 list.
ID: TypeAlias = tuple[str, str]
Quantity: TypeAlias = tuple[Decimal, QuantityCode]
# (amount, unit code) or just amount
Money: TypeAlias = tuple[Decimal, str] | Decimal
# (content, mime type, filename)
Attachment: TypeAlias = tuple[bytes, str, str]
