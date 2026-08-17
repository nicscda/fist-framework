# 發布 SOP

[![English](https://img.shields.io/badge/lang-English-blue)](/i18n/en_US/RELEASE.md)
[![繁體中文](https://img.shields.io/badge/lang-繁體中文-red)](/i18n/zh_TW/RELEASE.md)

這份文件說明：從 dev 改完東西，到公開倉庫 `fist-framework` 出現新的 GitHub Release 與文件站，中間要按哪些按鈕。預設讀者已經讀過 [開發手冊](/i18n/zh_TW/HANDBOOK.md)。

> [!IMPORTANT]
> 合進 `fist-framework-dev` 的 `main` **不會**自動更新 public。一定要有人在 GitHub Actions 手動跑 **Asset Sync**。

## 先搞清楚兩條版本線

| | dev（`fist-framework-dev`） | public（`fist-framework`） |
| --- | --- | --- |
| 誰在升版 | 合進 `main` 後，release-please 自動開 PR | Asset Sync 推進去的那筆 commit，再由 public 自己的 release-please 開 PR |
| 目前量級 | `0.0.x`（內部開發） | `1.x.x`（對外穩定版） |
| 網站 | 內部 Pages（推測 `…/fist-framework-dev`） | 正式 Pages（推測 `…/fist-framework`） |

兩邊的 `.github/release-please/.release-please-manifest.json` **不會**被同步覆蓋，所以版本號本來就該分開算。

## 兩顆地雷（請先記住）

### 雷 1：`build:` 不會讓 public 升版

Asset Sync 推到 public 的 commit 訊息會被 release-please 拿去算版本。

- `feat:` → 開 release PR，升 minor
- `fix:` → 開 release PR，升 patch
- `build:` / `chore:` / `docs:` → 多半**只更新檔案、不開新版**

舊的 workflow 預設訊息是 `build: :bento: sync assets to production`，所以檔案過去了，public 仍停在 1.0.0。新的預設已改成 `feat: :rocket: sync framework assets to production`。

### 雷 2：不要再讓腳本把版號寫成 `v1.0.0`

舊邏輯：從 `v0.*` tag 同步時，一律寫 `Release-As: v1.0.0`。public 已經有 `v1.0.0` 了，再跑一次會撞 tag。

新邏輯：

- 檔案從哪裡來：GitHub Actions 頁面上 **Use workflow from** 選的那個 branch/tag。
- public 要發幾點幾：表單的 **release_as**。這次請填 `1.0.2`。
- 若 `release_as` 留 `-`，腳本會讀 public 的 manifest 然後 **patch + 1**。public 現在是 `1.0.0`，自動會得到 `1.0.1`，**不是** 1.0.2。要跳號就一定要手動填。

## 標準流程

下列步驟以「要把目前 dev 的資料發成 public **1.0.2**」為例。之後發 1.0.3 / 1.1.0 時，只改版號與 commit 前綴即可。

### 第 1 步：在 dev 做完並合進 `main`

**在哪裡：** GitHub → `fist-framework-dev`，或你的終端機。

1. 從最新 `main` 開分支，改 `data/` / `src/` / 文件。
2. 本地建置檢查：`python -m src.cli build -R data --clean --output-dir out`
3. 開 PR。標題用 `feat:` 或 `fix:`（見手冊）。
4. 等 PR Check、Linter。非 draft 的 PR 會自動在 preview 站長出預覽頁；若 404，等幾分鐘再試。
5. 有權限的人批准後合併（標題合格會 squash）。

**檢查點**

- [ ] PR 已合進 `main`
- [ ] `data/techniques/` 裡這次要公開的 ID 都在（1.0.2 應含 T0011.004–006、T0062 系列）
- [ ] 不要只合在舊 tag `v0.0.13` 上：T0062 是後來才進 `main` 的

### 第 2 步（可選）：發一個 dev 內部 release

**在哪裡：** GitHub → `fist-framework-dev`。

push 到 `main` 之後，`release.yml` 會跑 release-please。若自上次 tag 以來有 `feat` / `fix` / breaking，bot 會開 `release-please--branches--main`。合了它，dev 會多一個 `v0.0.x` tag，並觸發內部 Pages 與（若已設定）PyPI。

**這一步不是 public 1.0.2 的必要條件。** Asset Sync 可以從 `main` 或任何 branch 拷檔，不必先有新的 dev tag。若你們想在內部也留一個對應里程碑，再合這顆 PR。

**檢查點**

- [ ] （可選）dev 出現新的 GitHub Release
- [ ] 內部 Pages 看起來正常

### 第 3 步：手動跑 Asset Sync（把檔案拷到 public）

**在哪裡：** GitHub 網頁 → `fist-framework-dev` → **Actions** → **Asset Sync** → **Run workflow**。

表單請這樣填：

| 欄位 | 填什麼 | 為什麼 |
| --- | --- | --- |
| Use workflow from | 已含新 `sync.yml` 的 ref（合進後選 `main`；尚未合併時用 `feature/1-0-2`） | GitHub 用「你選的這個 ref」上的 workflow 定義，也用它當檔案來源。選到舊 `main` 會跑到沒有 `release_as` 的舊腳本。 |
| target_repository | `fist-framework` | 預設就是它 |
| commit_message | 可留預設 `feat: :rocket: sync framework assets to production` | 必須是 `feat:` 或 `fix:`，不要改回 `build:` |
| **release_as** | **`1.0.2`** | 寫進 commit footer `Release-As: 1.0.2`，強制 public 發這版，而不是 1.0.1 或 1.1.0 |
| co_authors | 不需要就 `-` | 可填帳號或 `teams/fist-team` |
| action | `sync` | 先拷檔，不要選 `release` |

按下 **Run workflow**，等綠勾。

**檢查點**

- [ ] Actions 成功
- [ ] 到 `fist-framework` 的 `main` 看到一筆 bot commit（作者 `nicscda-action[bot]`）
- [ ] commit 訊息主旨是 `feat:`，footer 有 `Release-As: 1.0.2`
- [ ] 瀏覽 public 的 `data/techniques/`，看得到 T0062.yaml 等新檔
- [ ] **還沒有** 新的 GitHub Release（那是下一步）

`sync.yml` / `sync.sh` 不會被拷到 public，這是刻意的。CHANGELOG 與 public 的 release-please manifest 也不會被覆蓋。

### 第 4 步：在 public 合 release-please PR

**在哪裡：** GitHub 網頁 → `fist-framework`。

1. 等不到一分鐘到數分鐘，bot 應開出標題類似 `chore(main): :bookmark: release 1.0.2` 的 PR，分支名 `release-please--branches--main`。
2. 打開 PR，確認 CHANGELOG 與 `pyproject.toml` 的 version 是 **1.0.2**。若是 1.0.1 或 1.1.0，代表 `Release-As` 沒寫上或寫錯，**不要合**，先回頭查第 3 步的 commit footer。
3. 合併方式二選一：
   - 在該 PR 上按 Merge（squash）。
   - 或再跑一次 Asset Sync，**action 改成 `release`**（用 admin 權限合，用來隱藏批准者）。其他欄位可保持不變。

**檢查點**

- [ ] PR 已合
- [ ] `fist-framework` 出現 tag `v1.0.2`，以及浮動 tag `latest` / `v1` / `v1.0`（由 release.yml 更新）
- [ ] GitHub Releases 頁面有 1.0.2

### 第 5 步：等正式站部署

**在哪裡：** GitHub 網頁 → `fist-framework` → Actions → **Pages Build and Deploy**。

`deploy.yml` 的觸發條件是 **release published**，不是每一次 push。Release 一出現就會：

1. 用 **該 tag**（不是最新 main 的未標記 commit）checkout
2. 建 STIX bundle 並上傳到 Release（public 腳本是 `docs/bundle.json`）
3. 建 Jekyll 並部署 GitHub Pages

**檢查點**

- [ ] `Pages Build and Deploy` 成功
- [ ] 打開正式站（推測 `https://nicscda.github.io/fist-framework`），能搜到 T0062 / T0011.004
- [ ] Release 資產裡有 bundle 檔

若頁面 404：先等幾分鐘；仍不行再看 Pages 設定與 workflow log。

## 常見錯誤速查

| 現象 | 可能原因 | 怎麼辦 |
| --- | --- | --- |
| public 檔案更新了，但沒有新 release | sync commit 用了 `build:` / `chore:` | 再 sync 一次，訊息改 `feat:` 或 `fix:`，並填 `release_as` |
| release PR 寫 1.0.0 或警告 Duplicate tag | 舊腳本把 `v0.*` 映射成 1.0.0 | 確認跑的是含新 `sync.sh` 的 ref，且 `release_as=1.0.2` |
| release PR 寫 1.0.1 | `release_as` 留了 `-`，腳本對 1.0.0 做 patch+1 | 不要合；用 `release_as=1.0.2` 再 sync |
| release PR 寫 1.1.0 | 只有 `feat:`、沒有 `Release-As` footer | 同上，填 `release_as` |
| 正式站沒有 T0062 | 從舊 tag `v0.0.13` 同步，檔案來源不含 #87 | Use workflow from 選 `main`（或含 T0062 的 branch） |
| preview 404 | 剛開 PR，Pages 還沒建完 | 等；確認 PR 不是 draft，也不是 release-please / dependabot |
| Asset Sync 權限失敗 | 缺少 GitHub App secrets `APP_ID` / `PRIVATE_KEY` | 找還有組織權限的人，不要把金鑰寫進 repo |
| 想在 commit 訊息裡自己加 `Release-As` | 腳本會拒絕（避免跟表單衝突） | 用 `release_as` 欄位 |

## 這次 1.0.2 特別要注意

- 內容以 **dev `main`（含 #87）** 為準，不要用 `v0.0.13` 當檔案來源。
- public 跳過從未發過的 1.0.1，直接指定 **1.0.2**。
- 先把含新 sync 腳本的 PR 合進 dev `main`，再跑 Asset Sync；或暫時在 **Use workflow from** 選 `feature/1-0-2`。
