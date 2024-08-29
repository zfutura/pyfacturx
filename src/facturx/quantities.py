"""
Quantities defined in UNECE/CEFACT Trade Facilitation Recommendations
No.20 and No.21.

https://unece.org/trade/uncefact/cl-recommendations
"""

from enum import StrEnum


def N_(s: str) -> str:
    return s


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


# Mapping between QuantityCode and its names, either in singular and plural
# forms (as a tuple, localizable) or as a unit symbol (str, not localizable).
QUANTITY_NAMES: dict[QuantityCode, tuple[str, str] | str] = {
    QuantityCode.ONE: (N_("unit"), N_("units")),
    QuantityCode.PIECE: (N_("pc"), N_("pcs")),
    QuantityCode.HOUR: "h",
    QuantityCode.DAY: (N_("day"), N_("days")),
    QuantityCode.LITER: "l",
    QuantityCode.CUBIC_METERS: "m²",
    QuantityCode.KILOGRAM: "kg",
    QuantityCode.METERS: "m",
    QuantityCode.TON: "t",
}
