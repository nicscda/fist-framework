<a id="top"></a>

<!-- TITLE -->
# FIST 框架

<!-- PROJECT SHIELDS -->
[![GitHub Super-Linter](https://github.com/nicscda/fist-framework/actions/workflows/linter.yml/badge.svg?branch=main)](https://github.com/nicscda/fist-framework/actions/workflows/linter.yml?query=branch%3Amain++ (Build Status))
[![English](https://img.shields.io/badge/lang-English-blue)](/i18n/en_US/README.md)
[![繁體中文](https://img.shields.io/badge/lang-繁體中文-red)](/i18n/zh_TW/README.md)

<!-- BLURB -->
> 一個專為現代詐騙事件分析打造的敘事結構化威脅模型。

<!-- OVERVIEW -->
## 專案介紹

**FIST** 是以攻擊戰術、技術與程序（TTPs）為核心，系統性建構詐騙情資模組，整理了現代詐騙集團針對個人或企業目標所採用的攻擊路徑、行為流程、關鍵資產、社交工程技巧及新興手法。

**FIST** 協助使用者深入剖析各類詐騙事件，並透過階段性分解與專屬工具，快速建立通用或客製化的知識庫模板，匯出可導入 **[OpenCTI](https://filigran.io)** 等情資平台的 **[STIX](https://oasis-open.github.io/cti-documentation)** 標準格式資料集，為消費者、企業、資安產業、政府機構及社群提供多元防詐應用。

### 設計理念

我們的靈感主要來自著名的 **[MITRE ATT&CK®](https://attack.mitre.org)** 網路安全框架。有別於他們聚焦在對抗資安威脅和訊息操作，我們專注在詐欺行為研究，探討並建立詐騙與社交工程行為的模型與攻擊鏈。

我們的框架旨在促進跨組織情資共享、強化反詐騙協作機制，並作為未來開發監測工具與建置知識庫的基礎，以打擊詐騙相關犯罪。

### 開發工具

<!-- NOTE! The official logo(=visualstudiocode) link is missing, use a custom logo instead -->
[![Visual Studio Code][visualstudiocode]](https://code.visualstudio.com (Visual Studio Code))

自訂個人工作區之前請參考以下指令：

```sh
git update-index [--[no-]skip-worktree] .vscode/**
```

- 選項說明
  - `--skip-worktree` : 忽略本地變更
  - `--no-skip-worktree` : 恢復追蹤更新

該指令用於控制 [**`git`**](https://git-scm.com/docs/git-update-index (Git)) 的檔案追蹤行為，讓使用者修改個人開發環境配置而不影響遠端儲存庫。

<!-- GETTING STARTED -->
## 快速開始

以下指南用於幫助使用者在本地環境中快速建置及測試此專案：

### 開發環境

_請先安裝 **Python** 和 **Jekyll**，並確保開發環境（IDE）已配置妥當，以利專案程式運行。_

#### [![Python](https://img.shields.io/badge/Python-306998?style=for-the-badge&logo=python&logoColor=FFD43B)](https://python.org (Python))

- 安裝指南

  - 請從[官方網站](https://python.org)下載 Python 3.12 以上版本進行安裝。

  - 建議搭配 [**Homebrew**](https://brew.sh) 或 [**pyenv**](https://github.com/pyenv/pyenv) 進行軟體版本與套件管理。

- 虛擬環境

  建議建立虛擬環境並啟用它，以防止不同 Python 專案函式庫的套件和模組版本衝突。

  ```sh
  # 參考: https://docs.python.org/3/tutorial/venv.html
  python -m venv .venv
  # # 在 Windows 系統中，使用：
  # .venv\Scripts\activate
  # 在 Unix 或 MacOS 系統，使用：
  source .venv/bin/activate
  # 要停用虛擬環境，輸入：
  deactivate
  ```

#### [![Jekyll](https://img.shields.io/badge/Jekyll-D9D9D9?style=for-the-badge&logo=Jekyll&logoColor=CB0000)](https://jekyllrb.com (Jekyll))

- 安裝指南

  - 請參考[官方網站](https://jekyllrb.com/docs/installation)教學完成安裝，包含相關系統及軟體需求， 例如：[**Ruby**](https://ruby-lang.org)、[**RubyGem**](https://rubygems.org)、[**GCC**](https://gcc.gnu.org)、[**Make**](https://www.gnu.org/software/make/) 。

### 組態

本專案應用程式支援下列預先定義的使用者設定：

| 環境變數 | 預設值 | 描述 |
| - | - | - |
| `SOURCE` |  | 必填，框架的來源名稱，必須以英數字（A到Z、0到9）及底線（_）命名，但不區分大小寫，系統會根據上下文自動調整。建議使用專案的英文別名。 |
| `BASE_URL` |  | 必填，線上框架文件的基礎網址。 |
| `AUTO_CLEAN` | false | 可選，輸出前是否自動清理儲存目標資料夾。 |
| `OUTPUT` | bundle.json | 可選，輸出的 STIX 結構化資料檔案名稱（*.json） 。 |
| `SUBFOLDER` |  | 可選，輸出的網頁文件（*.md）集中存放的子資料夾名稱，同時也是線上文件的子目錄路徑。 |
| `SUFFIX` |  | 可選，為輸出檔案名添加後綴文字，預設空白。目前支援附帶日期（date）、時間戳記（timestamp）和版本號（version）三種選項。 |

### 使用方式

請按照以下步驟建立並部署您的自定義框架網站。

1. **取得儲存庫**

   建議初學者參考[官方網站](https://docs.github.com/repositories/creating-and-managing-repositories/cloning-a-repository)的圖文教學來完成操作。

   ```sh
   git clone https://github.com/<擁有者名稱>/<儲存庫名稱>.git <下載儲存位置>
   ```

2. **建立內容**

   請先選擇欲建立的資料類型，目前提供以下幾種：

   - 貢獻者（Contributor）
     - [個人（Individual）](/templates/contributors/individual.yaml)
     - [組織（Organization）](/templates/contributors/organization.yaml)
   - 偵測資料（Detection）
     - [元件（Component）](/templates/detection/component.yaml)
     - [來源（Source）](/templates/detection/source.yaml)
   - [緩解措施（Mitigation）](/templates/mitigation.yaml)
   - [階段（Phase）](/templates/phase.yaml)
   - [戰術（Tactic）](/templates/tactic.yaml)
   - [技術（Technique）](/templates/technique.yaml)
   - [工具（Tool）](/templates/tool.yaml)
   - [筆記（Note）](/templates/note.yaml)

   接著，請複製相應的資料範本到合適的資料夾存放。

   ```sh
   # 強烈建議檔案名稱與資料識別號（ID）對齊。例如，一個名為 "T0001" 的新技術：
   id="T0001"; output="data/techniques/${id}.yaml";
   sed -e "0,/^id:.*/s//id: ${id}/" templates/technique.yaml > "${output}"
   ```

   最後，請使用以下指令檢查所有欄位資訊是否已完成更新，確保新增檔案資料是唯一且可用的：

   ```sh
   # 在特定文件中搜索關鍵字 "changeme"
   grep -Ri changeme "${output}"
   ```

   如果不確定怎麼開始，我們有提供 `CLI` 協助建立新資料，請參照步驟5。

3. **設定環境變數**

   請參考[組態](#組態)的說明並更新本地環境參數設定。

   ```sh
   cp .env.sample .env
   # 使用您習慣的文字編輯器更新設定檔，例如：
   nano .env
   ```

   對於較嚴謹的 MacOS 和 [Zsh](https://ohmyz.sh) 環境，請記得於修改完後以匯出臨時變數後代入。

   ```sh
   set -a; [ -f .env ] && source .env; set +a
   ```

4. **安裝套件**

   ```sh
   pip install .
   ```

5. **創建新的內容**

   ```sh
   # 顯示工具命令和相關幫助訊息
   fist add --help
   # 確保輸出目錄已建立
   mkdir -p data
   # 載入 "data/**/*.yaml" 作為本地資料驗證
   fist add -R data -t data [--[no]-auto-increment]
   ```

   - 選項說明
     - `--auto-increment` : 自動遞增編號（預設行為）
     - `--no-auto-increment` : 禁用自動遞增，允許使用者自訂資料文件編號

   如果已於步驟二完成資料創建與更新，可跳過本步驟。

6. **執行生成工具**

   ```sh
   # 顯示工具命令和相關幫助訊息
   fist build --help
   # 確保輸出目錄已建立
   mkdir -p out
   # 載入 "data/**/*.yaml" 並生成資料模型及相應說明文件
   fist build -R data -t out
   ```

   如果資料格式驗證失敗，將提示錯誤訊息，供使用者修正。如果成功，新生成的 STIX 檔案及網頁文件將被匯出並儲存在本機資料夾中。

7. **在本機伺服器上建置網站**

   ```sh
   mkdir -p site
   for i in docs out; do cp -Rf ${i}/* site; done
   bundle exec jekyll serve -s site
   ```

   啟動後，打開瀏覽器前往 <http://localhost:4000> 即可看到剛建立的靜態網站。

> [!NOTE]
> 如果使用 Visual Studio Code 進行開發，可以透過 **Debugging** 功能快速執行步驟 4 、 6 和 7。
>
> ![Debugging 操作指引](https://code.visualstudio.com/assets/docs/editor/debugging/debugging_hero.png (Debugging 操作指引))
> <p align="center"><b>偵錯工具使用者介面，引自 <a href="https://go.microsoft.com/fwlink/?linkid=830387"><i>visualstudio.com</i></a></b></p>

[<img src="/.github/images/arrow_circle_up.svg" align="right" alt="Back to top">](#top (Back to top))

---

## 致謝

本專案引用 MITRE ATT&CK® 框架之部分內容，該部分之複製與發行依循 The MITRE Corporation 授權許可。

© 2025 The MITRE Corporation。

MITRE ATT&CK® 框架之使用與發佈條款詳見：<https://attack.mitre.org/resources/terms-of-use/>

**特此聲明，The MITRE Corporation 並未對本專案之任何衍伸商業產品、流程或服務提供認可、擔保或背書。**

[visualstudiocode]: https://img.shields.io/badge/Visual_Studio_Code-0078D4?style=for-the-badge&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMjggMTI4Ij48cGF0aCBmaWxsPSJ3aGl0ZSIgZmlsbC1ydWxlPSJldmVub2RkIiBkPSJNOTAuNzY3IDEyNy4xMjZhNy45NjggNy45NjggMCAwIDAgNi4zNS0uMjQ0bDI2LjM1My0xMi42ODFhOCA4IDAgMCAwIDQuNTMtNy4yMDlWMjEuMDA5YTggOCAwIDAgMC00LjUzLTcuMjFMOTcuMTE3IDEuMTJhNy45NyA3Ljk3IDAgMCAwLTkuMDkzIDEuNTQ4bC01MC40NSA0Ni4wMjZMMTUuNiAzMi4wMTNhNS4zMjggNS4zMjggMCAwIDAtNi44MDcuMzAybC03LjA0OCA2LjQxMWE1LjMzNSA1LjMzNSAwIDAgMC0uMDA2IDcuODg4TDIwLjc5NiA2NCAxLjc0IDgxLjM4N2E1LjMzNiA1LjMzNiAwIDAgMCAuMDA2IDcuODg3bDcuMDQ4IDYuNDExYTUuMzI3IDUuMzI3IDAgMCAwIDYuODA3LjMwM2wyMS45NzQtMTYuNjggNTAuNDUgNDYuMDI1YTcuOTYgNy45NiAwIDAgMCAyLjc0MyAxLjc5M1ptNS4yNTItOTIuMTgzTDU3Ljc0IDY0bDM4LjI4IDI5LjA1OFYzNC45NDNaIiBjbGlwLXJ1bGU9ImV2ZW5vZGQiLz48L3N2Zz4K
