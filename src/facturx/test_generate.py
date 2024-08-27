import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path

import pytest

from .generate import generate_et
from .model import MinimumInvoice
from .test_data import (
    basic_einfach,
    basic_wl_einfach,
    en16931_einfach,
    minimum_rechnung,
)


@pytest.mark.parametrize(
    "invoice, filename",
    [
        (minimum_rechnung, "MINIMUM_Rechnung.xml"),
        (basic_wl_einfach, "BASIC-WL_Einfach.xml"),
        (basic_einfach, "BASIC_Einfach.xml"),
        (en16931_einfach, "EN16931_Einfach.xml"),
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
    path = Path(__file__).parent / "test_data" / filename
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
