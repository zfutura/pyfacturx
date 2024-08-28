import locale
import re
from decimal import Decimal
from typing import Literal, cast


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

    def __str__(self) -> str:
        conv = locale.localeconv()
        # Check for C locale, in which case locale.currency() raises an error.
        if conv["int_frac_digits"] == 127:  # C locale
            return f"{self.currency} {self.amount}"

        formatted_amount = locale.currency(
            self.amount, symbol=False, grouping=True
        )

        precedes = cast(
            Literal[0, 1],
            conv[self.amount < 0 and "n_cs_precedes" or "p_cs_precedes"],
        )
        separated = cast(
            Literal[0, 1],
            conv[self.amount < 0 and "n_sep_by_space" or "p_sep_by_space"],
        )

        if precedes:
            return self.currency + (separated and " " or "") + formatted_amount
        else:
            currency = (
                self.currency[:-1]
                if self.currency.endswith(" ")
                else self.currency
            )
            return formatted_amount + (separated and " " or "") + currency


_ISO_4217_RE = re.compile(r"^[A-Z]{3}$")


def validate_iso_4217_currency(currency: str) -> None:
    """Validate an ISO 4217 currency code.

    Raise a ValueError if the currency code does not match ISO 4217 format.
    This does not check whether the currency code is actually defined in
    ISO 4217.
    """
    if not _ISO_4217_RE.match(currency):
        raise ValueError(f"Invalid ISO 4217 currency code: {currency}")
