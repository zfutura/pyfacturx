from datetime import date
from decimal import Decimal

from facturx.model import (
    BasicInvoice,
    BasicWLInvoice,
    EN16931Invoice,
    EN16931LineItem,
    IncludedNote,
    LineItem,
    MinimumInvoice,
    PaymentTerms,
    PostalAddress,
    Tax,
    TradeParty,
)
from facturx.money import Money
from facturx.quantities import QuantityCode
from facturx.type_codes import (
    DocumentTypeCode,
    IdentifierSchemeCode,
    TaxCategoryCode,
    TextSubjectCode,
)


def minimum_rechnung() -> MinimumInvoice:
    return MinimumInvoice(
        invoice_number="471102",
        type_code=DocumentTypeCode.INVOICE,
        invoice_date=date(2020, 3, 5),
        seller=TradeParty(
            "Lieferant GmbH",
            PostalAddress("DE"),
            tax_number="201/113/40209",
            vat_id="DE123456789",
        ),
        buyer=TradeParty("Kunden AG Frankreich", None),
        currency_code="EUR",
        tax_basis_total_amount=Money("198.00", "EUR"),
        tax_total_amounts=[Money("37.62", "EUR")],
        grand_total_amount=Money("235.62", "EUR"),
        due_payable_amount=Money("235.62", "EUR"),
    )


def basic_wl_einfach() -> BasicWLInvoice:
    return BasicWLInvoice(
        invoice_number="TX-471102",
        type_code=DocumentTypeCode.INVOICE,
        invoice_date=date(2019, 10, 30),
        currency_code="EUR",
        delivery_date=date(2019, 10, 29),
        seller=TradeParty(
            "Taxiunternehmen TX GmbH",
            PostalAddress(
                "DE", None, "10369", "Berlin", "Lieferantenstraße 20"
            ),
            vat_id="DE123456789",
        ),
        buyer=TradeParty(
            "Taxi-Gast AG Mitte",
            PostalAddress(
                "DE",
                None,
                "13351",
                "Berlin",
                "Hans Mustermann",
                "Kundenstraße 15",
            ),
        ),
        line_total_amount=Money("16.90", "EUR"),
        charge_total_amount=Money("0.00", "EUR"),
        allowance_total_amount=Money("0.00", "EUR"),
        tax_basis_total_amount=Money("16.90", "EUR"),
        tax=[
            Tax(
                Money("1.18", "EUR"),
                Money("16.90", "EUR"),
                Decimal(7),
                TaxCategoryCode.STANDARD_RATE,
            )
        ],
        tax_total_amounts=[Money("1.18", "EUR")],
        grand_total_amount=Money("18.08", "EUR"),
        due_payable_amount=Money("18.08", "EUR"),
        payment_terms=PaymentTerms(due_date=date(2019, 11, 29)),
        notes=[
            IncludedNote("Rechnung gemäß Taxifahrt vom 29.10.2019"),
            IncludedNote("""Taxiunternehmen TX GmbH\t\t\t\t
Lieferantenstraße 20\t\t\t\t
10369 Berlin\t\t\t\t
Deutschland\t\t\t\t
Geschäftsführer: Hans Mustermann
Handelsregisternummer: H A 123
      """),
            IncludedNote("""Unsere GLN: 4000001123452
Ihre GLN: 4000001987658
Ihre Kundennummer: GE2020211
     """),
        ],
    )


def basic_einfach() -> BasicInvoice:
    return BasicInvoice(
        invoice_number="471102",
        type_code=DocumentTypeCode.INVOICE,
        invoice_date=date(2020, 3, 5),
        currency_code="EUR",
        delivery_date=date(2020, 3, 5),
        seller=TradeParty(
            "Lieferant GmbH",
            PostalAddress(
                "DE", None, "80333", "München", "Lieferantenstraße 20"
            ),
            tax_number="201/113/40209",
            vat_id="DE123456789",
        ),
        buyer=TradeParty(
            "Kunden AG Mitte",
            PostalAddress(
                "DE",
                None,
                "69876",
                "Frankfurt",
                "Hans Muster",
                "Kundenstraße 15",
            ),
        ),
        line_items=[
            LineItem(
                "1",
                """GTIN: 4012345001235
Unsere Art.-Nr.: TB100A4
Trennblätter A4
        """,
                Money("9.90", "EUR"),
                (Decimal("20.0000"), QuantityCode.PIECE),
                Money("198.00", "EUR"),
                Decimal(19),
                global_id=("4012345001235", IdentifierSchemeCode.GTIN),
            ),
        ],
        line_total_amount=Money("198.00", "EUR"),
        charge_total_amount=Money("0.00", "EUR"),
        allowance_total_amount=Money("0.00", "EUR"),
        tax_basis_total_amount=Money("198.00", "EUR"),
        tax=[
            Tax(
                Money("37.62", "EUR"),
                Money("198.00", "EUR"),
                Decimal("19.00"),
                TaxCategoryCode.STANDARD_RATE,
            )
        ],
        tax_total_amounts=[Money("37.62", "EUR")],
        grand_total_amount=Money("235.62", "EUR"),
        due_payable_amount=Money("235.62", "EUR"),
        payment_terms=PaymentTerms(due_date=date(2020, 4, 4)),
        notes=[
            IncludedNote("Rechnung gemäß Bestellung vom 01.03.2020."),
            IncludedNote("""Lieferant GmbH\t\t\t\t
Lieferantenstraße 20\t\t\t\t
80333 München\t\t\t\t
Deutschland\t\t\t\t
Geschäftsführer: Hans Muster
Handelsregisternummer: H A 123
      """),
            IncludedNote("""Unsere GLN: 4000001123452
Ihre GLN: 4000001987658
Ihre Kundennummer: GE2020211


Zahlbar innerhalb 30 Tagen netto bis 04.04.2020, 3% Skonto innerhalb 10 Tagen bis 15.03.2020.
      """),  # noqa: E501
        ],
    )


def en16931_einfach() -> EN16931Invoice:
    return EN16931Invoice(
        invoice_number="471102",
        type_code=DocumentTypeCode.INVOICE,
        invoice_date=date(2018, 3, 5),
        currency_code="EUR",
        delivery_date=date(2018, 3, 5),
        seller=TradeParty(
            "Lieferant GmbH",
            PostalAddress(
                "DE", None, "80333", "München", "Lieferantenstraße 20"
            ),
            tax_number="201/113/40209",
            vat_id="DE123456789",
            ids=["549910"],
            global_ids=[("4000001123452", IdentifierSchemeCode.GLN)],
        ),
        buyer=TradeParty(
            "Kunden AG Mitte",
            PostalAddress(
                "DE",
                None,
                "69876",
                "Frankfurt",
                "Kundenstraße 15",
            ),
            ids=["GE2020211"],
        ),
        line_items=[
            EN16931LineItem(
                "1",
                "Trennblätter A4",
                Money("9.9000", "EUR"),
                (Decimal("20.0000"), QuantityCode.PIECE),
                Money("198.00", "EUR"),
                Decimal("19.00"),
                global_id=("4012345001235", IdentifierSchemeCode.GTIN),
                seller_assigned_id="TB100A4",
                gross_unit_price=(Money("9.9000", "EUR"), None),
            ),
            EN16931LineItem(
                "2",
                "Joghurt Banane",
                Money("5.5000", "EUR"),
                (Decimal("50.0000"), QuantityCode.PIECE),
                Money("275.00", "EUR"),
                Decimal("7.00"),
                global_id=("4000050986428", IdentifierSchemeCode.GTIN),
                seller_assigned_id="ARNR2",
                gross_unit_price=(Money("5.5000", "EUR"), None),
            ),
        ],
        line_total_amount=Money("473.00", "EUR"),
        charge_total_amount=Money("0.00", "EUR"),
        allowance_total_amount=Money("0.00", "EUR"),
        tax_basis_total_amount=Money("473.00", "EUR"),
        tax=[
            Tax(
                Money("19.25", "EUR"),
                Money("275.00", "EUR"),
                Decimal("7.00"),
                TaxCategoryCode.STANDARD_RATE,
            ),
            Tax(
                Money("37.62", "EUR"),
                Money("198.00", "EUR"),
                Decimal("19.00"),
                TaxCategoryCode.STANDARD_RATE,
            ),
        ],
        tax_total_amounts=[Money("56.87", "EUR")],
        grand_total_amount=Money("529.87", "EUR"),
        prepaid_amount=Money("0.00", "EUR"),
        due_payable_amount=Money("529.87", "EUR"),
        payment_terms=PaymentTerms(
            description="Zahlbar innerhalb 30 Tagen netto bis 04.04.2018, "
            "3% Skonto innerhalb 10 Tagen bis 15.03.2018"
        ),
        notes=[
            IncludedNote("Rechnung gemäß Bestellung vom 01.03.2018."),
            IncludedNote(
                """Lieferant GmbH\t\t\t\t
Lieferantenstraße 20\t\t\t\t
80333 München\t\t\t\t
Deutschland\t\t\t\t
Geschäftsführer: Hans Muster
Handelsregisternummer: H A 123
      """,
                TextSubjectCode.REGULATORY_INFORMATION,
            ),
        ],
    )
