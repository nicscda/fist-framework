<a id="top"></a>

<!-- TITLE -->
# FIST Framework

<!-- PROJECT SHIELDS -->
[![GitHub Super-Linter](https://github.com/nicscda/fist-framework/actions/workflows/linter.yml/badge.svg?branch=main)](https://github.com/nicscda/fist-framework/actions/workflows/linter.yml?query=branch%3Amain++ (Build Status))
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

### Build with

<!-- NOTE! The official logo(=visualstudiocode) link is missing, use a custom logo instead -->
[![Visual Studio Code][visualstudiocode]](https://code.visualstudio.com (Visual Studio Code))

Before customizing personal workspace, it's recommended to run the following command:

```sh
git update-index --skip-worktree .vscode/**
```

This instructs [**`git`**](https://git-scm.com/docs/git-update-index (Git)) to ignore local changes to specific files, letting you modify personal configurations without affecting the repository.

To revert the tracking effect, use the `--no-skip-worktree` option.

<!-- GETTING STARTED -->
## Getting Started

This is a guide to help you set up your project locally. To get started, follow these simple steps:

### Prerequisites

_For developers, ensure you have **Python** and **Jekyll** installed. Additionally, prepare your IDEs for a smooth workflow._

#### [![Python](https://img.shields.io/badge/Python-306998?style=for-the-badge&logo=python&logoColor=FFD43B)](https://python.org (Python))

- Installation

  - Download the installer from the [official site](https://python.org).
  - It's recommended to use [**Homebrew**](https://brew.sh) or [**pyenv**](https://github.com/pyenv/pyenv) for easier package management and to avoid permission issues.

- Virtual Environment Setup

  - It's recommended (but optional) to run the following command to create and activate it.

      ```sh
      python -m venv .venv
      # # On Windows, run:
      # .venv\Scripts\activate
      # On Unix or MacOS, run:
      source .venv/bin/activate
      # To deactivate a virtual environment, type:
      deactivate
      ```

  - For more details, refer to the [official tutorial](https://docs.python.org/3/tutorial/venv.html).

#### [![Jekyll](https://img.shields.io/badge/Jekyll-D9D9D9?style=for-the-badge&logo=Jekyll&logoColor=CB0000)](https://jekyllrb.com (Jekyll))

- Installation

  - Follow the [official guide](https://jekyllrb.com/docs/installation) step by step, including pre-installation requirements, such as [**Ruby**](https://ruby-lang.org), [**RubyGem**](https://rubygems.org), [**GCC**](https://gcc.gnu.org), [**Make**](https://www.gnu.org/software/make) etc.

### Configuration

The app can be configured with the following variables:

| Env var | Default | Description |
| - | - | - |
| `SOURCE` |  | Required, the source name of the framework, following the `[[:word:]]` regular expression format (case-insensitive), the system will automatically adjust it as needed. It's recommended to use the same name as the project. |
| `BASE_URL` |  | Required, the base URL of the site related to this framework. |
| `AUTO_CLEAN` | false | Optional, automatically clean up before output. |
| `OUTPUT` | bundle.json | Optional, the file name of STIX bundle(.json). |
| `SUBFOLDER` |  | Optional, the sub folder of web pages. |
| `SUFFIX` |  | Optional, use it if you want to add an automatic suffix to the output. Supports `date`, `timestamp` and `version` formats. |

### Usage

Perform the following steps to create and deploy your custom framework site.

1. **Clone the repository**

   ```sh
   git clone https://github.com/<USERNAME>/<REPOSITORY_NAME>.git <DIRECTORY>
   ```

2. **Create metadata**

   First, please chose currently supported data types:

   - Contributor
     - [Individual](/templates/contributors/individual.yaml)
     - [Organization](/templates/contributors/organization.yaml)
   - Detection
     - [Component](/templates/detection/component.yaml)
     - [Source](/templates/detection/source.yaml)
   - [Mitigation](/templates/mitigation.yaml)
   - [Phase](/templates/phase.yaml)
   - [Tactic](/templates/tactic.yaml)
   - [Technique](/templates/technique.yaml)
   - [Tool](/templates/tool.yaml)
   - [Note](/templates/note.yaml)

   Next, identify what type of data you need.
   Copy the corresponding template contents to the suitable folder:

   ```sh
   # Align file names with data IDs. For example, a new technique named "T0001":
   id="T0001"; output="data/techniques/${id}.yaml";
   sed -e "0,/^id:.*/s//id: $id/" templates/technique.yaml > "${output}"
   ```

   Finally, modify fields to ensure the data is unique and readable.
   Use below command to find all places that need changes:

   ```sh
   # Search for the term "changeme" within specific file.
   grep -Ri changeme "${output}"
   ```

   If you are not sure how to start, we provide a `CLI` guide for creating new data. See step [5].

3. **Set up environment variables**

   Refer to the [Configuration](#configuration) section for details, then update the settings:

   ```sh
   cp .env.sample .env
   # Edit the file with your preferred text editor, for example:
   nano .env
   ```

   For MacOS and [Zsh](https://ohmyz.sh), which have stricter rules, use exporting temporary variables instead.

   ```sh
   set -a; [ -f .env ] && source .env; set +a
   ```

4. **Install packages**

   ```sh
   pip install .
   ```

5. **Create new data**

   ```sh
   # View help messages
   fist add --help
   # Make sure the output directory is created
   mkdir -p data
   # Load files in "data/**/*.yaml" for verification
   fist add -R data -t data [--[no]-auto-increment]
   ```

   - Options
     - `--auto-increment` : Automatically generate incremental IDs (default)
     - `--no-auto-increment` : Disable automatic ID generation, allow custom IDs

   Skip this step if you have already created and updated the data files.

6. **Run generator**

   ```sh
   # View help messages
   fist build --help
   # Make sure the output directory is created
   mkdir -p out
   # Generate files with "data/**/*.yaml"
   fist build -R data -t out
   ```

   If the data format or relationships are invalid, error messages will prompt for corrections.
   Otherwise, the bundle files will be exported and saved locally.

7. **Build and preview the site locally**

   Create the site directory, clone the necessary assets, and start the **Jekyll** server:

   ```sh
   # Initialize website directory
   mkdir -p site && rm -Rf site/*
   for i in docs out; do cp -Rf ${i}/* site; done
   # Serve the website
   bundle exec jekyll serve -s site
   ```

   Then, browse to <http://localhost:4000> to preview the site.

> [!NOTE]
> If developing with Visual Studio Code, simple use **Debugging** shortcut to skip steps 4, 6, and 7.
>
> ![Debugging Diagram](https://code.visualstudio.com/assets/docs/editor/debugging/debugging_hero.png (Debugging Diagram))
> <p align="center"><b>Debugger user interface, quoted from <a href="https://go.microsoft.com/fwlink/?linkid=830387"><i>visualstudio.com</i></a></b></p>

[<img src="/.github/images/arrow_circle_up.svg" align="right" alt="Back to top">](#top (Back to top))

---

## Attributions

This project references portions of the MITRE ATT&CK® framework.

© 2025 The MITRE Corporation. This work is reproduced and distributed with the permission of The MITRE Corporation.

The MITRE ATT&CK® framework is made available under terms described at: <https://attack.mitre.org/resources/terms-of-use/>

THE MITRE CORPORATION DOES NOT ENDORSE ANY COMMERCIAL PRODUCT, PROCESS, OR SERVICE.

[visualstudiocode]: https://img.shields.io/badge/Visual_Studio_Code-0078D4?style=for-the-badge&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMjggMTI4Ij48cGF0aCBmaWxsPSJ3aGl0ZSIgZmlsbC1ydWxlPSJldmVub2RkIiBkPSJNOTAuNzY3IDEyNy4xMjZhNy45NjggNy45NjggMCAwIDAgNi4zNS0uMjQ0bDI2LjM1My0xMi42ODFhOCA4IDAgMCAwIDQuNTMtNy4yMDlWMjEuMDA5YTggOCAwIDAgMC00LjUzLTcuMjFMOTcuMTE3IDEuMTJhNy45NyA3Ljk3IDAgMCAwLTkuMDkzIDEuNTQ4bC01MC40NSA0Ni4wMjZMMTUuNiAzMi4wMTNhNS4zMjggNS4zMjggMCAwIDAtNi44MDcuMzAybC03LjA0OCA2LjQxMWE1LjMzNSA1LjMzNSAwIDAgMC0uMDA2IDcuODg4TDIwLjc5NiA2NCAxLjc0IDgxLjM4N2E1LjMzNiA1LjMzNiAwIDAgMCAuMDA2IDcuODg3bDcuMDQ4IDYuNDExYTUuMzI3IDUuMzI3IDAgMCAwIDYuODA3LjMwM2wyMS45NzQtMTYuNjggNTAuNDUgNDYuMDI1YTcuOTYgNy45NiAwIDAgMCAyLjc0MyAxLjc5M1ptNS4yNTItOTIuMTgzTDU3Ljc0IDY0bDM4LjI4IDI5LjA1OFYzNC45NDNaIiBjbGlwLXJ1bGU9ImV2ZW5vZGQiLz48L3N2Zz4K
