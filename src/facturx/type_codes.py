"""
UNTDID type codes, maintained by UN/CEFACT.
"""

from enum import IntEnum, StrEnum


def N_(s: str) -> str:
    return s


ALLOWED_MIME_TYPES = [
    "application/pdf",
    "image/png",
    "image/jpeg",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.oasis.opendocument.spreadsheet",
]


class IdentifierSchemeCode(StrEnum):
    """Selected identifier scheme codes defined in ISO/IEC 6523."""

    GLN = "0088"  # Global Location Number, aka GS1/EAN location number
    GTIN = "0160"


class DocumentTypeCode(IntEnum):
    """Selected document type codes defined in UNTDID 1001.

    https://service.unece.org/trade/untdid/d99a/uncl/uncl1001.htm
    """

    VALIDATED_PRICED_TENDER = 50
    INVOICING_DATA_SHEET = 130
    PRO_FORMA_INVOICE = 325
    PARTIAL_INVOICE = 326
    INVOICE = 380
    CREDIT_NOTE = 381
    CORRECTION = 384
    PREPAYMENT = 386
    RELATED_DOCUMENT = 916

    @property
    def is_invoice_type(self) -> bool:
        return self in (
            DocumentTypeCode.PRO_FORMA_INVOICE,
            DocumentTypeCode.PARTIAL_INVOICE,
            DocumentTypeCode.INVOICE,
            DocumentTypeCode.CREDIT_NOTE,
            DocumentTypeCode.CORRECTION,
            DocumentTypeCode.PREPAYMENT,
        )

    @property
    def is_supporting_document_type(self) -> bool:
        return self in (
            DocumentTypeCode.VALIDATED_PRICED_TENDER,
            DocumentTypeCode.INVOICING_DATA_SHEET,
            DocumentTypeCode.RELATED_DOCUMENT,
        )


DOCUMENT_TYPE_NAMES = {
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


class ReferenceQualifierCode(StrEnum):
    """Selected reference qualifier codes defined in UNTDID 1153.

    https://service.unece.org/trade/untdid/d98b/uncl/uncl1153.htm"""

    PRICE_LIST_VERSION = "PI"


REFERENCE_QUALIFIER_NAMES = {
    ReferenceQualifierCode.PRICE_LIST_VERSION: N_("Price List Version"),
}


class PaymentTimeCode(IntEnum):
    """Selected payment time codes defined in UNTDID 2475.

    https://service.unece.org/trade/untdid/d98b/uncl/uncl2475.htm
    """

    INVOICE_DATE = 5
    DELIVERY_DATE = 29
    PAYMENT_DATE = 72

    @property
    def is_invoice_due_date(self) -> bool:
        return self in (
            PaymentTimeCode.INVOICE_DATE,
            PaymentTimeCode.DELIVERY_DATE,
            PaymentTimeCode.PAYMENT_DATE,
        )


PAYMENT_TIME_CODE_NAMES = {
    PaymentTimeCode.INVOICE_DATE: N_("Invoice Date"),
    PaymentTimeCode.DELIVERY_DATE: N_("Delivery Date"),
    PaymentTimeCode.PAYMENT_DATE: N_("Payment Date"),
}


class TextSubjectCode(StrEnum):
    """Selected text subject codes defined in UNTDID 4451.

    https://service.unece.org/trade/untdid/d96b/uncl/uncl4451.htm
    """

    GENERAL_INFORMATION = "AAI"
    COMMENTS_BY_SELLER = "SUR"
    REGULATORY_INFORMATION = "REG"
    LEGAL_INFORMATION = "ABL"
    TAX_INFORMATION = "TXD"
    CUSTOMS_INFORMATION = "CUS"
    TITLE = "AFM"


TEXT_SUBJECT_CODE_NAMES = {
    TextSubjectCode.GENERAL_INFORMATION: N_("General Information"),
    TextSubjectCode.COMMENTS_BY_SELLER: N_("Comments by Seller"),
    TextSubjectCode.REGULATORY_INFORMATION: N_("Regulatory Information"),
    TextSubjectCode.LEGAL_INFORMATION: N_("Legal Information"),
    TextSubjectCode.TAX_INFORMATION: N_("Tax Information"),
    TextSubjectCode.CUSTOMS_INFORMATION: N_("Customs Information"),
    TextSubjectCode.TITLE: N_("Title"),
}


class PaymentMeansCode(StrEnum):
    """Selected payment means codes defined in UNTDID 4461.

    https://service.unece.org/trade/untdid/d98a/uncl/uncl4461.htm
    """
    NOTDEFINED = "1"
    SPECIES = "10"
    CHECK = "20"
    TRANSFER = "30"
    BANK_PAYMENT = "42"
    CREDIT_CARD = "48"
    DIRECT_DEBIT = "49"
    STANDING_AGREEMENT = "57"
    SEPA_CREDIT_TRANSFER = "58"
    SEPA_DIRECT_DEBIT = "59"
    REPORT = "97"
    INTERIM_AGREEMENT = "ZZZ"


PAYMENT_MEANS_NAMES = {
    PaymentMeansCode.NOTDEFINED: N_("Instrument not defined"),
    PaymentMeansCode.SPECIES: N_("Species"),
    PaymentMeansCode.CHECK: N_("Check"),
    PaymentMeansCode.TRANSFER: N_("Transfer"),
    PaymentMeansCode.BANK_PAYMENT: N_("Bank Payment"),
    PaymentMeansCode.CREDIT_CARD: N_("Credit Card"),
    PaymentMeansCode.DIRECT_DEBIT: N_("Direct Debit"),
    PaymentMeansCode.STANDING_AGREEMENT: N_("Standing Agreement"),
    PaymentMeansCode.SEPA_CREDIT_TRANSFER: N_("SEPA Credit Transfer"),
    PaymentMeansCode.SEPA_DIRECT_DEBIT: N_("SEPA Direct Debit"),
    PaymentMeansCode.REPORT: N_("Report"),
    PaymentMeansCode.INTERIM_AGREEMENT: N_("Interim Agreement"),
}


class AllowanceChargeCode(IntEnum):
    """Selected allowance/charge/discount codes defined in EN 16931.

    Despite the standard saying different, these codes only partially
    correspond to UNTDID 5189.

    https://service.unece.org/trade/untdid/d95b/uncl/uncl5189.htm
    """

    AHEAD_OF_SCHEDULE = 41


class TaxCategoryCode(StrEnum):
    """Duty/tax/fee category codes defined in UNTDID 5305.

    https://service.unece.org/trade/untdid/d98a/uncl/uncl5305.htm
    """

    REVERSE_CHARGE = "AE"  # not in UNTDID 5305, but defined in EN 16931
    EXEMPT = "E"
    FREE_EXPORT = "G"
    INTRA_COMMUNITY_EXEMPT = "K"  # not in UNTDID 5305, but defined in EN 16931
    CANARY_ISLANDS_TAX = "L"  # not in UNTDID 5305, but defined in EN 16931
    CEUTA_MELILLA_TAX = "M"  # not in UNTDID 5305, but defined in EN 16931
    OUT_OF_SCOPE = "O"
    STANDARD_RATE = "S"
    ZERO_RATE = "Z"


class ItemTypeCode(StrEnum):
    """Selected item type codes defined in UNTDID 7143.

    https://service.unece.org/trade/untdid/d96a/uncl/uncl7143.htm
    """

    ISBN = "IB"
    ISSN = "IS"


class SpecialServiceCode(StrEnum):
    """Selected special service (surcharge) codes defined in UNTDID 7161.

    https://service.unece.org/trade/untdid/d98a/uncl/uncl7161.htm
    """

    MATERIAL_SURCHARGE = "MC"


class VATExemptionCode(StrEnum):
    """VAT exemption codes defined by the Connecting Europe Facility (CEF).

    https://ec.europa.eu/digital-building-blocks/sites/display/DIGITAL/Registry+of+supporting+artefacts+to+implement+EN16931
    """
