from __future__ import annotations

from collections.abc import Sequence
from gettext import ngettext
from textwrap import indent

from facturx.quantities import QUANTITY_NAMES

from ._locale import setup_locale
from .model import (
    BankAccount,
    BasicInvoice,
    BasicWLInvoice,
    DocumentAllowance,
    DocumentCharge,
    EN16931Invoice,
    IncludedNote,
    LineAllowance,
    LineCharge,
    LineItem,
    MinimumInvoice,
    PaymentMeans,
    PaymentTerms,
    PostalAddress,
    ReferenceDocument,
    TradeContact,
    TradeParty,
)
from .type_codes import (
    DOCUMENT_TYPE_NAMES,
    PAYMENT_MEANS_NAMES,
    PAYMENT_TIME_CODE_NAMES,
    REFERENCE_QUALIFIER_NAMES,
    TEXT_SUBJECT_CODE_NAMES,
    IdentifierSchemeCode,
)
from .types import ID, OptionalQuantity, Quantity

__all__ = ["format_invoice_as_text", "format_trade_party", "format_address"]

_ = setup_locale()


def format_invoice_as_text(invoice: MinimumInvoice) -> str:
    lines: list[str] = []

    type_name = _(DOCUMENT_TYPE_NAMES[invoice.type_code])
    lines += [
        (
            "{document_type} {invoice_number}".format(
                document_type=type_name, invoice_number=invoice.invoice_number
            )
        ),
        _("Date: {invoice_date:%Y-%m-%d}").format(
            invoice_date=invoice.invoice_date
        ),
    ]
    if isinstance(invoice, BasicWLInvoice):
        if invoice.delivery_date:
            lines.append(
                _("Delivery Date: {delivery_date:%Y-%m-%d}").format(
                    delivery_date=invoice.delivery_date
                )
            )
        if invoice.billing_period:
            start, end = invoice.billing_period
            lines.append(
                _("Billing Period: {start:%Y-%m-%d}–{end:%Y-%m-%d}").format(
                    start=start, end=end
                )
            )

    lines += [
        _header(_("Sender")),
        format_trade_party(invoice.seller),
        _header(_("Recipient")),
        format_trade_party(invoice.buyer),
    ]
    if isinstance(invoice, BasicWLInvoice):
        if invoice.ship_to:
            lines += [
                _header(_("Ship To")),
                format_trade_party(invoice.ship_to),
            ]
        if invoice.seller_tax_representative:
            lines += [
                _header(_("Seller's Tax Representative")),
                format_trade_party(invoice.seller_tax_representative),
            ]

    refs = _format_references(invoice)
    if refs:
        lines += [_header(_("References")), refs]
    if isinstance(invoice, BasicWLInvoice):
        if invoice.notes:
            formatted_notes = [format_note(note) for note in invoice.notes]
            lines += [
                _header(_("Notes")),
                "\n\n----\n\n".join(formatted_notes),
            ]
    if isinstance(invoice, BasicInvoice):
        lines += [
            _header(_("Line Items")),
            _format_line_items(invoice.line_items),
        ]
    if isinstance(invoice, BasicWLInvoice):
        if invoice.charges:
            lines += [
                _header(_("Surcharges")),
                _format_allowances_and_charges(invoice.charges),
            ]
        if invoice.allowances:
            lines += [
                _header(_("Deductions")),
                _format_allowances_and_charges(invoice.allowances),
            ]
        lines += [
            _header(_("Tax")),
            _format_tax(invoice),
        ]
    lines += [
        _header(_("Totals")),
        _format_totals(invoice),
    ]
    if isinstance(invoice, BasicWLInvoice):
        lines.append(_format_payment(invoice))

    return "\n".join(lines)


def _format_references(invoice: MinimumInvoice) -> str:
    lines = []
    if isinstance(invoice, BasicWLInvoice):
        for preceding in invoice.preceding_invoices:
            number, date = preceding
            if date:
                lines.append(
                    _("Related Invoice: {number} ({date:%Y-%m-%d})").format(
                        number=number, date=date
                    )
                )
            else:
                lines.append(
                    _("Related Invoice: {number}").format(number=number)
                )
    if isinstance(invoice, BasicWLInvoice) and invoice.contract_id:
        lines.append(_("Contract ID: {}").format(invoice.contract_id))
    if isinstance(invoice, EN16931Invoice) and invoice.procuring_project:
        id, name = invoice.procuring_project
        lines.append(
            _("Procuring Project: {id} {name}").format(id=id, name=name)
        )
    if invoice.business_process_id is not None:
        lines.append(
            _("Business Process ID: {}").format(invoice.business_process_id)
        )
    if invoice.buyer_reference is not None:
        lines.append(_("Buyer Reference: {}").format(invoice.buyer_reference))
    if invoice.buyer_order_id is not None:
        lines.append(_("Buyer Order ID: {}").format(invoice.buyer_order_id))
    if isinstance(invoice, EN16931Invoice) and invoice.seller_order_id:
        lines.append(_("Seller Order ID: {}").format(invoice.seller_order_id))
    if isinstance(invoice, BasicWLInvoice) and invoice.despatch_advice_id:
        lines.append(
            _("Despatch Advice ID: {}").format(invoice.despatch_advice_id)
        )
    if isinstance(invoice, EN16931Invoice):
        lines.append(
            _("Receiving Advice ID: {}").format(invoice.receiving_advice_id)
        )
    if isinstance(invoice, BasicWLInvoice) and invoice.despatch_advice_id:
        for id in invoice.receiver_accounting_ids:
            lines.append(_("Receiver Accounting ID: {}").format(id))
    if isinstance(invoice, EN16931Invoice):
        for doc in invoice.referenced_docs:
            lines.append(format_reference_doc(doc))
    return "\n".join(lines)


def _format_line_items(line_items: Sequence[LineItem]) -> str:
    lines = []
    for li in line_items:
        lines.append(
            _("{id} {net_price} {quantity} {total_price}").format(
                id=li.id,
                net_price=li.net_price,
                quantity=format_quantity(li.billed_quantity),
                total_price=li.billed_total,
            )
        )
        for allowance in li.allowances:
            lines.append(_format_line_allowance_or_charge(allowance))
        for charge in li.charges:
            lines.append(_format_line_allowance_or_charge(charge))
        if li.basis_quantity:
            lines.append(
                _("  Basis Quantity: {}").format(
                    format_quantity(li.basis_quantity)
                )
            )
        if li.tax_rate is not None:
            lines.append(
                _("  VAT: {tax_rate}\u2009% ({tax_category})").format(
                    tax_rate=li.tax_rate, tax_category=li.tax_category
                )
            )
        lines.append(indent(li.name, "  "))
        if li.global_id:
            lines.append(
                "  {global_id}".format(
                    global_id=_format_global_id(li.global_id)
                )
            )

    return "\n".join(lines)


def _format_line_allowance_or_charge(
    allowance: LineAllowance | LineCharge,
) -> str:
    lines = []
    type = (
        _("Surcharge") if isinstance(allowance, LineCharge) else _("Deduction")
    )
    lines.append(
        _("  {type}: {basis} {percent:>4}\u2009% {amount}").format(
            type=type,
            basis=allowance.basis_amount,
            percent=allowance.percent or "",
            amount=allowance.actual_amount or "",
        )
    )
    if allowance.reason and allowance.reason_code:
        lines.append(
            _("  Reason: {reason} ({code})").format(
                reason=allowance.reason, code=allowance.reason_code.name
            )
        )
    elif allowance.reason:
        lines.append(_("  Reason: {reason}").format(reason=allowance.reason))
    elif allowance.reason_code:
        lines.append(
            _("  Reason: {code}").format(code=allowance.reason_code.name)
        )
    return "\n".join(lines)


def _format_allowances_and_charges(
    allowances: Sequence[DocumentAllowance | DocumentCharge],
) -> str:
    basis_len = max(
        (
            len(str(a.basis_amount))
            for a in allowances
            if a.basis_amount is not None
        ),
        default=0,
    )
    amount_len = max(
        (
            len(str(a.actual_amount))
            for a in allowances
            if a.actual_amount is not None
        ),
        default=0,
    )
    basis_s = _("Basis").center(basis_len)
    amount_s = _("Amount").center(amount_len)
    lines = [
        _("{basis} |   %    |   Tax    | {amount}").format(
            basis=basis_s, amount=amount_s
        )
    ]
    for a in allowances:
        basis_s = str(a.basis_amount).rjust(basis_len)
        amount_s = str(a.actual_amount).rjust(amount_len)
        lines.append(
            _(
                "{basis} | {percent:>4}\u2009% |"
                " {tax_rate}\u2009% ({tax_category}) | {amount}"
            ).format(
                basis=basis_s,
                percent=a.percent,
                tax_rate=a.tax_rate,
                tax_category=a.tax_category.name,
                amount=amount_s,
            )
        )
        if a.reason and a.reason_code:
            lines.append(
                _("  Reason: {reason} ({code})").format(
                    reason=a.reason, code=a.reason_code.name
                )
            )
        elif a.reason:
            lines.append(_("  Reason: {reason}").format(reason=a.reason))
        elif a.reason_code:
            lines.append(_("  Reason: {code}").format(code=a.reason_code.name))
    return "\n".join(lines)


def _format_tax(invoice: BasicWLInvoice) -> str:
    lines = []

    if isinstance(invoice, EN16931Invoice) and invoice.tax_currency_code:
        lines += [_("Tax Currency: {}").format(invoice.tax_currency_code), ""]

    basis_len = max(
        (len(str(tax.basis_amount)) for tax in invoice.tax), default=0
    )
    tax_len = max(
        (len(str(tax.calculated_amount)) for tax in invoice.tax), default=0
    )
    net_s = _("Net").center(basis_len)
    tax_s = _("Tax").center(tax_len)
    lines.append(
        _("Cat | Rate | {net} | {tax}").format(net=net_s, tax=tax_s),
    )
    for tax in invoice.tax:
        basis_s = str(tax.basis_amount).rjust(basis_len)
        tax_s = str(tax.calculated_amount).rjust(tax_len)
        lines.append(
            _("{category:>2}  | {rate:>2}\u2009% | {basis} | {tax}").format(
                category=tax.category_code,
                rate=tax.rate_percent,
                basis=basis_s,
                tax=tax_s,
            )
        )

        exemption = ""
        if tax.exemption_reason and tax.exemption_reason_code:
            exemption += _("  Exemption Reason: {reason} ({code})").format(
                reason=tax.exemption_reason,
                code=tax.exemption_reason_code.name,
            )
        elif tax.exemption_reason:
            exemption += _("  Exemption Reason: {reason}").format(
                reason=tax.exemption_reason
            )
        elif tax.exemption_reason_code:
            exemption += _("  Exemption Reason: {code}").format(
                code=tax.exemption_reason_code.name
            )
        if exemption:
            lines.append(exemption)

        due_date = ""
        if tax.tax_point_date and tax.due_date_type_code:
            time_code = _(PAYMENT_TIME_CODE_NAMES[tax.due_date_type_code])
            due_date += _(
                "  Tax Point Date: {date:%Y-%m-%d} ({time_code})"
            ).format(
                date=tax.tax_point_date,
                time_code=time_code,
            )
        elif tax.tax_point_date:
            due_date += _("  Tax Point Date: {date:%Y-%m-%d}").format(
                date=tax.tax_point_date
            )
        elif tax.due_date_type_code:
            time_code = _(PAYMENT_TIME_CODE_NAMES[tax.due_date_type_code])
            due_date += _("  Due Date Type: {time_code}").format(
                time_code=time_code
            )
        if due_date:
            lines.append(due_date)

    return "\n".join(lines)


def _format_totals(invoice: MinimumInvoice) -> str:
    lines = []
    if invoice.line_total_amount:
        lines.append(
            _("Line Total (net): {}").format(invoice.line_total_amount)
        )
    if isinstance(invoice, BasicWLInvoice):
        if invoice.charge_total_amount:
            lines.append(
                _("Surcharges: {}").format(invoice.charge_total_amount)
            )
        if invoice.allowance_total_amount:
            lines.append(
                _("Deductions: {}").format(invoice.allowance_total_amount)
            )
    lines.append(_("Net: {}").format(invoice.tax_basis_total_amount))
    for tax_amount in invoice.tax_total_amounts:
        lines.append(_("VAT: {}").format(tax_amount))
    lines.append(_("Gross: {}").format(invoice.grand_total_amount))
    if isinstance(invoice, BasicWLInvoice) and invoice.prepaid_amount:
        lines.append(_("Prepaid: {}").format(invoice.prepaid_amount))
    if isinstance(invoice, EN16931Invoice) and invoice.rounding_amount:
        lines.append(_("Rounding amount: {}").format(invoice.rounding_amount))
    lines.append(_("Amount payable: {}").format(invoice.due_payable_amount))
    return "\n".join(lines)


def _format_payment(invoice: BasicWLInvoice) -> str:
    lines = []
    if invoice.payee:
        lines += [
            _header(_("Payee")),
            format_trade_party(invoice.payee),
        ]
    if (
        invoice.payment_means
        or invoice.sepa_reference
        or invoice.payment_reference
    ):
        lines.append(_header(_("Payment Means")))
        for means in invoice.payment_means:
            lines.append(format_payment_means(means))
        if invoice.sepa_reference:
            lines.append(
                _("SEPA Reference: {}").format(invoice.sepa_reference)
            )
        if invoice.payment_reference:
            lines.append(
                _("Payment Reference: {}").format(invoice.payment_reference)
            )
    if invoice.payment_terms:
        lines += [
            _header(_("Payment Terms")),
            format_payment_terms(invoice.payment_terms),
        ]
    return "\n".join(lines)


def format_quantity(quantity: Quantity | OptionalQuantity) -> str:
    if quantity[1] is None:
        return str(quantity[0])

    qn = QUANTITY_NAMES[quantity[1]]
    if isinstance(qn, tuple):
        q = quantity[0].as_integer_ratio()
        if q[1] == 1:  # if unit is an integer
            unit = ngettext(*qn, q[0])
        else:
            unit = _(qn[1])  # plural
    else:
        unit = qn
    return _("{quantity} {unit}").format(quantity=quantity[0], unit=unit)


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


def format_note(note: IncludedNote) -> str:
    if note.subject_code:
        code = _(TEXT_SUBJECT_CODE_NAMES[note.subject_code])
        return _("{subject_code}: {content}").format(
            subject_code=code, content=note.content.strip()
        )
    else:
        return note.content.strip()


def format_payment_means(payment_means: PaymentMeans) -> str:
    lines = []
    lines.append(
        _("Payment Means: {}").format(
            _(PAYMENT_MEANS_NAMES[payment_means.type_code])
        )
    )
    if payment_means.payee_account:
        lines.append(format_bank_account(payment_means.payee_account))
    if payment_means.payee_bic:
        lines.append(_("BIC: {}").format(payment_means.payee_bic))
    if payment_means.card:
        pan, cardholder = payment_means.card
        if cardholder:
            lines.append(_("Credit card: {} ({})").format(pan, cardholder))
        else:
            lines.append(_("Credit card: {}").format(pan))
    if payment_means.payer_iban:
        lines.append(_("Payer IBAN: {}").format(payment_means.payer_iban))
    if payment_means.information:
        lines.append(payment_means.information)
    return "\n".join(lines)


def format_bank_account(account: BankAccount) -> str:
    lines = []
    if account.iban:
        lines.append(_("IBAN: {}").format(account.iban))
    if account.name:
        lines.append(_("Account owner: {}").format(account.name))
    if account.bank_id:
        lines.append(_("Bank: {}").format(account.bank_id))
    return "\n".join(lines)


def format_payment_terms(terms: PaymentTerms) -> str:
    lines = []
    if terms.due_date:
        lines.append(
            _("Due Date: {due_date:%Y-%m-%d}").format(due_date=terms.due_date)
        )
    if terms.direct_debit_mandate_id:
        lines.append(
            _("Direct Debit Mandate ID: {}").format(
                terms.direct_debit_mandate_id
            )
        )
    description = terms.description.strip() if terms.description else ""
    if description:
        lines.append(description)
    return "\n".join(lines)


def format_reference_doc(doc: ReferenceDocument) -> str:
    lines = []
    type_name = _(DOCUMENT_TYPE_NAMES[doc.type_code])
    lines.append("{type} {doc.id}".format(type=type_name, doc=doc))
    if doc.reference_type_code is not None:
        lines.append(
            _("  Reference Qualifier: {}").format(
                REFERENCE_QUALIFIER_NAMES[doc.reference_type_code]
            )
        )
    if doc.name is not None:
        lines.append(_("  Name: {}").format(doc.name))
    if doc.url is not None:
        lines.append(_("  URL: {}").format(doc.url))
    if doc.attachment is not None:
        __, mime_type, filename = doc.attachment
        lines.append(
            _("  Attachment: {filename} ({mime_type})").format(
                filename=filename, mime_type=mime_type
            )
        )

    return "\n".join(lines)


def _format_global_id(global_id: ID) -> str:
    id, code = global_id
    if code is None:
        return _("Global ID: {}").format(id)
    if isinstance(code, IdentifierSchemeCode):
        code = code.name
    return _("{id_type}: {id}").format(id_type=code, id=id)


def _header(header: str) -> str:
    return f"\n{header}\n{'-' * len(header)}\n"


if __name__ == "__main__":
    # Print a sample invoice

    import locale

    from .test_data import en16931_einfach

    locale.setlocale(locale.LC_ALL, "")

    invoice = en16931_einfach()
    print(format_invoice_as_text(invoice))
