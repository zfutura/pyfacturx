# PyFactur-X – Factur-X/ZUGFeRD parsing and generation library for Python

[![GitHub](https://img.shields.io/github/release/zfutura/pyfacturx/all.svg)](https://github.com/zfutura/pyfacturx/releases/)
[![Apache 2.0 License](https://img.shields.io/github/license/zfutura/pyfacturx)](https://github.com/zfutura/pyfacturx/blob/main/LICENSE)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/zfutura/pyfacturx/test-and-lint)](https://github.com/zfutura/pyfacturx/actions/workflows/test-and-lint)


Factur-X (also called ZUGFeRD in Germany) is a Franco-German standard for
electronic invoices. Structured XML data is embedded in PDF-A/3 files,
allowing invoices to be processed automatically, but still be displayed in
standard PDF readers. Factur-X supports EN 16931, the European standard for
electronic invoicing.

See the [Factur-X website (French)](https://www.factur-x.org/) or
[FeRD website (German)](https://www.ferd-net.de/) for more information.

Currently, this library supports writing XML files according Factur-X Version
1.0.06 (aka ZUGFeRD 2.2) in the profiles up to EN 16931 (Comfort). Generally
in scope of this library, but currently not supported are:

* Extended and XRechnung profiles.
* Reading Factur-X files (XML or PDF).
* Embedding the XML in PDF files.
