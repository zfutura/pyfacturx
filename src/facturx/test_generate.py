import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import date
from pathlib import Path

import pytest

from facturx.generate import generate_et
from facturx.type_codes import DocumentTypeCode

from .model import MinimumInvoice, PostalAddress, TradeParty
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


@pytest.mark.parametrize(
    "invoice, filename", [(minimum_rechnung, "MINIMUM_Rechnung.xml")]
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
