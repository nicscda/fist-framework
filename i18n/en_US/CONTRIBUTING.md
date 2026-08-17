# How to Contribute

[![English](https://img.shields.io/badge/lang-English-red)](/i18n/en_US/CONTRIBUTING.md)
[![繁體中文](https://img.shields.io/badge/lang-繁體中文-blue)](/i18n/zh_TW/CONTRIBUTING.md)

Thank you for your interest in contributing.

Please review the relevant sections of this guide and the [Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct) before submitting.

> [!IMPORTANT]
>
> By submitting a contribution to this project, you certify that:
>
> &nbsp;&nbsp;&nbsp;&nbsp;(a) you are the original author or have obtained the necessary rights to submit it; and\
> &nbsp;&nbsp;&nbsp;&nbsp;(b) you agree to license your contribution under the project's [LICENSE](/LICENSE).
>
> For more details, see the [Developer Certificate of Origin (DCO)](https://developercertificate.org).

## Issues & Discussions

Please select the appropriate [template or form](https://github.com/nicscda/fist-framework/issues/new/choose).

## Development

### Prerequisites

Please ensure the following are prepared before proceeding.

<!-- NOTE! The official logo(=visualstudiocode) link is missing, use a custom logo instead -->
#### [![Visual Studio Code][visualstudiocode]](https://code.visualstudio.com (Visual Studio Code))

- **Installation**

  Download the desktop app from the [official site](https://code.visualstudio.com/download).
  
- **Workspace Settings**

  To prevent local customizations from being committed:

  ```sh
  git update-index --skip-worktree .vscode/**
  ```

  To restore tracking for remote sharing:
  
  ```sh
  git update-index --no-skip-worktree .vscode/**
  ```

#### [![Python Version](https://img.shields.io/badge/dynamic/regex?url=https%3A%2F%2Fraw.githubusercontent.com%2Fnicscda%2Ffist-framework%2FHEAD%2Fpyproject.toml&search=(requires-python%5B%5E0-9%5D%2B)(%5B0-9.%5D%2B)&replace=%242&style=for-the-badge&logo=python&logoColor=FFD43B&label=Python&labelColor=306998&color=gray)](https://python.org (Python))

- **Installation**

  Download from the [official site](https://www.python.org/downloads), or use [Homebrew](https://brew.sh) / [pyenv](https://github.com/pyenv/pyenv) for easier package management and to avoid permission issues.

- **Virtual Environment**

  Isolates project dependencies to avoid version conflicts.

  To launch:

  ```sh
  python -m venv .venv
  # # On Windows, run:
  # .venv\Scripts\activate
  # On Unix or MacOS, run:
  source .venv/bin/activate
  ```

  To exit:

  ```sh
  deactivate
  ```

  For details, see the [official tutorial](https://docs.python.org/3/tutorial/venv.html).

#### [![Jekyll Version](https://img.shields.io/badge/dynamic/regex?url=https%3A%2F%2Fraw.githubusercontent.com%2Fnicscda%2Ffist-framework%2FHEAD%2FGemfile&search=(jekyll%5B%5E0-9%5D%2B)(%5B0-9.%5D%2B)&replace=%242&style=for-the-badge&logo=jekyll&logoColor=CB0000&label=Jekyll&labelColor=D9D9D9&color=gray)](https://jekyllrb.com (Jekyll))

- **Installation**

  Follow the [official guide](https://jekyllrb.com/docs/installation), including requirements, such as [**Ruby**](https://ruby-lang.org), GCC, and Make.

### Workflow

Please clone the repository and navigate to the project root first.

1. Setup

   ```sh
   make install config
   ```

   For environment variables and available options, see the [package documentation](/i18n/en_US/src/README.md) or run `make` to see more details.

2. Create Data

   - **CLI (Recommended)**

     ```sh
     python -m src.cli add -R data
     ```

   - **Manual**

     Copy the appropriate file from [available templates](/i18n/en_US/templates/) and edit with your preferred text editor.

3. Launch

   ```sh
   make start SKIP="install config"
   ```

   Visit <http://localhost:4000> in your browser.

## Changes

Please submit a [PR](https://github.com/nicscda/fist-framework/compare) when ready.

For repository roles, local setup, and commit prefixes, see the [team handbook](/i18n/zh_TW/HANDBOOK.md) (canonical Traditional Chinese; English stub: [HANDBOOK.md](/i18n/en_US/HANDBOOK.md)). Publishing to the public repository is documented in the [release SOP](/i18n/zh_TW/RELEASE.md).

We appreciate your contribution!

[visualstudiocode]: https://img.shields.io/badge/Visual_Studio_Code-0078D4?style=for-the-badge&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMjggMTI4Ij48cGF0aCBmaWxsPSJ3aGl0ZSIgZmlsbC1ydWxlPSJldmVub2RkIiBkPSJNOTAuNzY3IDEyNy4xMjZhNy45NjggNy45NjggMCAwIDAgNi4zNS0uMjQ0bDI2LjM1My0xMi42ODFhOCA4IDAgMCAwIDQuNTMtNy4yMDlWMjEuMDA5YTggOCAwIDAgMC00LjUzLTcuMjFMOTcuMTE3IDEuMTJhNy45NyA3Ljk3IDAgMCAwLTkuMDkzIDEuNTQ4bC01MC40NSA0Ni4wMjZMMTUuNiAzMi4wMTNhNS4zMjggNS4zMjggMCAwIDAtNi44MDcuMzAybC03LjA0OCA2LjQxMWE1LjMzNSA1LjMzNSAwIDAgMC0uMDA2IDcuODg4TDIwLjc5NiA2NCAxLjc0IDgxLjM4N2E1LjMzNiA1LjMzNiAwIDAgMCAuMDA2IDcuODg3bDcuMDQ4IDYuNDExYTUuMzI3IDUuMzI3IDAgMCAwIDYuODA3LjMwM2wyMS45NzQtMTYuNjggNTAuNDUgNDYuMDI1YTcuOTYgNy45NiAwIDAgMCAyLjc0MyAxLjc5M1ptNS4yNTItOTIuMTgzTDU3Ljc0IDY0bDM4LjI4IDI5LjA1OFYzNC45NDNaIiBjbGlwLXJ1bGU9ImV2ZW5vZGQiLz48L3N2Zz4K
