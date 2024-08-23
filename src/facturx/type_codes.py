"""
UNTDID type codes, maintained by UN/CEFACT.
"""

from enum import IntEnum, StrEnum


class IdentifierSchemeCode(StrEnum):
    """Selected identifier scheme codes defined in ISO/IEC 6523."""

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


class ReferenceQualifierCode(StrEnum):
    """Selected reference qualifier codes defined in UNTDID 1153.

    https://service.unece.org/trade/untdid/d98b/uncl/uncl1153.htm"""

    PRICE_LIST_VERSION = "PI"


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


class PaymentMeansCode(StrEnum):
    """Selected payment means codes defined in UNTDID 4461.

    https://service.unece.org/trade/untdid/d98a/uncl/uncl4461.htm
    """

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
    """VAT exemption codes defined by the Connecting Europe Facility (CEF)."""
