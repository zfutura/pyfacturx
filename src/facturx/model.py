from __future__ import annotations

import datetime
from collections.abc import Sequence
from dataclasses import KW_ONLY, dataclass, field
from decimal import Decimal
from types import NoneType
from typing import ClassVar

from .const import (
    URN_BASIC_PROFILE,
    URN_BASIC_WL_PROFILE,
    URN_EN16931_PROFILE,
    URN_MINIMUM_PROFILE,
)
from .countries import validate_iso_3166_1_alpha_2
from .type_codes import (
    AllowanceChargeCode,
    DocumentTypeCode,
    ItemTypeCode,
    PaymentMeansCode,
    PaymentTimeCode,
    ReferenceQualifierCode,
    SpecialServiceCode,
    TaxCategoryCode,
    TextSubjectCode,
    VATExemptionCode,
)
from .types import ID, Attachment, DocRef, Money, Quantity

__all__ = [
    "MinimumInvoice",
    "BasicWLInvoice",
    "BasicInvoice",
    "EN16931Invoice",
    "LineItem",
    "EN16931LineItem",
    "PostalAddress",
    "ReferenceDocument",
    "Tax",
    "TradeContact",
    "TradeParty",
    "LineAllowanceCharge",
    "DocumentAllowanceCharge",
    "ProductCharacteristic",
    "ProductClassification",
    "PaymentMeans",
    "PaymentTerms",
    "BankAccount",
    "IncludedNote",
]


@dataclass
class IncludedNote:
    """A note included in an invoice."""

    content: str
    subject_code: TextSubjectCode | None = None


@dataclass
class TradeParty:
    """
    Trade party data used in invoices for seller, buyer, and other parties.

    The required fields depend on the invoice profile and the role of the
    party.
    """

    name: str | None
    address: PostalAddress | None  # Not required in MINIMUM for the buyer
    email: str | None = None
    _: KW_ONLY
    tax_number: str | None = None
    vat_id: str | None = None
    ids: Sequence[str] = field(default_factory=list)
    global_ids: Sequence[ID] = field(default_factory=list)
    description: str | None = None
    legal_id: ID | None = None
    trading_business_name: str | None = None
    contacts: Sequence[TradeContact] = field(default_factory=list)

    def validate_minimum(self, *, buyer: bool) -> None:
        """Validate the MINIMUM profile requirements."""

        if buyer:
            if self.tax_number is not None:
                raise ValueError(
                    "Buyer tax number is not allowed in the MINIMUM profile."
                )
            if self.vat_id is not None:
                raise ValueError(
                    "Buyer VAT ID is not allowed in the MINIMUM profile."
                )
        if self.email is not None:
            raise ValueError(
                "Seller email is not allowed in the MINIMUM profile."
            )
        if len(self.ids) > 0:
            raise ValueError(
                "Seller IDs are not allowed in the MINIMUM profile."
            )
        if len(self.global_ids) > 0:
            raise ValueError(
                "Seller global IDs are not allowed in the MINIMUM profile."
            )
        if self.trading_business_name is not None:
            raise ValueError(
                "Seller trading business name is not allowed "
                "in the MINIMUM profile."
            )
        if self.address is not None:
            self.address.validate_minimum()

    def validate_tax_representative(self) -> None:
        """Validate the requirements for a seller tax representative."""

        if self.name is None:
            raise ValueError("Seller tax representative name is required.")
        if len(self.ids) > 0:
            raise ValueError(
                "Seller tax representative IDs are not allowed in BASIC WL "
                "profile."
            )
        if len(self.global_ids) > 0:
            raise ValueError(
                "Seller tax representative global IDs are not allowed in "
                "BASIC WL profile."
            )
        if self.legal_id is not None:
            raise ValueError(
                "Seller tax representative legal ID is not allowed in BASIC "
                "WL profile."
            )
        if self.trading_business_name is not None:
            raise ValueError(
                "Seller tax representative trading business name is not "
                "allowed in BASIC WL profile."
            )
        if len(self.contacts) > 0:
            raise ValueError(
                "Seller tax representative contacts are not allowed in BASIC "
                "WL profile."
            )
        if self.address is None:
            raise ValueError(
                "Seller tax representative address is required in BASIC WL "
                "profile."
            )
        if self.email is not None:
            raise ValueError(
                "Seller tax representative email is not allowed in BASIC WL "
                "profile."
            )
        if self.tax_number is not None:
            raise ValueError(
                "Seller tax representative tax number is not allowed in BASIC "
                "WL profile."
            )
        if self.vat_id is None:
            raise ValueError(
                "Seller tax representative VAT ID is required in BASIC WL "
                "profile."
            )

    def validate_ship_to(self) -> None:
        """Validate the requirements for a ship-to party."""

        if len(self.ids) > 1:
            raise ValueError(
                "Multiple ship-to IDs are not allowed in BASIC WL profile."
            )
        if len(self.global_ids) > 1:
            raise ValueError(
                "Multiple ship-to global IDs are not allowed in BASIC WL "
                "profile."
            )
        if self.legal_id is not None:
            raise ValueError(
                "Ship-to legal ID is not allowed in BASIC WL profile."
            )
        if self.trading_business_name is not None:
            raise ValueError(
                "Ship-to trading business name is not allowed in BASIC WL "
                "profile."
            )
        if len(self.contacts) > 0:
            raise ValueError(
                "Ship-to contacts are not allowed in BASIC WL profile."
            )
        if self.email is not None:
            raise ValueError(
                "Ship-to email is not allowed in BASIC WL profile."
            )
        if self.tax_number is not None:
            raise ValueError(
                "Ship-to tax number is not allowed in BASIC WL profile."
            )
        if self.vat_id is not None:
            raise ValueError(
                "Ship-to VAT ID is not allowed in BASIC WL profile."
            )

    def validate_payee(self) -> None:
        """Validate the requirements for a payee party."""

        if len(self.ids) > 0:
            raise ValueError(
                "Multiple payee IDs are not allowed in BASIC WL profile."
            )
        if len(self.global_ids) > 0:
            raise ValueError(
                "Multiple payee global IDs are not allowed in "
                "BASIC WL profile."
            )
        if self.trading_business_name is not None:
            raise ValueError(
                "Payee trading business name is not allowed in BASIC WL "
                "profile."
            )
        if len(self.contacts) > 0:
            raise ValueError(
                "Payee contacts are not allowed in BASIC WL profile."
            )
        if self.address is not None:
            raise ValueError(
                "Payee address is not allowed in BASIC WL profile."
            )
        if self.email is not None:
            raise ValueError("Payee email is not allowed in BASIC WL profile.")
        if self.tax_number is not None:
            raise ValueError(
                "Payee tax number is not allowed in BASIC WL profile."
            )
        if self.vat_id is not None:
            raise ValueError(
                "Payee VAT ID is not allowed in BASIC WL profile."
            )


@dataclass
class TradeContact:
    """Contact information for a trade party."""

    person_name: str | None = None
    department_name: str | None = None
    _: KW_ONLY
    phone: str | None = None
    email: str | None = None


@dataclass
class PostalAddress:
    """Postal address used in invoices."""

    country_code: str  # ISO 3166-1 alpha-2
    country_subdivision: str | None = None
    post_code: str | None = None
    city: str | None = None
    line_one: str | None = None
    line_two: str | None = None
    line_three: str | None = None

    def __post_init__(self) -> None:
        if not validate_iso_3166_1_alpha_2(self.country_code):
            raise ValueError("Invalid ISO 3166-1 alpha-2 country code.")

    def validate_minimum(self) -> None:
        """Validate the MINIMUM profile requirements."""
        if (
            self.country_subdivision is not None
            or self.post_code is not None
            or self.city is not None
            or self.line_one is not None
            or self.line_two is not None
            or self.line_three is not None
        ):
            raise ValueError(
                "Address fields are not allowed in the MINIMUM profile."
            )


@dataclass
class MinimumInvoice:
    """Invoice data for the MINIMUM profile."""

    PROFILE_URN: ClassVar[str] = URN_MINIMUM_PROFILE

    invoice_number: str
    type_code: DocumentTypeCode
    invoice_date: datetime.date
    seller: TradeParty
    buyer: TradeParty
    currency_code: str
    line_total_amount: Money | None
    tax_basis_total_amount: Money
    tax_total_amount: Money
    grand_total_amount: Money
    due_payable_amount: Money

    _: KW_ONLY

    business_doc_ctx_uri: str | None = None
    buyer_reference: str | None = None
    buyer_order_ref_doc_id: str | None = None

    def __post_init__(self) -> None:
        if not self.type_code.is_invoice_type:
            raise ValueError(f"Invalid invoice type code: {self.type_code}.")
        if self.seller.address is None:
            raise ValueError("Seller address is required in MINIMUM profile.")
        if type(self) is MinimumInvoice:
            self.seller.validate_minimum(buyer=False)
            self.buyer.validate_minimum(buyer=True)
        if self.seller.name is None:
            raise ValueError("Seller name is required.")
        if self.buyer.name is None:
            raise ValueError("Buyer name is required.")
        if self.buyer.description is not None:
            raise ValueError("Buyer description is not allowed.")
        if not isinstance(self, EN16931Invoice):
            if self.seller.description is not None:
                raise ValueError(
                    "Seller description is not allowed in this profile."
                )
            if len(self.seller.contacts) > 0:
                raise ValueError(
                    "Seller contacts are not allowed in this profile."
                )
            if len(self.buyer.contacts) > 0:
                raise ValueError(
                    "Buyer contacts are not allowed in this profile."
                )
            if self.buyer.trading_business_name is not None:
                raise ValueError(
                    "Buyer trading business name is not allowed "
                    "in this profile."
                )


@dataclass
class BasicWLInvoice(MinimumInvoice):
    """Invoice data for the BASIC WL profile."""

    PROFILE_URN = URN_BASIC_WL_PROFILE

    tax: Sequence[Tax]

    _: KW_ONLY

    charge_total_amount: Money | None = None
    allowance_total_amount: Money | None = None
    prepaid_amount: Money | None = None
    payee: TradeParty | None = None
    delivery_date: datetime.date | None = None
    billing_period: tuple[datetime.date, datetime.date] | None = None
    specified_allowance_charges: Sequence[DocumentAllowanceCharge] = field(
        default_factory=list
    )
    doc_notes: list[IncludedNote] = field(default_factory=list)
    seller_tax_representative: TradeParty | None = None
    contract_referenced_doc_id: str | None = None
    ship_to: TradeParty | None = None
    despatch_advice_ref_doc_id: str | None = None
    receiving_advice_ref_doc_id: str | None = None
    sepa_reference: str | None = None
    payment_reference: str | None = None
    payment_means: Sequence[PaymentMeans] = field(default_factory=list)
    payment_terms: PaymentTerms | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.line_total_amount is None:
            raise ValueError(
                "Line total amount is required in BASIC WL profile."
            )
        if len(self.tax) < 1:
            raise ValueError("At least one tax entry is required.")
        if self.payee is not None:
            self.payee.validate_payee()
        if len(self.buyer.global_ids) > 1:
            raise ValueError(
                "Only one buyer global ID is allowed in BASIC WL profile."
            )
        if self.seller_tax_representative is not None:
            self.seller_tax_representative.validate_tax_representative()
        if self.buyer.address is None:
            raise ValueError("Buyer address is required in BASIC WL profile.")
        if self.ship_to is not None:
            self.ship_to.validate_ship_to()
        if not isinstance(self, EN16931Invoice):
            for means in self.payment_means:
                means.verify_basic()
            if self.payment_terms is not None:
                self.payment_terms.verify_basic()


@dataclass
class BasicInvoice(BasicWLInvoice):
    """Invoice data for the BASIC profile."""

    PROFILE_URN = URN_BASIC_PROFILE

    _: KW_ONLY

    line_items: Sequence[LineItem]  # BG-25

    def __post_init__(self) -> None:
        if len(self.line_items) < 1:
            raise ValueError("At least one line item is required.")
        if type(self) is BasicInvoice:
            for li in self.line_items:
                if isinstance(li, EN16931LineItem):
                    raise TypeError(
                        "EN 16931/COMFORT line items are not allowed in the "
                        "BASIC profile."
                    )
                for allowance in li.specified_allowance_charges:
                    allowance.validate_basic()


@dataclass
class EN16931Invoice(BasicInvoice):
    """Invoice data for the EN 16931/COMFORT profile."""

    PROFILE_URN = URN_EN16931_PROFILE

    _: KW_ONLY

    rounding_amount: Money | None = None
    seller_order_ref_doc_id: str | None = None
    referenced_docs: Sequence[ReferenceDocument] = field(default_factory=list)
    procuring_project: tuple[str, str] | None = None
    tax_currency_code: str | None = None
    trade_account_id: str | None = None
    ref_doc: DocRef | None = None


@dataclass
class LineItem:
    """Line item data used in the BASIC profile."""

    name: str
    net_price: Money
    billed_quantity: Quantity
    billed_total: Money
    tax_rate: Decimal
    tax_category: TaxCategoryCode = TaxCategoryCode.STANDARD_RATE
    global_id: ID | None = None

    _: KW_ONLY
    basis_quantity: Quantity | None = None
    specified_allowance_charges: Sequence[LineAllowanceCharge] = field(
        default_factory=list
    )


@dataclass
class EN16931LineItem(LineItem):
    """Line item data used in the EN 16931/COMFORT profile."""

    _: KW_ONLY
    description: str | None = None
    note: IncludedNote | None = None
    # (Unit price, optional basis quantity)
    gross_unit_price: tuple[Decimal, Quantity | None] | None = None
    applied_allowance_charge: LineAllowanceCharge | None = None
    seller_assigned_id: str | None = None
    buyer_assigned_id: str | None = None
    product_characteristics: Sequence[ProductCharacteristic] = field(
        default_factory=list
    )
    product_classifications: Sequence[ProductClassification] = field(
        default_factory=list
    )
    origin_country: str | None = None
    buyer_order_ref_doc_id: str | None = None
    billing_period: tuple[datetime.date, datetime.date] | None = None
    ref_docs: Sequence[DocRef] = field(default_factory=list)
    trade_account_id: str | None = None

    def __post_init__(self) -> None:
        if self.note is not None and self.note.subject_code is not None:
            raise ValueError(
                "Line item note subject codes are not allowed in the "
                "EN 16931/COMFORT profile."
            )
        if (
            self.applied_allowance_charge is not None
            and self.gross_unit_price is None
        ):
            raise ValueError(
                "Allowance/charge requires a gross unit price in the "
                "EN 16931/COMFORT profile."
            )
        if self.origin_country is not None:
            if not validate_iso_3166_1_alpha_2(self.origin_country):
                raise ValueError("Invalid ISO 3166-1 alpha-2 country code.")
        if self.billing_period is not None:
            start, end = self.billing_period
            if start > end:
                raise ValueError(
                    "Billing period start date must be before end date."
                )


@dataclass
class ProductCharacteristic:
    """A single product characteristic."""

    description: str
    value: str


@dataclass
class ProductClassification:
    """A single product classification."""

    class_code: str
    _: KW_ONLY
    list_id: ItemTypeCode | None = None
    list_version_id: str | None = None


@dataclass
class LineAllowanceCharge:
    """An allowance or charge for a line item."""

    actual_amount: Money
    surcharge: bool = False
    reason_code: AllowanceChargeCode | SpecialServiceCode | None = None
    reason: str | None = None
    _: KW_ONLY
    percent: Decimal | None = None
    basis_amount: Money | None = None

    def __post_init__(self) -> None:
        if self.surcharge:
            if not isinstance(
                self.reason_code, (SpecialServiceCode, NoneType)
            ):
                raise ValueError(
                    "Surcharge requires a special service reason code."
                )
        else:
            if not isinstance(
                self.reason_code, (AllowanceChargeCode, NoneType)
            ):
                raise ValueError("Allowance/charge requires a reason code.")

    def validate_basic(self) -> None:
        """Validate the requirements for the BASIC profile."""
        if self.percent is not None:
            raise ValueError(
                "Percentage-based allowances/charges are not allowed in the "
                "BASIC profile."
            )
        if self.basis_amount is not None:
            raise ValueError(
                "Basis amount-based allowances/charges are not allowed in the "
                "BASIC profile."
            )


@dataclass
class DocumentAllowanceCharge(LineAllowanceCharge):
    """An allowance or charge for the entire invoice."""

    _: KW_ONLY
    tax_category: TaxCategoryCode = TaxCategoryCode.STANDARD_RATE
    tax_rate: Decimal | None = None


@dataclass
class ReferenceDocument:
    """A reference document attached to an invoice."""

    id: str
    type_code: DocumentTypeCode
    name: str | None = None
    url: str | None = None
    attachment: Attachment | None = None
    _: KW_ONLY
    reference_type_code: ReferenceQualifierCode | None = None

    def __post_init__(self) -> None:
        if not self.type_code.is_supporting_document_type:
            raise ValueError(
                f"Invalid reference document type code: {self.type_code}."
            )


@dataclass
class PaymentMeans:
    """Payment means data used in invoices."""

    type_code: PaymentMeansCode
    payee_account: BankAccount | None = None
    payee_bic: str | None = None
    information: str | None = None
    _: KW_ONLY
    # (account number (PAN), cardholder name)
    card: tuple[str, str | None] | None = None
    payer_iban: str | None = None

    def verify_basic(self) -> None:
        if self.information is not None:
            raise ValueError(
                "Payment means information is not allowed in the "
                "BASIC profile."
            )
        if self.card is not None:
            raise ValueError(
                "Payment means card information is not allowed in the "
                "BASIC profile."
            )
        if (
            self.payee_account is not None
            and self.payee_account.name is not None
        ):
            raise ValueError(
                "Payment means account name is not allowed in the BASIC "
                "profile."
            )
        if self.payee_bic is not None:
            raise ValueError(
                "Payment means BIC is not allowed in the BASIC profile."
            )


@dataclass
class PaymentTerms:
    """Payment terms data used in invoices."""

    _: KW_ONLY
    description: str | None = None
    due_date: datetime.date | None = None
    direct_debit_mandate_id: str | None = None

    def verify_basic(self) -> None:
        if self.description is not None:
            raise ValueError(
                "Payment terms description is not allowed in the "
                "BASIC profile."
            )


@dataclass
class BankAccount:
    """Bank account data used in invoices."""

    iban: str | None
    name: str | None
    bank_id: str | None


@dataclass
class Tax:
    """A single tax entry for an invoice."""

    calculated_amount: Money
    basis_amount: Money
    rate_percent: Decimal
    category_code: TaxCategoryCode = TaxCategoryCode.STANDARD_RATE
    _: KW_ONLY
    exemption_reason: str | None = None
    exemption_reason_code: VATExemptionCode | None = None
    tax_point_date: datetime.date | None = None
    due_date_type_code: PaymentTimeCode | None = None

    def __post_init__(self) -> None:
        if (
            self.due_date_type_code is not None
            and not self.due_date_type_code.is_invoice_due_date
        ):
            raise ValueError(
                "Invalid due date type code: {self.due_date_type_code}."
            )

    def validate_basic(self) -> None:
        """Validate the requirements for the BASIC profile."""
        if self.tax_point_date is not None:
            raise ValueError(
                "Tax point date is not allowed in the BASIC profile."
            )
