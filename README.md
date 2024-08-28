# PyFactur-X – Factur-X/ZUGFeRD parsing and generation library for Python

[![GitHub](https://img.shields.io/github/release/zfutura/pyfacturx/all.svg)](https://github.com/zfutura/pyfacturx/releases/)
[![Apache 2.0 License](https://img.shields.io/github/license/zfutura/pyfacturx)](https://github.com/zfutura/pyfacturx/blob/main/LICENSE)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/zfutura/pyfacturx/test-and-lint.yml)](https://github.com/zfutura/pyfacturx/actions/workflows/test-and-lint)

Factur-X (also called ZUGFeRD in Germany) is a Franco-German standard for
electronic invoices. Structured XML data is embedded in PDF-A/3 files,
allowing invoices to be processed automatically, but still be displayed in
standard PDF readers. Factur-X supports EN 16931, the European standard for
electronic invoicing.

See the [Factur-X website (French)](https://www.factur-x.org/) or
[FeRD website (German)](https://www.ferd-net.de/) for more information.

Currently, this library supports reading and writing XML files according to
Factur-X Version 1.0.06 (aka ZUGFeRD 2.2) in the profiles up to EN 16931
(Comfort).

Generally in scope of this library, but currently not supported are:

* Extended and XRechnung profiles.
* Reading PDF Factur-X files.
* Embedding the XML in PDF files.

## Usage

### Generating Factur-X XML

PyFactur-X supports several profiles of Factur-X. First, you need to create
an instance of the correct profile. Then, you can pass that instance to one
of the generation functions.

```python
from datetime import date
from facturx import EN16931Invoice, Money, generate

invoice = EN16931Invoice(
    invoice_number="2021-123",
    invoice_date=date(2021, 4, 13),
    grand_total=Money("100.00", "EUR"),
    ...  # See the class documentation for all required and optional fields.
)
xml_string = generate(invoice)
```

### Parsing Factur-X XML

PyFactur-X can parse certain Factur-X XML files. The parser will return an
instance of the correct profile.

```python
from facturx import parse_xml

invoice = parse_xml(path_or_xml_string)  # MinimumInvoice or a subclass
```

### Printing invoices

To print a formatted Factur-X invoice to the terminal, you can use the
`format_invoice_as_text()` function:

```python
from facturx import format_invoice_as_text

invoice = EN16931Invoice(...)
print(format_invoice_as_text(invoice))
```

Currently, only invoices with the MINIMUM profile are supported.
