# 模板

## Schema 設定（選用）

若要在編輯器中啟用自動完成和驗證功能（例如 VS Code），請在 `$schema=` 後面加上 [schema 檔案路徑](/.schema.json)：

```yaml
# 使用本地路徑（推薦）
# yaml-language-server: $schema=../../.schema.json

# 或使用遠端連結
# yaml-language-server: $schema=https://raw.githubusercontent.com/nicscda/fist-framework/refs/tags/latest/.schema.json
```

設定後即可在編輯時獲得即時驗證和提示功能。
