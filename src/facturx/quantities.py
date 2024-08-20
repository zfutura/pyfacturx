"""
Quantities defined in UNECE/CEFACT Trade Facilitation Recommendations
No.20 and No.21.

https://unece.org/trade/uncefact/cl-recommendations
"""

from enum import StrEnum


class QuantityCode(StrEnum):
    """
    Selected quantities defined in UNECE/CEFACT Trade Facilitation
    Recommendations No.20 and No.21.
    """

    ONE = "C62"  # aka "unit"
    PIECE = "H87"  # aka "item"
    HOUR = "HUR"
    DAY = "DAY"
    LITER = "LTR"
    CUBIC_METERS = "MTQ"
    KILOGRAM = "KGM"
    METERS = "MTR"
    TON = "TNE"
