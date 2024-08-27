import re
from decimal import Decimal


class Money:
    """An amount of money in a certain currency.

    Initialize with a string with the correct amount of decimal places and
    an ISO 4217 currency code.

    >>> money = Money("33.13", "EUR")
    >>> money.amount
    Decimal('33.13')
    >>> money.currency
    'EUR'

    Alternatively, you can initialize with a Decimal object:

    >>> assert Money(Decimal("33.13"), "EUR") == Money("33.13", "EUR")
    """

    def __init__(self, amount: str | Decimal, currency: str) -> None:
        validate_iso_4217_currency(currency)
        if isinstance(amount, str):
            self.amount = Decimal(amount)
        elif isinstance(amount, Decimal):
            self.amount = amount
        else:
            raise TypeError("Amount must be a str or Decimal")
        self.currency = currency

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Money):
            if (self.amount, self.currency) != (
                value.amount,
                value.currency,
            ):
                return False
            if (
                self.amount.as_tuple().exponent
                != value.amount.as_tuple().exponent
            ):
                return False
            return True
        return NotImplemented

    def __repr__(self) -> str:
        return f"Money('{str(self.amount)}', {self.currency!r})"


_ISO_4217_RE = re.compile(r"^[A-Z]{3}$")


def validate_iso_4217_currency(currency: str) -> None:
    """Validate an ISO 4217 currency code.

    Raise a ValueError if the currency code does not match ISO 4217 format.
    This does not check whether the currency code is actually defined in
    ISO 4217.
    """
    if not _ISO_4217_RE.match(currency):
        raise ValueError(f"Invalid ISO 4217 currency code: {currency}")
