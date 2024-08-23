from decimal import Decimal

from .money import Money


class TestMoney:
    def test_init(self) -> None:
        money1 = Money("100.00", "EUR")
        assert money1.amount == Decimal("100.00")
        assert money1.currency == "EUR"

        money2 = Money(Decimal("100.00"), "EUR")
        assert money2.amount == Decimal("100.00")
        assert money2.currency == "EUR"

        assert money1 == money2

    def test_eq(self) -> None:
        assert Money("100.00", "EUR") == Money("100.00", "EUR")
        assert Money("100.00", "EUR") == Money(Decimal("100.00"), "EUR")
        assert Money("100.00", "EUR") != Money("100.00", "USD")
        assert Money("100.00", "EUR") != Money("200.00", "EUR")
        assert Money("100.00", "EUR") != Money("100", "EUR")
