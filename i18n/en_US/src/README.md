# FIST

[![PyPI Publish](https://github.com/nicscda/fist-framework/actions/workflows/publish.yml/badge.svg)](https://github.com/nicscda/fist-framework/actions/workflows/publish.yml (Publish Status))
[![English](https://img.shields.io/badge/lang-English-red)](/i18n/en_US/src/README.md)
[![繁體中文](https://img.shields.io/badge/lang-繁體中文-blue)](/i18n/zh_TW/src/README.md)

> Command-line toolkit for the [FIST Framework](https://nicscda.github.io/fist-framework)

Build, validate, and generate threat intelligence content with STIX export capabilities.

## Usage Example

```bash
# Create directories
mkdir -p data out

# Add new data file interactively
fist add -R data --output-dir data

# Generate STIX bundles and Jekyll content
fist build -R data --output-dir out
```

## Configuration

When the same setting is provided in multiple sources, the CLI determines the final value with the following precedence order (highest to lowest)

| Priority | Source | How to Set | Example |
| --- | --- | --- | --- |
| 1 | CLI options | Command flags | `--base-url <URL>` |
| 2 | Environment variables | System or CI | `FIST_BASE_URL=<URL>` |
| 3 | Custom `.env` | Via env file | `FIST_BASE_URL=<URL>` |
| 4 | Custom YAML | Via config file | `base_url: <URL>` |
| 5 | Defaults | *Built-in* \* | (varies by field) |

\* *Automatic fallbacks that cannot be set by users.*

### Core Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `FIST_YAML_FILE` | | Custom configuration file path |
| `FIST_PROJECT_NAME` | `FIST` | Framework identifier override, automatically formatted based on context |
| `FIST_BASE_URL` | `http://localhost:4000` | Base URL of your site |
| `FIST_SUBFOLDER` | | Output subdirectory and URL subpath (empty for root) |
| `FIST_ARTIFACT` | `bundle.json` | STIX bundle output filename |
| `LANGUAGE` | | Interface language (supports `en` and `zh_TW`) |

## Key Commands

| Command | Description | Key Options |
| --- | --- | --- |
| `add` | Interactive wizard to create threat intelligence data | `-R [PATHS]` `--output-dir [DIR]` `--[no-]auto-increment` |
| `build` | Validate and export structured documents | `-R [PATHS]` `--output-dir [DIR]` `--[no-]clean` |
| `config` | Manage local configuration | `[list\|edit\|reset]` |
| `transl` | Manage gettext translations | `--[no-]build` `--[no-]compile` |

Run `fist` or `fist <COMMAND> --help` for detailed options.
