<!-- TITLE -->
# FIST 框架

<!-- PROJECT SHIELDS -->
[![GitHub Super-Linter](https://github.com/nicscda/fist-framework/actions/workflows/linter.yml/badge.svg?branch=main)](https://github.com/nicscda/fist-framework/actions/workflows/linter.yml?query=branch%3Amain (Build Status))
[![English](https://img.shields.io/badge/lang-English-blue)](/i18n/en_US/README.md)
[![繁體中文](https://img.shields.io/badge/lang-繁體中文-red)](/i18n/zh_TW/README.md)

<!-- BLURB -->
> 一個專為現代詐騙事件分析打造的敘事結構化威脅模型知識庫。

<!-- OVERVIEW -->
## 專案介紹

**FIST** 是以攻擊戰術、技術與程序（TTPs）為核心，系統性建構詐騙情資模組，整理了現代詐騙集團針對個人或企業目標所採用的攻擊路徑、行為流程、關鍵資產、社交工程技巧及新興手法。

**FIST** 協助使用者深入剖析各類詐騙事件，並透過階段性分解與專屬工具，快速建立通用或客製化的知識庫模板，匯出可導入 **[OpenCTI](https://filigran.io)** 等情資平台的 **[STIX](https://oasis-open.github.io/cti-documentation)** 標準格式資料集，為消費者、企業、資安產業、政府機構及社群提供多元防詐應用。

### 設計理念

我們的靈感主要來自著名的 **[MITRE ATT&CK®](https://attack.mitre.org)** 網路安全框架。有別於他們聚焦在對抗資安威脅和訊息操作，我們專注在詐欺行為研究，探討並建立詐騙與社交工程行為的模型與攻擊鏈。

我們的框架旨在促進跨組織情資共享、強化反詐騙協作機制，並作為未來開發監測工具與建置知識庫的基礎，以打擊詐騙相關犯罪。

## 快速開始

> 需先安裝 [GNU Make](https://www.gnu.org/software/make/)。

請下載專案並進入專案根目錄，然後執行：

```sh
make start ENV=prod
```

更多選項請參閱 `make help` 提示。

第一次接觸本專案的開發者請先讀 [團隊開發手冊](/i18n/zh_TW/HANDBOOK.md)。發布到公開倉庫請看 [發布 SOP](/i18n/zh_TW/RELEASE.md)。

---

## 致謝

本專案引用 MITRE ATT&CK® 框架之部分內容。

© 2025 The MITRE Corporation. This work is reproduced and distributed with the permission of The MITRE Corporation.

**特此聲明：The MITRE Corporation 並未對本專案之任何衍伸商業產品、流程或服務提供認可或背書。**

完整使用條款詳見：<https://attack.mitre.org/resources/terms-of-use/>
