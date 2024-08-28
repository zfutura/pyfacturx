from __future__ import annotations

from ._locale import setup_locale
from .model import MinimumInvoice, PostalAddress, TradeContact, TradeParty
from .type_codes import DocumentTypeCode, IdentifierSchemeCode
from .types import ID

__all__ = ["format_invoice_as_text", "format_trade_party", "format_address"]

_ = setup_locale()


def N_(s: str) -> str:
    return s


_DOCUMENT_TYPE_NAMES = {
    DocumentTypeCode.VALIDATED_PRICED_TENDER: N_("Validated Priced Tender"),
    DocumentTypeCode.INVOICING_DATA_SHEET: N_("Invoicing Data Sheet"),
    DocumentTypeCode.PRO_FORMA_INVOICE: N_("Pro Forma Invoice"),
    DocumentTypeCode.PARTIAL_INVOICE: N_("Partial Invoice"),
    DocumentTypeCode.INVOICE: N_("Invoice"),
    DocumentTypeCode.CREDIT_NOTE: N_("Credit Note"),
    DocumentTypeCode.CORRECTION: N_("Correction"),
    DocumentTypeCode.PREPAYMENT: N_("Prepayment"),
    DocumentTypeCode.RELATED_DOCUMENT: N_("Related Document"),
}


def format_invoice_as_text(invoice: MinimumInvoice) -> str:
    if type(invoice) is not MinimumInvoice:
        raise NotImplementedError(
            "Only MINIMUM invoices are supported at this time"
        )

    lines: list[str] = []

    type_name = _(_DOCUMENT_TYPE_NAMES[invoice.type_code])
    lines += [
        (
            "{document_type} {invoice_number}".format(
                document_type=type_name, invoice_number=invoice.invoice_number
            )
        ),
        _("Date: {invoice_date:%Y-%m-%d}").format(
            invoice_date=invoice.invoice_date
        ),
        "",
    ]

    lines += [
        _header(_("Sender")),
        format_trade_party(invoice.seller),
        "",
        _header(_("Recipient")),
        format_trade_party(invoice.buyer),
        "",
    ]
    if invoice.business_process_id is not None:
        lines.append(
            _("Business Process ID: {}").format(invoice.business_process_id)
        )
    if invoice.buyer_reference is not None:
        lines.append(_("Buyer Reference: {}").format(invoice.buyer_reference))
    if invoice.buyer_order_id is not None:
        lines.append(_("Buyer Order ID: {}").format(invoice.buyer_order_id))
    lines += [
        _header(_("Totals")),
        _format_totals(invoice),
    ]

    return "\n".join(lines)


def _format_totals(invoice: MinimumInvoice) -> str:
    lines = []
    if invoice.line_total_amount:
        lines.append(
            _("Line Total (net): {}").format(str(invoice.line_total_amount))
        )
    lines.append(_("Net: {}").format(str(invoice.tax_basis_total_amount)))
    for tax_amount in invoice.tax_total_amounts:
        lines.append(_("Tax: {}").format(str(tax_amount)))
    lines.append(_("Gross: {}").format(str(invoice.grand_total_amount)))
    lines.append(_("Due amount: {}").format(str(invoice.due_payable_amount)))
    return "\n".join(lines)


def format_trade_party(trade_party: TradeParty) -> str:
    lines = []

    if trade_party.name:
        if trade_party.trading_business_name:
            lines.append(
                _("{name} ({trading_business_name})").format(
                    name=trade_party.name,
                    trading_business_name=trade_party.trading_business_name,
                )
            )
        else:
            lines.append(trade_party.name)
    if trade_party.description:
        lines.append(trade_party.description)
    if trade_party.address:
        lines.append(format_address(trade_party.address))
    if trade_party.email:
        lines.append(trade_party.email)
    if trade_party.vat_id:
        lines.append(_("VAT ID: {}").format(trade_party.vat_id))
    if trade_party.tax_number:
        lines.append(_("Tax Number: {}").format(trade_party.tax_number))
    if len(trade_party.ids) == 1:
        lines.append(_("ID: {}").format(trade_party.ids[0]))
    elif len(trade_party.ids) > 1:
        lines.append(_("IDs: {}").format(", ".join(trade_party.ids)))
    for gid in trade_party.global_ids:
        lines.append(_format_global_id(gid))
    if trade_party.legal_id:
        lines.append(_format_global_id(trade_party.legal_id))
    for contact in trade_party.contacts:
        lines.append(format_trade_contact(contact))

    return "\n".join(lines)


def format_address(address: PostalAddress) -> str:
    lines = []
    if address.line_one:
        lines.append(address.line_one)
    if address.line_two:
        lines.append(address.line_two)
    if address.line_three:
        lines.append(address.line_three)
    city_line = address.country_code
    if address.post_code:
        city_line += f" {address.post_code}"
    if address.city:
        city_line += f" {address.city}"
    lines.append(city_line)
    if address.country_subdivision:
        lines.append(address.country_subdivision)
    return "\n".join(lines)


def format_trade_contact(contact: TradeContact) -> str:
    lines = [_("Contact:")]
    if contact.person_name:
        lines.append(f"  {contact.person_name}")
    elif contact.department_name:
        lines.append(f"  {contact.department_name}")
    if contact.phone:
        lines.append(_("  Phone: {phone}").format(phone=contact.phone))
    if contact.email:
        lines.append(f"  {contact.email}")
    return "\n".join(lines)


def _format_global_id(global_id: ID) -> str:
    id, code = global_id
    if code is None:
        return _("Global ID: {id}").format(id=id)
    if isinstance(code, IdentifierSchemeCode):
        code = code.name
    return _("{id_type}: {id}").format(id_type=code, id=id)


def _header(header: str) -> str:
    return f"{header}\n{'-' * len(header)}\n"


if __name__ == "__main__":
    # Print a sample invoice

    import locale

    from .test_data import minimum_rechnung

    locale.setlocale(locale.LC_ALL, "")

    invoice = minimum_rechnung()
    print(format_invoice_as_text(invoice))
