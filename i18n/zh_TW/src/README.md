# FIST

[![PyPI Publish](https://github.com/nicscda/fist-framework/actions/workflows/publish.yml/badge.svg)](https://github.com/nicscda/fist-framework/actions/workflows/publish.yml (Publish Status))
[![English](https://img.shields.io/badge/lang-English-blue)](https://github.com/nicscda/fist-framework/blob/HEAD/i18n/en_US/src/README.md)
[![繁體中文](https://img.shields.io/badge/lang-繁體中文-red)](https://github.com/nicscda/fist-framework/blob/HEAD/i18n/zh_TW/src/README.md)

> [FIST框架](https://nicscda.github.io/fist-framework)命令列工具

建立、驗證並產生威脅情資內容，支援 STIX 格式匯出。

## 使用範例

```bash
# 建立目錄
mkdir -p data out

# 新增威脅情資資料（請根據互動式引導內容逐步完成）
fist add -R data --output-dir data

# 生成 STIX bundle 與 Jekyll 資源文件
fist build -R data --output-dir out
```

## 組態

當多個來源提供相同設定時，CLI 依照以下優先順序決定最終值（由高至低）：

| 優先序 | 來源 | 設定方式 | 範例 |
| --- | --- | --- | --- |
| 1 | CLI 選項 | 指令參數 | `--base-url <URL>` |
| 2 | 環境變數 | 系統或 CI | `FIST_BASE_URL=<URL>` |
| 3 | 自訂 `.env` | 透過環境變數檔 | `FIST_BASE_URL=<URL>` |
| 4 | 自訂 YAML | 透過設定檔 | `base_url: <URL>` |
| 5 | 預設值 | *內建* \* | (依欄位而異) |

\* *系統提供，無法自訂。*

### 核心環境變數

| 變數 | 預設值 | 說明 |
| --- | --- | --- |
| `FIST_YAML_FILE` | | 自訂設定檔路徑 |
| `FIST_PROJECT_NAME` | `FIST` | 自訂專案名與框架識別碼，會依情境自動轉換格式 |
| `FIST_BASE_URL` | `http://localhost:4000` | 網站基礎網址 |
| `FIST_SUBFOLDER` | | 輸出子目錄與網站子路徑（留空表示根目錄） |
| `FIST_ARTIFACT` | `bundle.json` | 輸出的 STIX bundle 檔名 |
| `LANGUAGE` | | 介面語言，支援 `en`（英文）與 `zh_TW`（繁體中文） |

## 常用指令

| 指令 | 說明 | 主要選項 |
| --- | --- | --- |
| `add` | 互動式建立詐騙框架檔案 | `-R [PATHS]` `--output-dir [DIR]` `--[no-]auto-increment` |
| `build` | 驗證並輸出格式化情資內容 | `-R [PATHS]` `--output-dir [DIR]` `--[no-]clean` |
| `config` | 管理本地設定檔 | `[list\|edit\|reset]` |
| `transl` | 管理多語系翻譯 | `--[no-]build` `--[no-]compile` |

執行 `fist` 或 `fist <COMMAND> --help` 查看詳細選項。
