import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from facturx.generate import generate_et
from facturx.type_codes import DocumentTypeCode, TaxCategoryCode

from .model import (
    BasicWLInvoice,
    IncludedNote,
    MinimumInvoice,
    PaymentTerms,
    PostalAddress,
    Tax,
    TradeParty,
)
from .money import Money


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
        tax_total_amount=Money("37.62", "EUR"),
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
        tax_total_amount=Money("1.18", "EUR"),
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


@pytest.mark.parametrize(
    "invoice, filename",
    [
        (minimum_rechnung, "MINIMUM_Rechnung.xml"),
        (basic_wl_einfach, "BASIC-WL_Einfach.xml"),
    ],
)
def test_generate(
    invoice: Callable[[], MinimumInvoice], filename: str
) -> None:
    our_xml = _generate_xml(invoice())
    their_xml = _read_xml(filename)
    assert our_xml == their_xml


def _generate_xml(invoice: MinimumInvoice) -> str:
    tree = generate_et(invoice)
    tree.attrib = dict(sorted(tree.attrib.items()))
    ET.indent(tree)
    return ET.tostring(tree, encoding="unicode")


def _read_xml(filename: str) -> str:
    path = Path(__file__).parent / "test-data" / filename
    register_all_namespaces(path)
    tree = ET.parse(path).getroot()
    tree.attrib = dict(sorted(tree.attrib.items()))
    ET.indent(tree)
    return ET.tostring(tree, encoding="unicode")


def register_all_namespaces(path: Path) -> None:
    namespaces = dict(
        [node for _, node in ET.iterparse(path, events=["start-ns"])]
    )
    for ns in namespaces:
        ET.register_namespace(ns, namespaces[ns])
