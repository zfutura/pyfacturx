import re


def validate_iso_3166_1_alpha_2(code: str) -> bool:
    """Validate an ISO 3166-1 country code in ALPHA-2 format."""
    return re.match(r"^[A-Z]{2}$", code) is not None
