# FIST 團隊開發手冊

[![English](https://img.shields.io/badge/lang-English-blue)](/i18n/en_US/HANDBOOK.md)
[![繁體中文](https://img.shields.io/badge/lang-繁體中文-red)](/i18n/zh_TW/HANDBOOK.md)

給第一次進實驗室、還沒碰過這個專案的研究生。讀完這篇，你應該能在自己電腦把網站跑起來，並新增一筆技術資料。

發布到公開倉庫請另外看 [發布 SOP](/i18n/zh_TW/RELEASE.md)。貢獻流程細節見 [如何貢獻](/i18n/zh_TW/CONTRIBUTING.md)。

## FIST 是什麼

**FIST**（Fraud Incident Structured Threat）是一套描述「詐騙怎麼發生」的知識庫，寫法參考 [MITRE ATT&CK®](https://attack.mitre.org)。

你可以把它想成三層：

1. **資料**：`data/` 底下的 YAML。每一筆是一種戰術、技術、工具、緩解或偵測方式。
2. **程式**：`src/` 的 Python CLI。負責檢查 YAML、編成 [STIX 2.1](https://oasis-open.github.io/cti-documentation) bundle，並產出網站用的 JSON。
3. **網站**：`docs/` 的 Jekyll 樣板。把上一步的 JSON 渲染成可瀏覽的頁面。

最終產品是兩樣東西：一份可給 OpenCTI 等情資平台吃的 `bundle.json`，以及 GitHub Pages 上的文件站。

## 三個 GitHub 倉庫怎麼分工

請只在 **dev** 改程式和資料。不要把日常開發直接打在 public 上，下次同步會被覆蓋。

| 倉庫 | 你平常要做的事 | 不要誤會成 |
| --- | --- | --- |
| [fist-framework-dev](https://github.com/nicscda/fist-framework) | 開分支、改 YAML／程式、開 PR。內部版本號是 `0.0.x`。 | 這不是「還沒公開所以可以亂推」的垃圾桶，它是唯一的開發源。 |
| [fist-framework-preview](https://github.com/nicscda/fist-framework-preview) | 幾乎不用手動碰。你在 dev 開 PR 後，CI 會把預覽頁推到這裡。 | 不是正式產品的下一站，也不是完整備份。PR 關掉，對應的 `pr-編號` 資料夾就會被刪掉。 |
| [fist-framework](https://github.com/nicscda/fist-framework) | 對外公開版，版本從 `1.0.0` 起跳。由維護者手動跑 Asset Sync 更新。 | 合進 dev **不會**自動出現在這裡。 |

預覽網址（PR 開著時才有內容）：

`https://nicscda.github.io/fist-framework-preview/pr-{你的PR編號}`

## 本地環境

建議作業系統：Windows / macOS / Linux 都可以。Windows 若沒有 `make`，用下面的 Python 指令即可。

### 需要安裝的工具

1. **Git**
2. **Python 3.12+**（專案 `.python-version` 寫 3.12；3.13、3.14 也可以）
3. **[uv](https://docs.astral.sh/uv/)**：Python 套件管理。`pyproject.toml` 可能鎖定特定 uv 版本，若 `uv sync` 抱怨版本不符，可改用本手冊的 venv 作法。
4. **Ruby + Bundler + Jekyll**：只有要在瀏覽器看網站時才需要。只產生 STIX bundle 的話，Python 就夠了。

可選：

- **GNU Make**：`make start` 會一次跑完安裝、建置、開網站。
- **Visual Studio Code**：repo 已有 `.vscode/` 設定；個人偏好請用 `git update-index --skip-worktree .vscode/**`，避免把你的設定推上去。

### 第一次把專案跑起來

```sh
git clone https://github.com/nicscda/fist-framework-dev.git
cd fist-framework-dev
```

**作法 A（有 make、uv 版本也對得上）**

```sh
make start
```

瀏覽器開 <http://localhost:4000>。

**作法 B（沒有 make，或 uv 版本不合）**

```sh
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
# source .venv/bin/activate

pip install -r src/requirements.txt
python -m src.cli build -R data --clean --output-dir out
```

這一步會在 `out/bundle.json` 產出 STIX bundle。要看網站還需要 Jekyll：

```sh
bundle install
bundle exec jekyll serve --source docs
```

CLI 更完整的說明見 [套件 README](/i18n/zh_TW/src/README.md)。互動式新增資料：

```sh
python -m src.cli add -R data --output-dir data
```

## 怎麼新增一筆技術

技術檔放在 `data/techniques/`，一個 YAML 一筆。編號習慣：`T0001`、子技術 `T0001.001`。

1. 複製範本 [`i18n/zh_TW/templates/technique.yaml`](/i18n/zh_TW/templates/technique.yaml) 到 `data/techniques/T0xxx.yaml`（或用 `fist add`）。
2. 必填：
   - `type: technique`（不要改）
   - `id`：新的技術 ID。子技術必須接在父 ID 後面，例如 `T0062.001`。
   - `name`：人類看得懂的短名，不要換行。
   - `tactic_id`：所屬戰術，例如 `TA0002`。戰術清單在 `data/tactics/`。
   - `description`：用 `|` 寫多行說明。
3. 選填的清單若沒有內容，用 `[]`。不需要的區塊可以直接刪。
4. 若這筆技術已經過時、不要再出現在「現行手法」，把檔案底部的 `revoked: true` 取消註解。
5. 在 VS Code 開啟 YAML 時會套用 repo 根目錄的 `.schema.json`，紅線代表格式不對，請先修。
6. 本地驗證：

   ```sh
   python -m src.cli build -R data --clean --output-dir out
   ```

   成功會印出匯入了多少筆技術。把 `out/bundle.json` 搜尋你的 ID，確認 STIX 裡有對應的 `attack-pattern`。
7. 開 PR。標題用下一節的 conventional commit。變更類型勾「新增功能」。

其他種類（戰術、工具、緩解、偵測）同樣放在 `data/` 對應資料夾，範本在 `i18n/zh_TW/templates/`。

`data/*` 的 CODEOWNERS 比較寬：有 write 權限的人就可以批資料變更。程式與 CI 仍需要 `@nicscda/fist-team`。

## Commit message 規範

這個專案用 [Conventional Commits](https://www.conventionalcommits.org/zh-hant/v1.0.0/)，release-please 靠它決定要不要升版、CHANGELOG 寫什麼。實際 commit 常帶 gitmoji，例如：

```text
feat: :sparkles: add technique T0062 virtual persona
fix: :bug: correct T0011 description
docs: :memo: update handbook
```

| 前綴 | 什麼時候用 | 對 dev / public 的升版 |
| --- | --- | --- |
| `feat:` | 新技術、新功能 | **minor**（1.0.2 → 1.1.0；0.0.x 期間常見是 0.0.13 → 0.1.0，以 release-please 為準） |
| `fix:` | 修錯字、修邏輯、修壞掉的 YAML | **patch**（1.0.2 → 1.0.3） |
| `feat!:` / `fix!:` 或正文寫 `BREAKING CHANGE:` | 會讓舊資料／舊 CLI 不相容 | **major**（1.0.2 → 2.0.0） |
| `perf:` | 明顯變快 | patch |
| `docs:` `style:` `refactor:` `test:` `build:` `ci:` `chore:` | 文件、排版、重構、測試、CI、雜務 | **通常不單獨開新 release** |

PR 標題也要符合同一套格式。CI 會去 GitHub 的 branch ruleset 抓 regex（規則不在 repo 檔案裡）。標題合格會走 **squash** 合併，squash 後的 commit 標題 = PR 標題，這筆才會進 release-please。

不要用 `build:` 來表達「我們要發一個新的公開版」。那是這次踩過的雷，詳見 [發布 SOP](/i18n/zh_TW/RELEASE.md)。
