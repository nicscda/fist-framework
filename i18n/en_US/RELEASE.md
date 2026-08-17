# Release SOP

[![English](https://img.shields.io/badge/lang-English-red)](/i18n/en_US/RELEASE.md)
[![繁體中文](https://img.shields.io/badge/lang-繁體中文-blue)](/i18n/zh_TW/RELEASE.md)

The canonical copy is Traditional Chinese:

**[i18n/zh_TW/RELEASE.md](/i18n/zh_TW/RELEASE.md)**

Merging to `fist-framework-dev` does **not** update public `fist-framework`. A maintainer must run **Asset Sync** by hand. Use a `feat:` / `fix:` commit message (not `build:`), and set **release_as** to the public version you want (for this train: `1.0.2`). Do not reuse the old `v0.*` → `v1.0.0` mapping; public already has `v1.0.0`.
