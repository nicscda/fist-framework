<!-- TITLE -->
# FIST Framework

<!-- PROJECT SHIELDS -->
[![GitHub Super-Linter](https://github.com/nicscda/fist-framework/actions/workflows/linter.yml/badge.svg?branch=main)](https://github.com/nicscda/fist-framework/actions/workflows/linter.yml?query=branch%3Amain (Build Status))
[![English](https://img.shields.io/badge/lang-English-red)](/i18n/en_US/README.md)
[![繁體中文](https://img.shields.io/badge/lang-繁體中文-blue)](/i18n/zh_TW/README.md)

<!-- BLURB -->
> A knowledge base built from modern scam cases for fraud incident analysis via narrative-structured threat modeling.

<!-- OVERVIEW -->
## About The Project

**FIST** is centered around attack tactics, techniques, and procedures (TTPs), it systematically builds fraud intelligence modules by mapping out the attack paths, behavioral flows, key assets, social engineering tactics, and emerging methods used by modern fraud groups targeting individuals or organizations.

**FIST** helps users deeply analyze various types of fraud cases and, through step-by-step breakdowns and dedicated tools, quickly create standardized or customized knowledge base templates.
These can be exported as **[STIX](https://oasis-open.github.io/cti-documentation)**-compliant datasets for integration with threat intelligence platforms like **[OpenCTI](https://filigran.io)**, providing diverse anti-fraud applications for consumers, businesses, the cybersecurity industry, government agencies, and the broader community.

### Philosophy

Our framework draws inspiration from the renowned **[MITRE ATT&CK®](https://attack.mitre.org)** cybersecurity frameworks.
Unlike these frameworks, which focus on countering cyber threats and information operations, we focus on the study of fraudulent behaviors—analyzing and modeling fraud and social engineering activities and their attack chains.

Our mission is to foster cross-organizational intelligence sharing, strengthen collaborative anti-fraud efforts, and lay a solid foundation for the development of tools and knowledge bases to combat fraud-related crimes in the future.

## Quick Start

> Requires [GNU Make](https://www.gnu.org/software/make/).

Clone this repository and navigate to the project root, then run:

```sh
make start
```

For available options, run `make help`.

New contributors: start with the [team handbook](/i18n/zh_TW/HANDBOOK.md) (Traditional Chinese; [English stub](/i18n/en_US/HANDBOOK.md)). Publishing to the public repo: [release SOP](/i18n/zh_TW/RELEASE.md).

---

## Attributions

This project references portions of the MITRE ATT&CK® framework.

© 2025 The MITRE Corporation. This work is reproduced and distributed with the permission of The MITRE Corporation.

THE MITRE CORPORATION DOES NOT ENDORSE ANY COMMERCIAL PRODUCT, PROCESS, OR SERVICE.

For complete terms, see: <https://attack.mitre.org/resources/terms-of-use/>
