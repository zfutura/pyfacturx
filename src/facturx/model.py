from __future__ import annotations

import datetime
from collections.abc import Sequence
from dataclasses import KW_ONLY, dataclass, field
from decimal import Decimal
from typing import ClassVar, Literal

from .const import (
    URN_BASIC_PROFILE,
    URN_BASIC_WL_PROFILE,
    URN_EN16931_PROFILE,
    URN_MINIMUM_PROFILE,
)
from .countries import validate_iso_3166_1_alpha_2
from .exc import ModelError
from .money import Money, validate_iso_4217_currency
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
from .types import ID, Attachment, DocRef, OptionalQuantity, Quantity

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
    "LineAllowance",
    "LineCharge",
    "DocumentAllowance",
    "DocumentCharge",
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

    def validate(
        self,
        profile: type[MinimumInvoice],
        *,
        which: Literal[
            "seller", "buyer", "seller tax representative", "ship to", "payee"
        ],
    ) -> None:
        """Validate the requirements for the given profile."""

        if which in ("seller tax representative", "ship to", "payee"):
            if not issubclass(profile, BasicWLInvoice):
                raise ModelError(
                    f"{which.capitalize} is not allowed in the "
                    f"{profile.PROFILE_NAME} profile."
                )

        # ids and global_ids

        for gid in self.global_ids:
            if gid[1] is None:
                raise ModelError("Global ID scheme ID is required.")

        if which in ("buyer", "ship to", "payee"):
            if issubclass(profile, BasicWLInvoice):
                if len(self.ids) > 1:
                    raise ModelError(
                        f"Multiple {which} IDs are not allowed in the "
                        f"{profile.PROFILE_NAME} profile."
                    )
                if len(self.global_ids) > 1:
                    raise ModelError(
                        f"Multiple {which} global IDs are not allowed in the "
                        f"{profile.PROFILE_NAME} profile."
                    )
            else:  # only relevant for "buyer"
                if len(self.ids) > 0:
                    raise ModelError(
                        f"{which.capitalize()} IDs are not allowed in the "
                        f"{profile.PROFILE_NAME} profile."
                    )
                if len(self.global_ids) > 0:
                    raise ModelError(
                        f"{which.capitalize()} global IDs are not allowed "
                        f"in the {profile.PROFILE_NAME} profile."
                    )

        elif which == "seller":
            if not issubclass(profile, BasicWLInvoice):
                if len(self.ids) > 0:
                    raise ModelError(
                        "Seller IDs are not allowed in the "
                        f"{profile.PROFILE_NAME} profile."
                    )
                if len(self.global_ids) > 0:
                    raise ModelError(
                        "Seller global IDs are not allowed in the "
                        f"{profile.PROFILE_NAME} profile."
                    )
        elif which == "seller tax representative":
            if len(self.ids) > 0:
                raise ModelError(
                    "Seller tax representative IDs are not allowed in the "
                    f"{profile.PROFILE_NAME} profile."
                )
            if len(self.global_ids) > 0:
                raise ModelError(
                    "Seller tax representative global IDs are not allowed "
                    f"in the {profile.PROFILE_NAME} profile."
                )

        # name

        # Optional for ship to party only.
        if which != "ship to" and self.name is None:
            raise ModelError(f"{which.capitalize()} name is required.")

        # description

        # Allowed only for seller in EN 16931/COMFORT.
        if which != "seller" or not issubclass(profile, EN16931Invoice):
            if self.description is not None:
                raise ModelError(
                    f"{which.capitalize()} description is not allowed."
                )

        # legal organization ID

        # Not allowed for seller tax representative and ship to party.
        if which in ("seller tax representative", "ship to"):
            if self.legal_id is not None:
                raise ModelError(
                    f"{which.capitalize()} legal ID is not allowed "
                    f"in the {profile.PROFILE_NAME} profile."
                )

        # legal organization trading business name

        # Allowed for buyer in EN 16931/COMFORT and for seller in BASIC WL.
        if which == "buyer":
            if not issubclass(profile, EN16931Invoice):
                if self.trading_business_name is not None:
                    raise ModelError(
                        "Buyer trading business name is not allowed "
                        f"in the {profile.PROFILE_NAME} profile."
                    )
        elif which == "seller":
            if not issubclass(profile, BasicWLInvoice):
                if self.trading_business_name is not None:
                    raise ModelError(
                        "Seller trading business name is not allowed in the "
                        f"{profile.PROFILE_NAME} profile."
                    )
        else:
            if self.trading_business_name is not None:
                raise ModelError(
                    f"{which.capitalize()} trading business name is not "
                    f"allowed in the {profile.PROFILE_NAME} profile."
                )

        # contacts

        # Only allowed for buyer and seller in EN 16931/COMFORT.
        if which not in ("buyer", "seller") or not issubclass(
            profile, EN16931Invoice
        ):
            if len(self.contacts) > 0:
                raise ModelError(
                    f"{which.capitalize()} contacts are not allowed "
                    f"in the {profile.PROFILE_NAME} profile."
                )

        # address

        # Not allowed for payee.
        # Required for seller, seller tax representative in all profiles,
        # and buyer in BASIC WL.
        # Optional for buyer in MINIMUM and for ship to party.
        if which == "payee":
            if self.address is not None:
                raise ModelError(
                    "Payee address is not allowed in the "
                    f"{profile.PROFILE_NAME} profile."
                )
        elif which in ("seller", "seller tax representative") or (
            which == "buyer" and issubclass(profile, BasicWLInvoice)
        ):
            if self.address is None:
                raise ModelError(
                    f"{which.capitalize()} address is required in the "
                    f"{profile.PROFILE_NAME} profile."
                )

        if self.address is not None:
            self.address.validate(profile)

        # email

        # Not allowed in MINIMUM.
        if not issubclass(profile, BasicWLInvoice):
            if self.email is not None:
                raise ModelError(
                    f"{which.capitalize()} email is not allowed in the "
                    f"{profile.PROFILE_NAME} profile."
                )

        # tax number

        # Not allowed for buyer in MINIMUM and other parties.
        # Optional buyer in BASIC WL and seller.
        if (
            which == "buyer" and not issubclass(profile, BasicWLInvoice)
        ) or which in ("seller tax representative", "ship to", "payee"):
            if self.tax_number is not None:
                raise ModelError(
                    f"{which.capitalize()} tax number is not allowed in the "
                    f"{profile.PROFILE_NAME} profile."
                )

        # VAT ID

        # Required for seller tax representative.
        # Not allowed for buyer in MINIMUM and other parties.
        # Optional for buyer in BASIC WL and seller.
        if which == "seller tax representative":
            if self.vat_id is None:
                raise ModelError(
                    "Seller tax representative VAT ID is required in the "
                    f"{profile.PROFILE_NAME} profile."
                )
        elif (
            which == "buyer"
            and not issubclass(profile, BasicWLInvoice)
            or which in ("ship to", "payee")
        ):
            if self.vat_id is not None:
                raise ModelError(
                    f"{which.capitalize()} VAT ID is not allowed in the "
                    f"{profile.PROFILE_NAME} profile."
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
            raise ModelError("Invalid ISO 3166-1 alpha-2 country code.")

    def validate(self, profile: type[MinimumInvoice]) -> None:
        """Validate the requirements for the given profile."""
        if not issubclass(profile, BasicWLInvoice):
            if (
                self.country_subdivision is not None
                or self.post_code is not None
                or self.city is not None
                or self.line_one is not None
                or self.line_two is not None
                or self.line_three is not None
            ):
                raise ModelError(
                    "Address fields are not allowed in the "
                    f"{profile.PROFILE_NAME} profile."
                )


@dataclass
class MinimumInvoice:
    """Invoice data for the MINIMUM profile."""

    PROFILE_NAME: ClassVar[str] = "MINIMUM"
    PROFILE_URN: ClassVar[str] = URN_MINIMUM_PROFILE

    invoice_number: str
    type_code: DocumentTypeCode
    invoice_date: datetime.date
    seller: TradeParty
    buyer: TradeParty
    currency_code: str

    _: KW_ONLY

    line_total_amount: Money | None = None
    tax_basis_total_amount: Money
    tax_total_amounts: list[Money]
    grand_total_amount: Money
    due_payable_amount: Money

    business_process_id: str | None = None
    buyer_reference: str | None = None
    buyer_order_id: str | None = None

    def __post_init__(self) -> None:
        if not self.type_code.is_invoice_type:
            raise ModelError(f"Invalid invoice type code: {self.type_code}.")
        self.seller.validate(type(self), which="seller")
        self.buyer.validate(type(self), which="buyer")
        validate_iso_4217_currency(self.currency_code)
        if type(self) is MinimumInvoice:
            if len(self.tax_total_amounts) > 1:
                raise ModelError(
                    "Multiple tax total amounts are not allowed in the "
                    "MINIMUM profile."
                )


@dataclass
class BasicWLInvoice(MinimumInvoice):
    """Invoice data for the BASIC WL profile."""

    PROFILE_NAME = "BASIC WL"
    PROFILE_URN = URN_BASIC_WL_PROFILE

    tax: Sequence[Tax]

    _: KW_ONLY

    charge_total_amount: Money | None = None
    allowance_total_amount: Money | None = None
    prepaid_amount: Money | None = None
    payee: TradeParty | None = None
    delivery_date: datetime.date | None = None
    billing_period: tuple[datetime.date, datetime.date] | None = None
    allowances: Sequence[DocumentAllowance] = field(default_factory=list)
    charges: Sequence[DocumentCharge] = field(default_factory=list)
    notes: list[IncludedNote] = field(default_factory=list)
    seller_tax_representative: TradeParty | None = None
    contract_id: str | None = None
    ship_to: TradeParty | None = None
    despatch_advice_id: str | None = None
    sepa_reference: str | None = None
    payment_reference: str | None = None
    payment_means: Sequence[PaymentMeans] = field(default_factory=list)
    payment_terms: PaymentTerms | None = None
    preceding_invoices: list[tuple[str, datetime.date | None]] = field(
        default_factory=list
    )
    receiver_accounting_ids: Sequence[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.line_total_amount is None:
            raise ModelError(
                "Line total amount is required in BASIC WL profile."
            )
        if len(self.tax) < 1:
            raise ModelError("At least one tax entry is required.")
        for tax in self.tax:
            tax.validate(type(self))
        if self.payee is not None:
            self.payee.validate(type(self), which="payee")
        if self.seller_tax_representative is not None:
            self.seller_tax_representative.validate(
                type(self), which="seller tax representative"
            )
        if self.ship_to is not None:
            self.ship_to.validate(type(self), which="ship to")
        for means in self.payment_means:
            means.validate(type(self))
        if self.payment_terms is not None:
            self.payment_terms.validate(type(self))
        if len(self.tax_total_amounts) > 2:
            raise ModelError(
                "Multiple tax total amounts are not allowed in the "
                f"{self.PROFILE_NAME} profile."
            )


@dataclass
class BasicInvoice(BasicWLInvoice):
    """Invoice data for the BASIC profile."""

    PROFILE_NAME = "BASIC"
    PROFILE_URN = URN_BASIC_PROFILE

    _: KW_ONLY

    line_items: Sequence[LineItem]  # BG-25

    def __post_init__(self) -> None:
        if len(self.line_items) < 1:
            raise ModelError("At least one line item is required.")
        if type(self) is BasicInvoice:
            for li in self.line_items:
                if isinstance(li, EN16931LineItem):
                    raise TypeError(
                        "EN 16931/COMFORT line items are not allowed in the "
                        "BASIC profile."
                    )
        for li in self.line_items:
            li.validate(type(self))
        if len(self.receiver_accounting_ids) > 1:
            raise ModelError(
                "Multiple accounting reference IDs are not allowed in the "
                f"{self.PROFILE_NAME} profile."
            )


@dataclass
class EN16931Invoice(BasicInvoice):
    """Invoice data for the EN 16931/COMFORT profile."""

    PROFILE_NAME = "EN 16931/COMFORT"
    PROFILE_URN = URN_EN16931_PROFILE

    _: KW_ONLY

    receiving_advice_id: str | None = None
    rounding_amount: Money | None = None
    seller_order_id: str | None = None
    referenced_docs: Sequence[ReferenceDocument] = field(default_factory=list)
    procuring_project: tuple[str, str] | None = None
    tax_currency_code: str | None = None


@dataclass
class LineItem:
    """Line item data used in the BASIC profile."""

    id: str
    name: str
    net_price: Money
    billed_quantity: Quantity
    billed_total: Money
    tax_rate: Decimal | None
    tax_category: TaxCategoryCode = TaxCategoryCode.STANDARD_RATE
    global_id: ID | None = None

    _: KW_ONLY
    basis_quantity: OptionalQuantity | None = None
    allowances: Sequence[LineAllowance] = field(default_factory=list)
    charges: Sequence[LineCharge] = field(default_factory=list)

    def validate(self, profile: type[BasicInvoice]) -> None:
        """Validate the requirements for the given profile."""
        for allowance in self.allowances:
            allowance.validate(profile)
        for charge in self.charges:
            charge.validate(profile)


@dataclass
class EN16931LineItem(LineItem):
    """Line item data used in the EN 16931/COMFORT profile."""

    _: KW_ONLY
    description: str | None = None
    note: IncludedNote | None = None
    # (Unit price, optional basis quantity)
    gross_unit_price: tuple[Money, OptionalQuantity | None] | None = None
    gross_allowance_or_charge: LineAllowance | LineCharge | None = None
    seller_assigned_id: str | None = None
    buyer_assigned_id: str | None = None
    product_characteristics: Sequence[ProductCharacteristic] = field(
        default_factory=list
    )
    product_classifications: Sequence[ProductClassification] = field(
        default_factory=list
    )
    origin_country: str | None = None
    buyer_order_line_id: str | None = None
    billing_period: tuple[datetime.date, datetime.date] | None = None
    doc_ref: DocRef | None = None
    trade_account_id: str | None = None

    def __post_init__(self) -> None:
        if self.note is not None and self.note.subject_code is not None:
            raise ModelError(
                "Line item note subject codes are not allowed in the "
                "EN 16931/COMFORT profile."
            )
        if (
            self.gross_allowance_or_charge is not None
            and self.gross_unit_price is None
        ):
            raise ModelError(
                "Allowance/charge requires a gross unit price in the "
                "EN 16931/COMFORT profile."
            )
        if self.origin_country is not None:
            if not validate_iso_3166_1_alpha_2(self.origin_country):
                raise ModelError("Invalid ISO 3166-1 alpha-2 country code.")
        if self.billing_period is not None:
            start, end = self.billing_period
            if start > end:
                raise ModelError(
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
class LineAllowance:
    """An allowance for a line item."""

    actual_amount: Money
    reason_code: AllowanceChargeCode | None = None
    reason: str | None = None
    _: KW_ONLY
    percent: Decimal | None = None
    basis_amount: Money | None = None

    def validate(self, profile: type[BasicInvoice]) -> None:
        """Validate the requirements for the given profile."""
        if not issubclass(profile, EN16931Invoice):
            if self.percent is not None:
                raise ModelError(
                    "Percentage-based allowances are not allowed "
                    f"in the {profile.PROFILE_NAME} profile."
                )
            if self.basis_amount is not None:
                raise ModelError(
                    "Basis amount-based allowances are not allowed "
                    f"in the {profile.PROFILE_NAME} profile."
                )


@dataclass
class LineCharge:
    """A surcharge for a line item."""

    actual_amount: Money
    reason_code: SpecialServiceCode | None = None
    reason: str | None = None
    _: KW_ONLY
    percent: Decimal | None = None
    basis_amount: Money | None = None

    def validate(self, profile: type[BasicInvoice]) -> None:
        """Validate the requirements for the given profile."""
        if not issubclass(profile, EN16931Invoice):
            if self.percent is not None:
                raise ModelError(
                    "Percentage-based charges are not allowed "
                    f"in the {profile.PROFILE_NAME} profile."
                )
            if self.basis_amount is not None:
                raise ModelError(
                    "Basis amount-based charges are not allowed "
                    f"in the {profile.PROFILE_NAME} profile."
                )


@dataclass
class DocumentAllowance(LineAllowance):
    """An allowance for the entire invoice."""

    _: KW_ONLY
    tax_category: TaxCategoryCode = TaxCategoryCode.STANDARD_RATE
    tax_rate: Decimal | None = None


@dataclass
class DocumentCharge(LineCharge):
    """A surcharge for the entire invoice."""

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
            raise ModelError(
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

    def validate(self, profile: type[BasicWLInvoice]) -> None:
        """Validate the requirements for the given profile."""
        if not issubclass(profile, EN16931Invoice):
            if self.information is not None:
                raise ModelError(
                    "Payment means information is not allowed in the "
                    f"{profile.PROFILE_NAME} profile."
                )
            if self.card is not None:
                raise ModelError(
                    "Payment means card information is not allowed in the "
                    f"{profile.PROFILE_NAME} profile."
                )
            if (
                self.payee_account is not None
                and self.payee_account.name is not None
            ):
                raise ModelError(
                    "Payment means account name is not allowed in the "
                    f"{profile.PROFILE_NAME} profile."
                )
            if self.payee_bic is not None:
                raise ModelError(
                    "Payment means BIC is not allowed in the "
                    f"{profile.PROFILE_NAME} profile."
                )


@dataclass
class PaymentTerms:
    """Payment terms data used in invoices."""

    _: KW_ONLY
    description: str | None = None  # EN16931+
    due_date: datetime.date | None = None
    direct_debit_mandate_id: str | None = None

    def validate(self, profile: type[BasicWLInvoice]) -> None:
        """Validate the requirements for the given profile."""
        if not issubclass(profile, EN16931Invoice):
            if self.description is not None:
                raise ModelError(
                    "Payment terms description is not allowed in the "
                    f"{profile.PROFILE_NAME} profile."
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
    rate_percent: Decimal | None
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
            raise ModelError(
                "Invalid due date type code: {self.due_date_type_code}."
            )

    def validate(self, profile: type[BasicWLInvoice]) -> None:
        """Validate the requirements for the given profile."""
        if not issubclass(profile, EN16931Invoice):
            if self.tax_point_date is not None:
                raise ModelError(
                    "Tax point date is not allowed in the "
                    f"{profile.PROFILE_NAME} profile."
                )
