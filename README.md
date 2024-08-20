# PyFactur-X – Factur-X/ZUGFeRD parsing and generation library for Python

[![GitHub](https://img.shields.io/github/release/zfutura/pyfacturx/all.svg)](https://github.com/zfutura/pyfacturx/releases/)
[![Apache 2.0 License](https://img.shields.io/github/license/zfutura/pyfacturx)](https://github.com/zfutura/pyfacturx/blob/main/LICENSE)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/zfutura/pyfacturx/test-and-lint)](https://github.com/zfutura/pyfacturx/actions/workflows/test-and-lint)


Factur-X (also called ZUGFeRD in Germany) is a Franco-German standard for
electronic invoices. Structured XML data is embedded in PDF-A/3 files,
allowing invoices to be processed automatically, but still be displayed in
standard PDF readers.

See the [Factur-X website (French)](https://www.factur-x.org/) or
[FeRD website (German)](https://www.ferd-net.de/) for more information.

Currently, this library supports writing XML files according Factur-X Version
1.0.06 (aka ZUGFeRD 2.2) in the EN16931 (Comfort) profile. Generally in scope
of this library, but currently not supported are:

* Other profiles (Minimum, Basic, Basic WL, Extended, XRechnung).
* Reading Factur-X files.
* Embedding the XML in PDF files.
