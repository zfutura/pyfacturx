from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from base64 import b64decode
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from os import PathLike
from typing import TYPE_CHECKING, Any, NamedTuple

from facturx.quantities import QuantityCode

from .const import (
    NS_CII,
    NS_RAM,
    NS_UDT,
    URN_BASIC_PROFILE,
    URN_BASIC_WL_PROFILE,
    URN_EN16931_PROFILE,
    URN_EXTENDED_PROFILE,
    URN_MINIMUM_PROFILE,
    URN_XRECHNUNG_PROFILE,
)
from .exc import (
    InvalidProfileError,
    InvalidXMLError,
    NotFacturXError,
    UnsupportedProfileError,
    XMLParseError,
)
from .model import (
    BankAccount,
    BasicInvoice,
    BasicWLInvoice,
    DocumentAllowance,
    DocumentCharge,
    EN16931Invoice,
    EN16931LineItem,
    IncludedNote,
    LineAllowance,
    LineCharge,
    LineItem,
    MinimumInvoice,
    PaymentMeans,
    PaymentTerms,
    PostalAddress,
    ProductCharacteristic,
    ProductClassification,
    ReferenceDocument,
    Tax,
    TradeContact,
    TradeParty,
)
from .money import Money
from .type_codes import (
    ALLOWED_MIME_TYPES,
    AllowanceChargeCode,
    DocumentTypeCode,
    IdentifierSchemeCode,
    ItemTypeCode,
    PaymentMeansCode,
    PaymentTimeCode,
    ReferenceQualifierCode,
    SpecialServiceCode,
    TaxCategoryCode,
    TextSubjectCode,
    VATExemptionCode,
)
from .types import ID, Attachment, DocRef, OptionalQuantity, Quantity

if TYPE_CHECKING:
    from xml.etree.ElementTree import _FileRead

    from _typeshed import StrPath


def _find_text(parent: ET.Element, tag: str) -> str:
    """Find the text of a child element with the given tag.

    Raise InvalidXMLError if the element is not found or if the element has
    no text.
    """
    el = parent.find(tag)
    if el is None:
        raise InvalidXMLError(f"Element {tag} not found")
    if el.text is None:
        raise InvalidXMLError(f"Element {tag} has no text")
    return el.text


def _find_all_texts(parent: ET.Element, tag: str) -> list[str]:
    texts = []
    for el in parent.findall(tag):
        if el.text is None:
            raise InvalidXMLError(f"Element {tag} has no text")
        texts.append(el.text)
    return texts


def _find_text_optional(parent: ET.Element, tag: str) -> str | None:
    """Find the text of a child element with the given tag.

    Return None if the element is not found. Raise InvalidXMLError if the
    element has no text.
    """
    el = parent.find(tag)
    if el is None:
        return None
    if el.text is None:
        raise InvalidXMLError(f"Element {tag} has no text")
    return el.text


def _find_indicator(parent: ET.Element, tag: str) -> bool:
    el = parent.find(tag)
    if el is None:
        raise InvalidXMLError(f"Element {tag} not found")
    indicator = el.find(f"./{{{NS_RAM}}}Indicator")
    if indicator is None:
        raise InvalidXMLError("Indicator element not found")
    if indicator.text == "true":
        return True
    elif indicator.text == "false":
        return False
    else:
        raise InvalidXMLError(f"Invalid indicator: {indicator.text}")


def _find_all_ids(
    parent: ET.Element, tag: str, *, scheme_required: bool = False
) -> list[ID]:
    ids: list[ID] = []
    for el in parent.findall(tag):
        ids.append(_parse_id(el, scheme_required=scheme_required))
    return ids


def _find_id_optional(
    parent: ET.Element, tag: str, *, scheme_required: bool = False
) -> ID | None:
    el = parent.find(tag)
    if el is None:
        return None
    return _parse_id(el, scheme_required=scheme_required)


def _parse_id(el: ET.Element, *, scheme_required: bool) -> ID:
    if el.text is None:
        raise InvalidXMLError("ID element has no text")
    scheme_id_s = el.attrib.get("schemeID")
    scheme_id: IdentifierSchemeCode | None = None
    if scheme_id_s is None and scheme_required:
        raise InvalidXMLError("schemeID attribute not found")
    elif scheme_id_s is not None:
        try:
            scheme_id = IdentifierSchemeCode(scheme_id_s)
        except ValueError as exc:
            raise InvalidXMLError(str(exc)) from exc
    return el.text, scheme_id


def _find_percent_optional(parent: ET.Element, tag: str) -> Decimal | None:
    rate_s = _find_text_optional(parent, tag)
    if rate_s is None:
        return None
    try:
        return Decimal(rate_s)
    except ValueError as exc:
        raise InvalidXMLError(f"Invalid tax rate: {rate_s}") from exc


def _find_quantity(parent: ET.Element, tag: str) -> Quantity:
    quantity = _find_optional_quantity_optional(parent, tag)
    if quantity is None:
        raise InvalidXMLError(f"Element {tag} not found")
    if quantity[1] is None:
        raise InvalidXMLError(f"Element {tag} has no unitCode")
    return quantity[0], quantity[1]


def _find_optional_quantity_optional(
    parent: ET.Element, tag: str
) -> OptionalQuantity | None:
    el = parent.find(tag)
    if el is None:
        return None
    if el.text is None:
        raise InvalidXMLError(f"Element {tag} has no text")
    try:
        quantity = Decimal(el.text)
    except ValueError as exc:
        raise InvalidXMLError(str(exc)) from exc
    code_s = el.attrib.get("unitCode")
    try:
        code = QuantityCode(code_s) if code_s is not None else None
    except ValueError as exc:
        raise InvalidXMLError(str(exc)) from exc
    return quantity, code


def _find_amount(
    parent: ET.Element,
    tag: str,
    default_currency: str,
    *,
    require_currency: bool = False,
) -> Money:
    el = parent.find(tag)
    if el is None:
        raise InvalidXMLError(f"Element {tag} not found")
    return _parse_amount(
        el, default_currency, require_currency=require_currency
    )


def _find_all_amounts(
    parent: ET.Element,
    tag: str,
    default_currency: str,
    *,
    require_currency: bool = False,
) -> list[Money]:
    return [
        _parse_amount(el, default_currency, require_currency=require_currency)
        for el in parent.findall(tag)
    ]


def _find_amount_optional(
    parent: ET.Element,
    tag: str,
    default_currency: str,
    *,
    require_currency: bool = False,
) -> Money | None:
    el = parent.find(tag)
    if el is None:
        return None
    return _parse_amount(
        el, default_currency, require_currency=require_currency
    )


def _parse_amount(
    el: ET.Element, default_currency: str, *, require_currency: bool = False
) -> Money:
    currency_code = el.attrib.get("currencyID")
    if currency_code is None and require_currency:
        raise InvalidXMLError("currencyID attribute not found")
    if currency_code is None:
        currency_code = default_currency
    amount = el.text
    if amount is None:
        raise InvalidXMLError("Element has no text")
    try:
        return Money(amount, currency_code)
    except ValueError as exc:
        raise InvalidXMLError(str(exc)) from exc


_DATE_RE = re.compile(r"\d{4}\d{2}\d{2}")


def _find_date(parent: ET.Element, tag: str) -> date:
    """Parse the text of a child element with the given tag as a date.

    Raise InvalidXMLError if the element is not found or if the element has
    no valid date.
    """
    date = _find_date_optional(parent, tag)
    if date is None:
        raise InvalidXMLError(f"Element {tag} not found")
    return date


def _find_date_optional(parent: ET.Element, tag: str) -> date | None:
    """Parse the text of a child element with the given tag as a date.

    Return None if the element is not found. Raise InvalidXMLError if the
    element has no valid date.
    """
    date_el = parent.find(tag)
    if date_el is None:
        return None
    dts_el = date_el.find(f"./{{{NS_UDT}}}DateTimeString")
    if dts_el is None:
        raise InvalidXMLError(f"DateTimeString element not found in {tag}")
    if dts_el.attrib.get("format") != "102":
        raise InvalidXMLError(f"Invalid format in DateTimeString in {tag}")
    text = dts_el.text
    if text is None:
        raise InvalidXMLError(f"DateTimeString element has no text in {tag}")
    if not _DATE_RE.fullmatch(text):
        raise InvalidXMLError(f"Invalid date: {text}")
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise InvalidXMLError(f"Invalid date: {text}") from None


def _find_ref_doc_id_optional(parent: ET.Element, tag: str) -> str | None:
    """Find the ID of a referenced document.

    Return None if the element is not found. Raise InvalidXMLError if the
    element has no text.
    """
    el = parent.find(tag)
    if el is None:
        return None
    id_el = el.find(f"./{{{NS_RAM}}}IssuerAssignedID")
    if id_el is None:
        raise InvalidXMLError(f"IssuerAssignedID element not found in {tag}")
    if id_el.text is None:
        raise InvalidXMLError(f"IssuerAssignedID element has no text in {tag}")
    return id_el.text


def parse_xml(xml: str | _FileRead | StrPath) -> MinimumInvoice:
    """Parse a Factur-X XML file and return a matching invoice.

    Raise a FacturXParseError if the XML file is not a valid Factur-X file
    or a ModelError if the invoice is invalid.
    """

    tree = _parse_tree(xml)
    if tree.tag != f"{{{NS_CII}}}CrossIndustryInvoice":
        raise NotFacturXError("Root element is not a Factur-X invoice")
    id_el = tree.find(
        f"./{{{NS_CII}}}ExchangedDocumentContext/{{{NS_RAM}}}GuidelineSpecifiedDocumentContextParameter/{{{NS_RAM}}}ID"
    )
    if id_el is None:
        raise NotFacturXError("Profile ID element not found")
    if id_el.text == URN_MINIMUM_PROFILE:
        return _parse_minimum_invoice(tree)
    elif id_el.text == URN_BASIC_WL_PROFILE:
        return _parse_basic_wl_invoice(tree)
    elif id_el.text == URN_BASIC_PROFILE:
        return _parse_basic_invoice(tree)
    elif id_el.text == URN_EN16931_PROFILE:
        return _parse_en16931_invoice(tree)
    elif id_el.text == URN_EXTENDED_PROFILE:
        raise UnsupportedProfileError("Unsupported profile: EXTENDED")
    elif id_el.text == URN_XRECHNUNG_PROFILE:
        raise UnsupportedProfileError("Unsupported profile: XRECHNUNG")
    else:
        raise UnsupportedProfileError(f"Unsupported profile: {id_el.text}")


def _parse_tree(xml: str | _FileRead | StrPath) -> ET.Element:
    try:
        if isinstance(xml, str):
            return ET.fromstring(xml)
        elif isinstance(xml, (str, PathLike)):
            with open(xml) as f:
                return ET.parse(f).getroot()
        else:
            return ET.parse(xml).getroot()
    except ET.ParseError as exc:
        raise XMLParseError(str(exc)) from exc


def _parse_minimum_invoice(tree: ET.Element) -> MinimumInvoice:
    doc_ctx = _parse_doc_ctx(tree)
    doc_info = _parse_doc(tree)
    agreement, delivery, settlement = _parse_transaction(tree)
    if len(doc_info.notes) > 0:
        raise InvalidProfileError(
            "MINIMUM", "Included notes are not supported in MINIMUM profile"
        )
    if agreement.seller_tax_representative is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "SellerTaxRepresentativeTradeParty element is not supported in "
            "MINIMUM profile",
        )
    if agreement.contract_id is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "ContractReferencedDocument element is not supported in "
            "MINIMUM profile",
        )
    if agreement.seller_order_id is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "SellerOrderReferencedDocument element is not supported in "
            "MINIMUM profile",
        )
    if len(agreement.referenced_docs) > 0:
        raise InvalidProfileError(
            "MINIMUM",
            "AdditionalReferencedDocument element is not supported in "
            "MINIMUM profile",
        )
    if agreement.procuring_project is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "SpecifiedProcuringProject element is not supported in "
            "MINIMUM profile",
        )
    if delivery.ship_to is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "ShipToTradeParty element is not supported in MINIMUM profile",
        )
    if delivery.delivery_date is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "Delivery date is not supported in MINIMUM profile",
        )
    if delivery.despatch_advice_id is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "DespatchAdviceReferencedDocument element is not supported in "
            "MINIMUM profile",
        )
    if delivery.receiving_advice_id is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "ReceivingAdviceReferencedDocument element is not supported in "
            "MINIMUM profile",
        )
    if settlement.creditor_reference_id is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "CreditorReferenceID element is not supported in MINIMUM profile",
        )
    if settlement.payment_reference is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "PaymentReference element is not supported in MINIMUM profile",
        )
    if settlement.tax_currency_code is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "TaxCurrencyCode element is not supported in MINIMUM profile",
        )
    if settlement.payee is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "PayeeTradeParty element is not supported in MINIMUM profile",
        )
    if len(settlement.payment_means) > 0:
        raise InvalidProfileError(
            "MINIMUM",
            "SpecifiedTradeSettlementPaymentMeans element is not supported "
            "in MINIMUM profile",
        )
    if len(settlement.tax) > 0:
        raise InvalidProfileError(
            "MINIMUM",
            "ApplicableTradeTax element is not supported in MINIMUM profile",
        )
    if settlement.billing_period is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "Billing period is not supported in MINIMUM profile",
        )
    if len(settlement.allowances) > 0 or len(settlement.charges) > 0:
        raise InvalidProfileError(
            "MINIMUM",
            "SpecifiedTradeAllowanceCharge element is not supported in "
            "MINIMUM profile",
        )
    if settlement.payment_terms is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "SpecifiedTradePaymentTerms element is not supported in MINIMUM "
            "profile",
        )
    if settlement.summation.charge_total is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "ChargeTotalAmount element is not supported in MINIMUM profile",
        )
    if settlement.summation.allowance_total is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "AllowanceTotalAmount element is not supported in MINIMUM profile",
        )
    if settlement.summation.prepaid_amount is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "PrepaidAmount element is not supported in MINIMUM profile",
        )
    if settlement.summation.rounding_amount is not None:
        raise InvalidProfileError(
            "MINIMUM",
            "RoundingAmount element is not supported in MINIMUM profile",
        )
    if len(settlement.preceding_invoices) > 0:
        raise InvalidProfileError(
            "MINIMUM",
            "InvoiceReferencedDocument element is not supported in MINIMUM "
            "profile",
        )
    if len(settlement.receiver_accounting_ids) > 0:
        raise InvalidProfileError(
            "MINIMUM",
            "ReceivableSpecifiedTradeAccountingAccount element is not "
            "supported in MINIMUM profile",
        )
    return MinimumInvoice(
        **_minimum_args(doc_ctx, doc_info, agreement, settlement)
    )


def _parse_basic_wl_invoice(tree: ET.Element) -> BasicWLInvoice:
    doc_ctx = _parse_doc_ctx(tree)
    doc_info = _parse_doc(tree)
    agreement, delivery, settlement = _parse_transaction(tree)
    if agreement.seller_order_id is not None:
        raise InvalidProfileError(
            "BASIC WL",
            "SellerOrderReferencedDocument element is not supported in "
            "BASIC WL profile",
        )
    if len(agreement.referenced_docs) > 0:
        raise InvalidProfileError(
            "BASIC WL",
            "AdditionalReferencedDocument element is not supported in "
            "BASIC WL profile",
        )
    if agreement.procuring_project is not None:
        raise InvalidProfileError(
            "BASIC WL",
            "SpecifiedProcuringProject element is not supported in "
            "BASIC WL profile",
        )
    if delivery.receiving_advice_id is not None:
        raise InvalidProfileError(
            "BASIC WL",
            "ReceivingAdviceReferencedDocument element is not supported in "
            "BASIC WL profile",
        )
    if settlement.tax_currency_code is not None:
        raise InvalidProfileError(
            "BASIC WL",
            "TaxCurrencyCode element is not supported in BASIC WL profile",
        )
    if settlement.summation.rounding_amount is not None:
        raise InvalidProfileError(
            "BASIC WL",
            "RoundingAmount element is not supported in BASIC WL profile",
        )
    return BasicWLInvoice(
        **_minimum_args(doc_ctx, doc_info, agreement, settlement),
        **_basic_wl_args(doc_info, agreement, delivery, settlement),
    )


def _parse_basic_invoice(tree: ET.Element) -> BasicInvoice:
    doc_ctx = _parse_doc_ctx(tree)
    doc_info = _parse_doc(tree)
    agreement, delivery, settlement = _parse_transaction(tree)
    line_items = _parse_line_items(tree, settlement.currency_code)
    if agreement.seller_order_id is not None:
        raise InvalidProfileError(
            "BASIC",
            "SellerOrderReferencedDocument element is not supported in "
            "BASIC profile",
        )
    if len(agreement.referenced_docs) > 0:
        raise InvalidProfileError(
            "BASIC",
            "AdditionalReferencedDocument element is not supported in "
            "BASIC profile",
        )
    if agreement.procuring_project is not None:
        raise InvalidProfileError(
            "BASIC",
            "SpecifiedProcuringProject element is not supported in BASIC "
            "profile",
        )
    if delivery.receiving_advice_id is not None:
        raise InvalidProfileError(
            "BASIC",
            "ReceivingAdviceReferencedDocument element is not supported in "
            "BASIC profile",
        )
    if settlement.tax_currency_code is not None:
        raise InvalidProfileError(
            "BASIC",
            "TaxCurrencyCode element is not supported in BASIC profile",
        )
    if settlement.summation.rounding_amount is not None:
        raise InvalidProfileError(
            "BASIC",
            "RoundingAmount element is not supported in BASIC profile",
        )
    return BasicInvoice(
        **_minimum_args(doc_ctx, doc_info, agreement, settlement),
        **_basic_wl_args(doc_info, agreement, delivery, settlement),
        **_basic_args(line_items),
    )


def _parse_en16931_invoice(tree: ET.Element) -> EN16931Invoice:
    doc_ctx = _parse_doc_ctx(tree)
    doc_info = _parse_doc(tree)
    agreement, delivery, settlement = _parse_transaction(tree)
    line_items = _parse_en16931_line_items(tree, settlement.currency_code)
    return EN16931Invoice(
        **_minimum_args(doc_ctx, doc_info, agreement, settlement),
        **_basic_wl_args(doc_info, agreement, delivery, settlement),
        **_basic_args(line_items),
        **_en16931_args(agreement, delivery, settlement),
    )


def _minimum_args(
    doc_ctx: _DocumentContext,
    doc_info: _DocumentInfo,
    agreement: _TradeAgreement,
    settlement: _TradeSettlement,
) -> dict[str, Any]:
    return {
        "invoice_number": doc_info.id,
        "type_code": doc_info.type_code,
        "invoice_date": doc_info.issue_date,
        "seller": agreement.seller,
        "buyer": agreement.buyer,
        "currency_code": settlement.currency_code,
        "line_total_amount": settlement.summation.line_total,
        "tax_basis_total_amount": settlement.summation.tax_basis_total,
        "tax_total_amounts": settlement.summation.tax_totals,
        "grand_total_amount": settlement.summation.grand_total,
        "due_payable_amount": settlement.summation.due_payable_amount,
        "business_process_id": doc_ctx.business_process_id,
        "buyer_reference": agreement.buyer_reference,
        "buyer_order_id": agreement.buyer_order_id,
    }


def _basic_wl_args(
    doc_info: _DocumentInfo,
    agreement: _TradeAgreement,
    delivery: _TradeDelivery,
    settlement: _TradeSettlement,
) -> dict[str, Any]:
    return {
        "tax": settlement.tax,
        "charge_total_amount": settlement.summation.charge_total,
        "allowance_total_amount": settlement.summation.allowance_total,
        "prepaid_amount": settlement.summation.prepaid_amount,
        "payee": settlement.payee,
        "delivery_date": delivery.delivery_date,
        "billing_period": settlement.billing_period,
        "allowances": settlement.allowances,
        "charges": settlement.charges,
        "notes": doc_info.notes,
        "seller_tax_representative": agreement.seller_tax_representative,
        "contract_id": agreement.contract_id,
        "ship_to": delivery.ship_to,
        "despatch_advice_id": delivery.despatch_advice_id,
        "sepa_reference": settlement.creditor_reference_id,
        "payment_reference": settlement.payment_reference,
        "payment_means": settlement.payment_means,
        "payment_terms": settlement.payment_terms,
        "preceding_invoices": settlement.preceding_invoices,
        "receiver_accounting_ids": settlement.receiver_accounting_ids,
    }


def _basic_args(line_items: Sequence[LineItem]) -> dict[str, Any]:
    return {"line_items": line_items}


def _en16931_args(
    agreement: _TradeAgreement,
    delivery: _TradeDelivery,
    settlement: _TradeSettlement,
) -> dict[str, Any]:
    return {
        "receiving_advice_id": delivery.receiving_advice_id,
        "rounding_amount": settlement.summation.rounding_amount,
        "seller_order_id": agreement.seller_order_id,
        "procuring_project": agreement.procuring_project,
        "tax_currency_code": settlement.tax_currency_code,
        "referenced_docs": agreement.referenced_docs,
    }


class _DocumentContext(NamedTuple):
    business_process_id: str | None


def _parse_doc_ctx(tree: ET.Element) -> _DocumentContext:
    doc_ctx = tree.find(f"./{{{NS_CII}}}ExchangedDocumentContext")
    if doc_ctx is None:
        raise InvalidXMLError("ExchangedDocumentContext element not found")
    business_process_el = doc_ctx.find(
        f"./{{{NS_RAM}}}BusinessProcessSpecifiedDocumentContextParameter/{{{NS_RAM}}}ID"
    )
    process_id = (
        business_process_el.text if business_process_el is not None else None
    )
    return _DocumentContext(process_id)


class _DocumentInfo(NamedTuple):
    id: str
    type_code: DocumentTypeCode
    issue_date: date
    notes: list[IncludedNote]  # BASIC WL+


def _parse_doc(tree: ET.Element) -> _DocumentInfo:
    doc_el = tree.find(f"./{{{NS_CII}}}ExchangedDocument")
    if doc_el is None:
        raise InvalidXMLError("ExchangedDocument element not found")
    id = _find_text(doc_el, f"./{{{NS_RAM}}}ID")
    type_code_s = _find_text(doc_el, f"./{{{NS_RAM}}}TypeCode")
    try:
        type_code = DocumentTypeCode(int(type_code_s))
    except ValueError:
        raise InvalidXMLError(f"Invalid TypeCode: {type_code_s}") from None
    dt = _find_date(doc_el, f"./{{{NS_RAM}}}IssueDateTime")
    notes = [
        _parse_note(el) for el in doc_el.findall(f"./{{{NS_RAM}}}IncludedNote")
    ]
    return _DocumentInfo(id, type_code, dt, notes)


def _parse_note(el: ET.Element) -> IncludedNote:
    content = _find_text(el, f"./{{{NS_RAM}}}Content")
    subject_code: TextSubjectCode | None = None
    code_el = el.find(f"./{{{NS_RAM}}}SubjectCode")
    if code_el is not None:
        if code_el.text is None:
            raise InvalidXMLError("SubjectCode element has no text")
        try:
            subject_code = TextSubjectCode(code_el.text)
        except ValueError as exc:
            raise InvalidXMLError(
                f"Invalid SubjectCode: {code_el.text}"
            ) from exc
    return IncludedNote(content, subject_code)


def _parse_transaction(
    tree: ET.Element,
) -> tuple[_TradeAgreement, _TradeDelivery, _TradeSettlement]:
    el = tree.find(f"./{{{NS_CII}}}SupplyChainTradeTransaction")
    if el is None:
        raise InvalidXMLError("SupplyChainTradeTransaction element not found")
    agreement = _parse_agreement(el)
    delivery = _parse_delivery(el)
    settlement = _parse_settlement(el)
    return agreement, delivery, settlement


class _TradeAgreement(NamedTuple):
    seller: TradeParty
    buyer: TradeParty
    buyer_reference: str | None
    seller_order_id: str | None  # EN16931+
    buyer_order_id: str | None
    contract_id: str | None  # BASIC WL+
    seller_tax_representative: TradeParty | None  # BASIC WL+
    referenced_docs: Sequence[ReferenceDocument]  # EN16931+
    procuring_project: tuple[str, str] | None  # EN16931+


def _parse_agreement(parent: ET.Element) -> _TradeAgreement:
    el = parent.find(f"./{{{NS_RAM}}}ApplicableHeaderTradeAgreement")
    if el is None:
        raise InvalidXMLError(
            "ApplicableHeaderTradeAgreement etax_currency_codelement not found"
        )
    buyer_ref = _find_text_optional(el, f"./{{{NS_RAM}}}BuyerReference")
    seller = _parse_trade_party(el, f"./{{{NS_RAM}}}SellerTradeParty")
    buyer = _parse_trade_party(el, f"./{{{NS_RAM}}}BuyerTradeParty")
    seller_order_id = _find_ref_doc_id_optional(
        el, f"./{{{NS_RAM}}}SellerOrderReferencedDocument"
    )
    buyer_order_id = _find_ref_doc_id_optional(
        el, f"./{{{NS_RAM}}}BuyerOrderReferencedDocument"
    )
    seller_tax_representative = _parse_trade_party_optional(
        el, f"./{{{NS_RAM}}}SellerTaxRepresentativeTradeParty"
    )
    contract_id = _find_ref_doc_id_optional(
        el, f"./{{{NS_RAM}}}ContractReferencedDocument"
    )
    referenced_docs = [
        _parse_reference_document(doc_el)
        for doc_el in el.findall(f"./{{{NS_RAM}}}AdditionalReferencedDocument")
    ]
    project: tuple[str, str] | None = None
    project_el = el.find(f"./{{{NS_RAM}}}SpecifiedProcuringProject")
    if project_el is not None:
        project = (
            _find_text(project_el, f"./{{{NS_RAM}}}ID"),
            _find_text(project_el, f"./{{{NS_RAM}}}Name"),
        )
    return _TradeAgreement(
        seller,
        buyer,
        buyer_ref,
        seller_order_id,
        buyer_order_id,
        contract_id,
        seller_tax_representative,
        referenced_docs,
        project,
    )


class _TradeDelivery(NamedTuple):
    ship_to: TradeParty | None  # BASIC WL+
    delivery_date: date | None  # BASIC WL+
    despatch_advice_id: str | None  # BASIC WL+
    receiving_advice_id: str | None  # EN16931+


def _parse_delivery(parent: ET.Element) -> _TradeDelivery:
    el = parent.find(f"./{{{NS_RAM}}}ApplicableHeaderTradeDelivery")
    if el is None:
        raise InvalidXMLError(
            "ApplicableHeaderTradeDelivery element not found"
        )
    ship_to = _parse_trade_party_optional(
        el, f"./{{{NS_RAM}}}ShipToTradeParty"
    )
    delivery_date = _parse_delivery_date(el)
    despatch_advice_id = _find_ref_doc_id_optional(
        el, f"./{{{NS_RAM}}}DespatchAdviceReferencedDocument"
    )
    receiving_advice_id = _find_ref_doc_id_optional(
        el, f"./{{{NS_RAM}}}ReceivingAdviceReferencedDocument"
    )
    return _TradeDelivery(
        ship_to, delivery_date, despatch_advice_id, receiving_advice_id
    )


def _parse_delivery_date(parent: ET.Element) -> date | None:
    el = parent.find(f"./{{{NS_RAM}}}ActualDeliverySupplyChainEvent")
    if el is None:
        return None
    return _find_date(el, f"./{{{NS_RAM}}}OccurrenceDateTime")


class _SettlementSummation(NamedTuple):
    line_total: Money | None
    tax_basis_total: Money
    tax_totals: list[Money]
    grand_total: Money
    due_payable_amount: Money
    charge_total: Money | None  # BASIC WL+
    allowance_total: Money | None  # BASIC WL+
    prepaid_amount: Money | None  # BASIC WL+
    rounding_amount: Money | None  # EN16931+


class _TradeSettlement(NamedTuple):
    currency_code: str
    summation: _SettlementSummation
    creditor_reference_id: str | None  # BASIC WL+
    payment_reference: str | None  # BASIC WL+
    tax_currency_code: str | None  # EN16931+
    payee: TradeParty | None  # BASIC WL+
    payment_means: list[PaymentMeans]  # BASIC WL+
    tax: list[Tax]  # BASIC WL+
    billing_period: tuple[date, date] | None  # BASIC WL+
    allowances: list[DocumentAllowance]  # BASIC WL+
    charges: list[DocumentCharge]  # BASIC WL+
    payment_terms: PaymentTerms | None  # BASIC WL+
    preceding_invoices: list[tuple[str, date | None]]  # BASIC WL+
    receiver_accounting_ids: list[str]  # BASIC WL+


def _parse_settlement(parent: ET.Element) -> _TradeSettlement:
    el = parent.find(f"./{{{NS_RAM}}}ApplicableHeaderTradeSettlement")
    if el is None:
        raise InvalidXMLError(
            "ApplicableHeaderTradeSettlement element not found"
        )
    currency_code = _find_text(el, f"./{{{NS_RAM}}}InvoiceCurrencyCode")
    creditor_reference_id = _find_text_optional(
        el, f"./{{{NS_RAM}}}CreditorReferenceID"
    )
    payment_reference = _find_text_optional(
        el, f"./{{{NS_RAM}}}PaymentReference"
    )
    tax_currency_code = _find_text_optional(
        el, f"./{{{NS_RAM}}}TaxCurrencyCode"
    )
    payee = _parse_trade_party_optional(el, f"./{{{NS_RAM}}}PayeeTradeParty")
    payment_means = [
        _parse_payment_means(pay_el)
        for pay_el in el.findall(
            f"./{{{NS_RAM}}}SpecifiedTradeSettlementPaymentMeans"
        )
    ]
    tax = [
        _parse_tax(tax_el, currency_code)
        for tax_el in el.findall(f"./{{{NS_RAM}}}ApplicableTradeTax")
    ]
    billing_period = _parse_billing_period_optional(el)
    allowances = [
        _parse_allowance_or_charge(ac_el, currency_code)
        for ac_el in el.findall(f"./{{{NS_RAM}}}SpecifiedTradeAllowanceCharge")
    ]
    payment_terms = _parse_payment_terms(el)
    summation = _parse_summation(el, currency_code)
    referenced_invoices = _parse_referenced_invoices(el)
    receiver_accounting_ids: list[str] = []
    for el in parent.findall(
        f"./{{{NS_RAM}}}ReceivableSpecifiedTradeAccountingAccount"
    ):
        receiver_accounting_ids.append(_find_text(el, f"./{{{NS_RAM}}}ID"))
    return _TradeSettlement(
        currency_code,
        summation,
        creditor_reference_id,
        payment_reference,
        tax_currency_code,
        payee,
        payment_means,
        tax,
        billing_period,
        [a for a in allowances if isinstance(a, DocumentAllowance)],
        [c for c in allowances if isinstance(c, DocumentCharge)],
        payment_terms,
        referenced_invoices,
        receiver_accounting_ids,
    )


def _parse_payment_means(el: ET.Element) -> PaymentMeans:
    type_code = _parse_payment_type_code(el)
    information = _find_text_optional(el, f"./{{{NS_RAM}}}Information")

    card: tuple[str, str | None] | None = None
    card_el = el.find(f"./{{{NS_RAM}}}ApplicableTradeSettlementFinancialCard")
    if card_el is not None:
        card = (
            _find_text(card_el, f"./{{{NS_RAM}}}ID"),
            _find_text_optional(card_el, f"./{{{NS_RAM}}}CardholderName"),
        )

    payer_iban: str | None = None
    payer_el = el.find(f"./{{{NS_RAM}}}PayerPartyDebtorFinancialAccount")
    if payer_el is not None:
        payer_iban_el = payer_el.find(f"./{{{NS_RAM}}}IBANID")
        if payer_iban_el is not None:
            payer_iban = payer_iban_el.text
    payee_account = _parse_account_optional(
        el, f"./{{{NS_RAM}}}PayeePartyCreditorFinancialAccount"
    )
    payee_bic = _find_text_optional(
        el,
        f"./{{{NS_RAM}}}PayeeSpecifiedCreditorFinancialInstitution/{{{NS_RAM}}}BICID",
    )
    return PaymentMeans(
        type_code,
        payee_account,
        payee_bic,
        information,
        card=card,
        payer_iban=payer_iban,
    )


def _parse_payment_type_code(parent: ET.Element) -> PaymentMeansCode:
    type_code_s = _find_text(parent, f"./{{{NS_RAM}}}TypeCode")
    try:
        return PaymentMeansCode(type_code_s)
    except ValueError as exc:
        raise InvalidXMLError(str(exc)) from exc


def _parse_account_optional(
    parent: ET.Element, tag: str
) -> BankAccount | None:
    el = parent.find(tag)
    if el is None:
        return None
    iban = _find_text_optional(el, f"./{{{NS_RAM}}}IBANID")
    account_name = _find_text_optional(el, f"./{{{NS_RAM}}}AccountName")
    bank_id = _find_text_optional(el, f"./{{{NS_RAM}}}ProprietaryID")
    return BankAccount(iban, account_name, bank_id)


def _parse_line_items(
    parent: ET.Element, default_currency: str
) -> list[LineItem]:
    el = parent.find(f"./{{{NS_CII}}}SupplyChainTradeTransaction")
    if el is None:
        raise InvalidXMLError("SupplyChainTradeTransaction element not found")
    return [
        _parse_line_item(li_el, default_currency)
        for li_el in el.findall(
            f"./{{{NS_RAM}}}IncludedSupplyChainTradeLineItem"
        )
    ]


def _parse_en16931_line_items(
    parent: ET.Element, default_currency: str
) -> list[EN16931LineItem]:
    el = parent.find(f"./{{{NS_CII}}}SupplyChainTradeTransaction")
    if el is None:
        raise InvalidXMLError("SupplyChainTradeTransaction element not found")
    return [
        _parse_en16931_line_item(li_el, default_currency)
        for li_el in el.findall(
            f"./{{{NS_RAM}}}IncludedSupplyChainTradeLineItem"
        )
    ]


def _parse_line_item(el: ET.Element, default_currency: str) -> LineItem:
    doc = _parse_line_document(el)
    product = _parse_trade_product(el)
    agreement = _parse_line_agreement(el, default_currency)
    delivery = _parse_line_delivery(el)
    settlement = _parse_line_settlement(el, default_currency)

    if doc.note is not None:
        raise InvalidProfileError(
            "BASIC",
            "Included notes are not supported in BASIC profile line items",
        )
    if product.seller_id is not None:
        raise InvalidProfileError(
            "BASIC",
            "SellerAssignedID element is not supported in BASIC profile "
            "line items",
        )
    if product.buyer_id is not None:
        raise InvalidProfileError(
            "BASIC",
            "BuyerAssignedID element is not supported in BASIC profile "
            "line items",
        )
    if product.description is not None:
        raise InvalidProfileError(
            "BASIC",
            "Description element is not supported in BASIC profile line items",
        )
    if len(product.characteristics) > 0:
        raise InvalidProfileError(
            "BASIC",
            "ApplicableProductCharacteristic element is not supported in "
            "BASIC profile line items",
        )
    if len(product.classifications) > 0:
        raise InvalidProfileError(
            "BASIC",
            "DesignatedProductClassification element is not supported in "
            "BASIC profile line items",
        )
    if product.origin_country is not None:
        raise InvalidProfileError(
            "BASIC",
            "OriginCountry element is not supported in BASIC profile "
            "line items",
        )
    if agreement.buyer_order_line_id is not None:
        raise InvalidProfileError(
            "BASIC",
            "BuyerOrderReferencedDocument element is not supported in BASIC "
            "profile line items",
        )
    if agreement.gross_unit_price is not None:
        raise InvalidProfileError(
            "BASIC",
            "GrossPriceProductTradePrice element is not supported in BASIC "
            "profile line items",
        )
    if settlement.billing_period is not None:
        raise InvalidProfileError(
            "BASIC",
            "BillingSpecifiedPeriod is not supported in BASIC profile "
            "line items",
        )
    if settlement.doc_ref is not None:
        raise InvalidProfileError(
            "BASIC",
            "AdditionalReferencedDocument element is not supported in "
            "BASIC profile line items",
        )
    if settlement.trade_account_id is not None:
        raise InvalidProfileError(
            "BASIC",
            "ReceivableSpecifiedTradeAccountingAccount element is not "
            "supported in BASIC profile line items",
        )

    return LineItem(
        doc.id,
        product.name,
        agreement.net_price,
        delivery.billed_quantity,
        settlement.total_amount,
        settlement.tax_rate,
        settlement.tax_category,
        global_id=product.global_id,
        basis_quantity=agreement.basis_quantity,
        allowances=settlement.allowances,
        charges=settlement.charges,
    )


def _parse_en16931_line_item(
    el: ET.Element, default_currency: str
) -> EN16931LineItem:
    doc = _parse_line_document(el)
    product = _parse_trade_product(el)
    agreement = _parse_line_agreement(el, default_currency)
    delivery = _parse_line_delivery(el)
    settlement = _parse_line_settlement(el, default_currency)
    return EN16931LineItem(
        doc.id,
        product.name,
        agreement.net_price,
        delivery.billed_quantity,
        settlement.total_amount,
        settlement.tax_rate,
        settlement.tax_category,
        global_id=product.global_id,
        basis_quantity=agreement.basis_quantity,
        gross_unit_price=agreement.gross_unit_price,
        allowances=settlement.allowances,
        charges=settlement.charges,
        note=doc.note,
        seller_assigned_id=product.seller_id,
        buyer_assigned_id=product.buyer_id,
        description=product.description,
        product_characteristics=product.characteristics,
        product_classifications=product.classifications,
        origin_country=product.origin_country,
        buyer_order_line_id=agreement.buyer_order_line_id,
        billing_period=settlement.billing_period,
        doc_ref=settlement.doc_ref,
        trade_account_id=settlement.trade_account_id,
    )


class _LineDocument(NamedTuple):
    id: str
    note: IncludedNote | None  # EN16931+


def _parse_line_document(parent: ET.Element) -> _LineDocument:
    el = parent.find(f"./{{{NS_RAM}}}AssociatedDocumentLineDocument")
    if el is None:
        raise InvalidXMLError(
            "AssociatedDocumentLineDocument element not found"
        )
    id = _find_text(el, f"./{{{NS_RAM}}}LineID")

    note: IncludedNote | None = None
    note_el = el.find(f"./{{{NS_RAM}}}IncludedNote")
    if note_el is not None:
        note = _parse_note(note_el)

    return _LineDocument(id, note)


class _TradeProduct(NamedTuple):
    name: str
    global_id: ID | None
    seller_id: str | None  # EN16931+
    buyer_id: str | None  # EN16931+
    description: str | None  # EN16931+
    characteristics: list[ProductCharacteristic]  # EN16931+
    classifications: list[ProductClassification]  # EN16931+
    origin_country: str | None  # EN16931+


def _parse_trade_product(parent: ET.Element) -> _TradeProduct:
    el = parent.find(f"./{{{NS_RAM}}}SpecifiedTradeProduct")
    if el is None:
        raise InvalidXMLError("SpecifiedTradeProduct element not found")
    global_id = _find_id_optional(el, f"./{{{NS_RAM}}}GlobalID")
    seller_id = _find_text_optional(el, f"./{{{NS_RAM}}}SellerAssignedID")
    buyer_id = _find_text_optional(el, f"./{{{NS_RAM}}}BuyerAssignedID")
    name = _find_text(el, f"./{{{NS_RAM}}}Name")
    description = _find_text_optional(el, f"./{{{NS_RAM}}}Description")
    characteristics = [
        _parse_product_characteristic(pc_el)
        for pc_el in el.findall(
            f"./{{{NS_RAM}}}ApplicableProductCharacteristic"
        )
    ]
    classifications = [
        _parse_product_classification(pc_el)
        for pc_el in el.findall(
            f"./{{{NS_RAM}}}DesignatedProductClassification"
        )
    ]
    origin_country = _find_text_optional(
        el, f"./{{{NS_RAM}}}OriginCountry/{{{NS_RAM}}}ID"
    )
    return _TradeProduct(
        name,
        global_id,
        seller_id,
        buyer_id,
        description,
        characteristics,
        classifications,
        origin_country,
    )


def _parse_product_characteristic(parent: ET.Element) -> ProductCharacteristic:
    description = _find_text(parent, f"./{{{NS_RAM}}}Description")
    value = _find_text(parent, f"./{{{NS_RAM}}}Value")
    return ProductCharacteristic(description, value)


def _parse_product_classification(parent: ET.Element) -> ProductClassification:
    class_code_el = parent.find(f"./{{{NS_RAM}}}ClassCode")
    if class_code_el is None:
        raise InvalidXMLError("ClassCode element not found")
    class_code = class_code_el.text
    if class_code is None:
        raise InvalidXMLError("ClassCode element has no text")
    list_id_s = class_code_el.attrib.get("listID")
    list_version_id = class_code_el.attrib.get("listVersionID")

    try:
        list_id = ItemTypeCode(list_id_s) if list_id_s is not None else None
    except ValueError as exc:
        raise InvalidXMLError(str(exc)) from exc

    return ProductClassification(
        class_code, list_id=list_id, list_version_id=list_version_id
    )


class _LineAgreement(NamedTuple):
    gross_unit_price: tuple[Money, OptionalQuantity | None] | None  # EN16931+
    gross_allowance_or_charge: LineAllowance | LineCharge | None  # EN16931+
    net_price: Money
    basis_quantity: OptionalQuantity | None
    buyer_order_line_id: str | None  # EN16931+


def _parse_line_agreement(
    parent: ET.Element, default_currency: str
) -> _LineAgreement:
    el = parent.find(f"./{{{NS_RAM}}}SpecifiedLineTradeAgreement")
    if el is None:
        raise InvalidXMLError("SpecifiedLineTradeAgreement element not found")

    (gross_price, gross_charge) = _parse_gross_line_price(el, default_currency)

    net_price_el = el.find(f"./{{{NS_RAM}}}NetPriceProductTradePrice")
    if net_price_el is None:
        raise InvalidXMLError("NetPriceProductTradePrice element not found")
    net_price = _find_amount(
        net_price_el, f"./{{{NS_RAM}}}ChargeAmount", default_currency
    )
    basis_quantity = _find_optional_quantity_optional(
        el, f"./{{{NS_RAM}}}BasisQuantity"
    )
    buyer_order_line_id = _find_text_optional(
        el, f"./{{{NS_RAM}}}BuyerOrderReferencedDocument/{{{NS_RAM}}}LineID"
    )
    return _LineAgreement(
        gross_price,
        gross_charge,
        net_price,
        basis_quantity,
        buyer_order_line_id,
    )


def _parse_gross_line_price(
    parent: ET.Element, default_currency: str
) -> tuple[
    tuple[Money, OptionalQuantity | None] | None,
    LineAllowance | LineCharge | None,
]:
    el = parent.find(f"./{{{NS_RAM}}}GrossPriceProductTradePrice")
    if el is None:
        return None, None
    gross_amount = _find_amount(
        el, f"./{{{NS_RAM}}}ChargeAmount", default_currency
    )
    gross_quantity = _find_optional_quantity_optional(
        el, f"./{{{NS_RAM}}}BasisQuantity"
    )
    allowance: LineAllowance | LineCharge | None = None
    allowance_el = el.find(f"./{{{NS_RAM}}}AppliedTradeAllowanceCharge")
    if allowance_el is not None:
        allowance = _parse_line_allowance_or_charge(
            allowance_el, default_currency
        )
        if allowance.reason is not None:
            raise InvalidProfileError(
                "EN16931",
                "Reason element is not supported in "
                "AppliedTradeAllowanceCharge",
            )
    return (gross_amount, gross_quantity), allowance


class _LineDelivery(NamedTuple):
    billed_quantity: Quantity


def _parse_line_delivery(parent: ET.Element) -> _LineDelivery:
    el = parent.find(f"./{{{NS_RAM}}}SpecifiedLineTradeDelivery")
    if el is None:
        raise InvalidXMLError("SpecifiedLineTradeDelivery element not found")
    billed_quantity = _find_quantity(el, f"./{{{NS_RAM}}}BilledQuantity")
    return _LineDelivery(billed_quantity)


class _LineSettlement(NamedTuple):
    tax_category: TaxCategoryCode
    tax_rate: Decimal | None
    allowances: Sequence[LineAllowance]
    charges: Sequence[LineCharge]
    total_amount: Money
    billing_period: tuple[date, date] | None  # EN16931+
    doc_ref: DocRef | None  # EN16931+
    trade_account_id: str | None  # EN16931+


def _parse_line_settlement(
    parent: ET.Element, default_currency: str
) -> _LineSettlement:
    el = parent.find(f"./{{{NS_RAM}}}SpecifiedLineTradeSettlement")
    if el is None:
        raise InvalidXMLError("SpecifiedLineTradeSettlement element not found")
    tax_el = el.find(f"./{{{NS_RAM}}}ApplicableTradeTax")
    if tax_el is None:
        raise InvalidXMLError("ApplicableTradeTax element not found")
    tax_category, tax_rate = _parse_tax_simple(tax_el)
    allowances = [
        _parse_line_allowance_or_charge(ac_el, default_currency)
        for ac_el in el.findall(f"./{{{NS_RAM}}}SpecifiedTradeAllowanceCharge")
    ]
    total_amount = _parse_line_summation(el, default_currency)
    billing_period = _parse_billing_period_optional(el)

    doc_ref: DocRef | None = None
    ref_doc_el = el.find(f"./{{{NS_RAM}}}AdditionalReferencedDocument")
    if ref_doc_el is not None:
        doc_ref = _parse_doc_ref(ref_doc_el)

    trade_account_id = _find_text_optional(
        el,
        f"./{{{NS_RAM}}}ReceivableSpecifiedTradeAccountingAccount/{{{NS_RAM}}}ID",
    )

    return _LineSettlement(
        tax_category,
        tax_rate,
        [a for a in allowances if isinstance(a, LineAllowance)],
        [c for c in allowances if isinstance(c, LineCharge)],
        total_amount,
        billing_period,
        doc_ref,
        trade_account_id,
    )


def _parse_line_summation(parent: ET.Element, default_currency: str) -> Money:
    el = parent.find(
        f"./{{{NS_RAM}}}SpecifiedTradeSettlementLineMonetarySummation"
    )
    if el is None:
        raise InvalidXMLError(
            "SpecifiedTradeSettlementLineMonetarySummation element not found"
        )
    return _find_amount(el, f"./{{{NS_RAM}}}LineTotalAmount", default_currency)


def _parse_line_allowance_or_charge(
    el: ET.Element, default_currency: str
) -> LineAllowance | LineCharge:
    surcharge = _find_indicator(el, f"./{{{NS_RAM}}}ChargeIndicator")
    percent = _find_percent_optional(el, f"./{{{NS_RAM}}}CalculationPercent")
    basis_amount = _find_amount_optional(
        el, f"./{{{NS_RAM}}}BasisAmount", default_currency
    )
    actual_amount = _find_amount(
        el, f"./{{{NS_RAM}}}ActualAmount", default_currency
    )
    service_code: SpecialServiceCode | None = None
    allowance_code: AllowanceChargeCode | None = None
    reason_code_s = _find_text_optional(el, f"./{{{NS_RAM}}}ReasonCode")
    if reason_code_s is not None:
        try:
            if surcharge:
                service_code = SpecialServiceCode(reason_code_s)
            else:
                allowance_code = AllowanceChargeCode(int(reason_code_s))
        except ValueError as exc:
            raise InvalidXMLError(str(exc)) from exc
    reason = _find_text_optional(el, f"./{{{NS_RAM}}}Reason")
    if surcharge:
        return LineCharge(
            actual_amount,
            service_code,
            reason,
            percent=percent,
            basis_amount=basis_amount,
        )
    else:
        return LineAllowance(
            actual_amount,
            allowance_code,
            reason,
            percent=percent,
            basis_amount=basis_amount,
        )


def _parse_allowance_or_charge(
    el: ET.Element, default_currency: str
) -> DocumentAllowance | DocumentCharge:
    line_allowance = _parse_line_allowance_or_charge(el, default_currency)
    tax_el = el.find(f"./{{{NS_RAM}}}CategoryTradeTax")
    if tax_el is None:
        raise InvalidXMLError("CategoryTradeTax element not found")
    tax_type_code = _find_text(tax_el, f"./{{{NS_RAM}}}TypeCode")
    if tax_type_code != "VAT":
        raise InvalidXMLError(f"Invalid tax TypeCode: {tax_type_code}")
    tax_category_s = _find_text(tax_el, f"./{{{NS_RAM}}}CategoryCode")
    try:
        tax_category = TaxCategoryCode(tax_category_s)
    except ValueError as exc:
        raise InvalidXMLError(str(exc)) from exc
    tax_rate = _find_percent_optional(
        tax_el, f"./{{{NS_RAM}}}RateApplicablePercent"
    )
    if isinstance(line_allowance, LineCharge):
        return DocumentCharge(
            line_allowance.actual_amount,
            line_allowance.reason_code,
            line_allowance.reason,
            percent=line_allowance.percent,
            basis_amount=line_allowance.basis_amount,
            tax_category=tax_category,
            tax_rate=tax_rate,
        )
    else:
        return DocumentAllowance(
            line_allowance.actual_amount,
            line_allowance.reason_code,
            line_allowance.reason,
            percent=line_allowance.percent,
            basis_amount=line_allowance.basis_amount,
            tax_category=tax_category,
            tax_rate=tax_rate,
        )


def _parse_payment_terms(parent: ET.Element) -> PaymentTerms | None:
    el = parent.find(f"./{{{NS_RAM}}}SpecifiedTradePaymentTerms")
    if el is None:
        return None
    description = _find_text_optional(el, f"./{{{NS_RAM}}}Description")
    due_date = _find_date_optional(el, f"./{{{NS_RAM}}}DueDateDateTime")
    mandate_id = _find_text_optional(el, f"./{{{NS_RAM}}}DirectDebitMandateID")
    return PaymentTerms(
        description=description,
        due_date=due_date,
        direct_debit_mandate_id=mandate_id,
    )


def _parse_summation(
    parent: ET.Element, default_currency: str
) -> _SettlementSummation:
    el = parent.find(
        f"./{{{NS_RAM}}}SpecifiedTradeSettlementHeaderMonetarySummation"
    )
    if el is None:
        raise InvalidXMLError(
            "SpecifiedTradeSettlementHeaderMonetarySummation element not found"
        )
    line_total = _find_amount_optional(
        el, f"./{{{NS_RAM}}}LineTotalAmount", default_currency
    )
    charge_total = _find_amount_optional(
        el, f"./{{{NS_RAM}}}ChargeTotalAmount", default_currency
    )
    allowance_total = _find_amount_optional(
        el, f"./{{{NS_RAM}}}AllowanceTotalAmount", default_currency
    )
    tax_basis_total = _find_amount(
        el, f"./{{{NS_RAM}}}TaxBasisTotalAmount", default_currency
    )
    tax_totals = _find_all_amounts(
        el, f"./{{{NS_RAM}}}TaxTotalAmount", default_currency
    )
    rounding_amount = _find_amount_optional(
        el, f"./{{{NS_RAM}}}RoundingAmount", default_currency
    )
    grand_total = _find_amount(
        el, f"./{{{NS_RAM}}}GrandTotalAmount", default_currency
    )
    prepaid = _find_amount_optional(
        el, f"./{{{NS_RAM}}}TotalPrepaidAmount", default_currency
    )
    due_payable = _find_amount(
        el, f"./{{{NS_RAM}}}DuePayableAmount", default_currency
    )
    return _SettlementSummation(
        line_total,
        tax_basis_total,
        tax_totals,
        grand_total,
        due_payable,
        charge_total,
        allowance_total,
        prepaid,
        rounding_amount,
    )


def _parse_referenced_invoices(
    parent: ET.Element,
) -> list[tuple[str, date | None]]:
    els = parent.findall(f"./{{{NS_RAM}}}InvoiceReferencedDocument")
    return [_parse_referenced_invoice(el) for el in els]


def _parse_referenced_invoice(el: ET.Element) -> tuple[str, date | None]:
    id = _find_text(el, f"./{{{NS_RAM}}}IssuerAssignedID")
    issue_date = _find_date_optional(
        el, f"./{{{NS_RAM}}}FormattedIssueDateTime"
    )
    return id, issue_date


# Parsing recurring elements


def _parse_trade_party(parent: ET.Element, tag: str) -> TradeParty:
    trade_party = _parse_trade_party_optional(parent, tag)
    if trade_party is None:
        raise InvalidXMLError(f"{tag} element not found")
    return trade_party


def _parse_trade_party_optional(
    parent: ET.Element, tag: str
) -> TradeParty | None:
    party_el = parent.find(tag)
    if party_el is None:
        return None
    ids = _find_all_texts(party_el, f"./{{{NS_RAM}}}ID")
    global_ids = _find_all_ids(party_el, f"./{{{NS_RAM}}}GlobalID")
    name = _find_text(party_el, f"./{{{NS_RAM}}}Name")
    description = _find_text_optional(party_el, f"./{{{NS_RAM}}}Description")
    legal_org_id, legal_org_name = _parse_legal_org(party_el)
    contacts = [
        _parse_trade_contact(contact_el)
        for contact_el in party_el.findall(
            f"./{{{NS_RAM}}}DefinedTradeContact"
        )
    ]
    address = _parse_address(party_el)
    email = _parse_email(party_el)
    tax_number: str | None = None
    vat_id: str | None = None
    for tax_reg in party_el.findall(f"./{{{NS_RAM}}}SpecifiedTaxRegistration"):
        is_vat_id, tax_reg_id = _parse_tax_reg(tax_reg)
        if is_vat_id:
            if vat_id is not None:
                raise InvalidXMLError("Multiple VAT IDs found")
            vat_id = tax_reg_id
        else:
            if tax_number is not None:
                raise InvalidXMLError("Multiple tax numbers found")
            tax_number = tax_reg_id

    return TradeParty(
        name,
        address,
        email,
        description=description,
        tax_number=tax_number,
        vat_id=vat_id,
        ids=ids,
        global_ids=global_ids,
        legal_id=legal_org_id,
        trading_business_name=legal_org_name,
        contacts=contacts,
    )


def _parse_legal_org(parent: ET.Element) -> tuple[ID | None, str | None]:
    legal_org_el = parent.find(f"./{{{NS_RAM}}}SpecifiedLegalOrganization")
    if legal_org_el is None:
        return None, None
    id = _find_id_optional(legal_org_el, f"./{{{NS_RAM}}}ID")
    name = _find_text_optional(
        legal_org_el, f"./{{{NS_RAM}}}TradingBusinessName"
    )
    return id, name


def _parse_tax_reg(parent: ET.Element) -> tuple[bool, str]:
    """Parse a SpecifiedTaxRegistration element.

    Return a tuple with a boolean indicating whether the ID is a VAT ID (True)
    or a tax number (False) and the ID itself.
    """
    id_el = parent.find(f"./{{{NS_RAM}}}ID")
    if id_el is None:
        raise InvalidXMLError(
            "ID element not found in SpecifiedTaxRegistration"
        )
    scheme = id_el.attrib.get("schemeID")
    id = id_el.text
    if id is None:
        raise InvalidXMLError("ID element has no text")
    match scheme:
        case "FC":
            return False, id
        case "VA":
            return True, id
        case _:
            raise InvalidXMLError(f"Invalid schemeID: {scheme}")


def _parse_trade_contact(el: ET.Element) -> TradeContact:
    person_name = _find_text_optional(el, f"./{{{NS_RAM}}}PersonName")
    department_name = _find_text_optional(el, f"./{{{NS_RAM}}}DepartmentName")
    phone = _find_text_optional(
        el,
        f"./{{{NS_RAM}}}TelephoneUniversalCommunication/{{{NS_RAM}}}CompleteNumber",
    )
    email = _find_text_optional(
        el, f"./{{{NS_RAM}}}EmailURIUniversalCommunication/{{{NS_RAM}}}URIID"
    )
    return TradeContact(
        person_name=person_name,
        department_name=department_name,
        phone=phone,
        email=email,
    )


def _parse_address(parent: ET.Element) -> PostalAddress | None:
    address_el = parent.find(f"./{{{NS_RAM}}}PostalTradeAddress")
    if address_el is None:
        return None
    post_code = _find_text_optional(address_el, f"./{{{NS_RAM}}}PostcodeCode")
    line_one = _find_text_optional(address_el, f"./{{{NS_RAM}}}LineOne")
    line_two = _find_text_optional(address_el, f"./{{{NS_RAM}}}LineTwo")
    line_three = _find_text_optional(address_el, f"./{{{NS_RAM}}}LineThree")
    city = _find_text_optional(address_el, f"./{{{NS_RAM}}}CityName")
    country_code = _find_text(address_el, f"./{{{NS_RAM}}}CountryID")
    country_sub = _find_text_optional(
        address_el, f"./{{{NS_RAM}}}CountrySubDivisionName"
    )
    return PostalAddress(
        country_code,
        country_sub,
        post_code,
        city,
        line_one,
        line_two,
        line_three,
    )


def _parse_email(parent: ET.Element) -> str | None:
    id_el = parent.find(
        f"./{{{NS_RAM}}}URIUniversalCommunication/{{{NS_RAM}}}URIID"
    )
    if id_el is None:
        return None
    if id_el.attrib.get("schemeID") != "EM":
        raise InvalidXMLError("Invalid schemeID for email")
    if id_el.text is None:
        raise InvalidXMLError("URIID element has no text")
    return id_el.text


def _parse_tax_simple(
    el: ET.Element,
) -> tuple[TaxCategoryCode, Decimal | None]:
    type_code_s = _find_text(el, f"./{{{NS_RAM}}}TypeCode")
    if type_code_s != "VAT":
        raise InvalidXMLError(f"Invalid tax TypeCode: {type_code_s}")
    category_code_s = _find_text(el, f"./{{{NS_RAM}}}CategoryCode")
    try:
        category_code = TaxCategoryCode(category_code_s)
    except ValueError as exc:
        raise InvalidXMLError(str(exc)) from exc
    rate = _find_percent_optional(el, f"./{{{NS_RAM}}}RateApplicablePercent")
    return category_code, rate


def _parse_tax(el: ET.Element, default_currency: str) -> Tax:
    category_code, rate = _parse_tax_simple(el)
    calculated_amount = _find_amount(
        el, f"./{{{NS_RAM}}}CalculatedAmount", default_currency
    )
    exemption_reason = _find_text_optional(
        el, f"./{{{NS_RAM}}}ExemptionReason"
    )
    basis_amount = _find_amount(
        el, f"./{{{NS_RAM}}}BasisAmount", default_currency
    )

    exemption_reason_code: VATExemptionCode | None = None
    exemption_reason_code_s = _find_text_optional(
        el, f"./{{{NS_RAM}}}ExemptionReasonCode"
    )
    if exemption_reason_code_s is not None:
        try:
            exemption_reason_code = VATExemptionCode(exemption_reason_code_s)
        except ValueError as exc:
            raise InvalidXMLError(str(exc)) from exc

    tax_point_date = _find_date_optional(el, f"./{{{NS_RAM}}}TaxPointDate")

    due_date_type_code_s = _find_text_optional(
        el, f"./{{{NS_RAM}}}DueDateTypeCode"
    )
    due_date_type_code: PaymentTimeCode | None = None
    if due_date_type_code_s is not None:
        try:
            due_date_type_code = PaymentTimeCode(int(due_date_type_code_s))
        except ValueError as exc:
            raise InvalidXMLError(str(exc)) from exc

    return Tax(
        calculated_amount,
        basis_amount,
        rate,
        category_code,
        exemption_reason=exemption_reason,
        exemption_reason_code=exemption_reason_code,
        tax_point_date=tax_point_date,
        due_date_type_code=due_date_type_code,
    )


def _parse_billing_period_optional(
    parent: ET.Element,
) -> tuple[date, date] | None:
    el = parent.find(f"./{{{NS_RAM}}}BillingSpecifiedPeriod")
    if el is None:
        return None
    start_date = _find_date(el, f"./{{{NS_RAM}}}StartDateTime")
    end_date = _find_date(el, f"./{{{NS_RAM}}}EndDateTime")
    return start_date, end_date


def _parse_doc_ref(el: ET.Element) -> DocRef:
    id = _find_text_optional(el, f"./{{{NS_RAM}}}IssuerAssignedID")
    type_code = _find_text(el, f"./{{{NS_RAM}}}TypeCode")
    if type_code != "130":
        raise InvalidXMLError(f"Invalid TypeCode: {type_code}")
    ref_type_code: ReferenceQualifierCode | None = None
    ref_type_code_s = _find_text_optional(
        el, f"./{{{NS_RAM}}}ReferenceTypeCode"
    )
    if ref_type_code_s is not None:
        try:
            ref_type_code = ReferenceQualifierCode(ref_type_code_s)
        except ValueError as exc:
            raise InvalidXMLError(str(exc)) from exc
    return (id, ref_type_code)


def _parse_reference_document(el: ET.Element) -> ReferenceDocument:
    id = _find_text(el, f"./{{{NS_RAM}}}IssuerAssignedID")
    type_code_s = _find_text(el, f"./{{{NS_RAM}}}TypeCode")
    try:
        type_code = DocumentTypeCode(int(type_code_s))
    except ValueError as exc:
        raise InvalidXMLError(str(exc)) from exc
    uri = _find_text_optional(el, f"./{{{NS_RAM}}}URIID")
    name = _find_text_optional(el, f"./{{{NS_RAM}}}Name")
    attachment = _parse_attachment_optional(el)
    ref_type_code: ReferenceQualifierCode | None = None
    ref_type_code_s = _find_text_optional(
        el, f"./{{{NS_RAM}}}ReferenceTypeCode"
    )
    if ref_type_code_s is not None:
        try:
            ref_type_code = ReferenceQualifierCode(ref_type_code_s)
        except ValueError as exc:
            raise InvalidXMLError(str(exc)) from exc

    return ReferenceDocument(
        id, type_code, name, uri, attachment, reference_type_code=ref_type_code
    )


def _parse_attachment_optional(parent: ET.Element) -> Attachment | None:
    el = parent.find(f"./{{{NS_RAM}}}AttachmentBinaryObject")
    if el is None:
        return None
    content = el.text
    mime_type = el.attrib.get("mimeCode")
    filename = el.attrib.get("filename")
    if content is None:
        raise InvalidXMLError("AttachmentBinaryObject element has no text")
    if not mime_type:
        raise InvalidXMLError("AttachmentBinaryObject has no mimeCode")
    if mime_type not in ALLOWED_MIME_TYPES:
        raise InvalidXMLError(f"MIME type not allowed: {mime_type}")
    if not filename:
        raise InvalidXMLError("AttachmentBinaryObject has no filename")
    return b64decode(content), mime_type, filename
