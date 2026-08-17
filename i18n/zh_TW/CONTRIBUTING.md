# 如何貢獻

[![English](https://img.shields.io/badge/lang-English-blue)](/i18n/en_US/CONTRIBUTING.md)
[![繁體中文](https://img.shields.io/badge/lang-繁體中文-red)](/i18n/zh_TW/CONTRIBUTING.md)

感謝您對我們的專案感興趣。

請詳閱本篇指引和[行為準則](https://www.contributor-covenant.org/zh-tw/version/2/1/code-of-conduct)以了解參與規範。

> [!IMPORTANT]
>
> 提交貢獻即表示您擔保：
>
> &nbsp;&nbsp;&nbsp;&nbsp;(一) 您為該貢獻之原始著作人，或已取得合法授權；\
> &nbsp;&nbsp;&nbsp;&nbsp;(二) 您同意依專案之 [LICENSE](/LICENSE) 授權您的貢獻。
>
> 詳情請參閱[開發者原創證書 (DCO)](https://developercertificate.org)。
<!-- Translation Ref: springframework.tw -->

## 議題討論

請從[清單](https://github.com/nicscda/fist-framework/issues/new/choose)選擇合適的主題開始或加入。

## 開發測試

### 前置作業

請先完成以下軟體安裝及配置。

<!-- NOTE! The official logo(=visualstudiocode) link is missing, use a custom logo instead -->
#### [![Visual Studio Code][visualstudiocode]](https://code.visualstudio.com (Visual Studio Code))

- **安裝指南**

  請從[官方網站](https://code.visualstudio.com/download)下載桌面版。

- **工作區設定**

  避免誤傳個人偏好設定：

  ```sh
  git update-index --skip-worktree .vscode/**
  ```

  復原追蹤共享遠端配置：

  ```sh
  git update-index --no-skip-worktree .vscode/**
  ```

#### [![Python Version](https://img.shields.io/badge/dynamic/regex?url=https%3A%2F%2Fraw.githubusercontent.com%2Fnicscda%2Ffist-framework%2FHEAD%2Fpyproject.toml&search=(requires-python%5B%5E0-9%5D%2B)(%5B0-9.%5D%2B)&replace=%242&style=for-the-badge&logo=python&logoColor=FFD43B&label=Python&labelColor=306998&color=gray)](https://python.org (Python))

- **安裝指南**

  請從[官方網站](https://www.python.org/downloads)下載，或使用 [Homebrew](https://brew.sh) / [pyenv](https://github.com/pyenv/pyenv) 管理套件並避免權限問題。

- **虛擬環境**

  防止不同專案間的版本衝突。

  啟動：

  ```sh
  python -m venv .venv
  # # 在 Windows 系統中，使用：
  # .venv\Scripts\activate
  # 在 Unix 或 MacOS 系統，使用：
  source .venv/bin/activate
  ```

  退出：

  ```sh
  deactivate
  ```

  詳情請參閱[官方教學](https://docs.python.org/3/tutorial/venv.html)。

#### [![Jekyll Version](https://img.shields.io/badge/dynamic/regex?url=https%3A%2F%2Fraw.githubusercontent.com%2Fnicscda%2Ffist-framework%2FHEAD%2FGemfile&search=(jekyll%5B%5E0-9%5D%2B)(%5B0-9.%5D%2B)&replace=%242&style=for-the-badge&logo=jekyll&logoColor=CB0000&label=Jekyll&labelColor=D9D9D9&color=gray)](https://jekyllrb.com (Jekyll))

- **安裝指南**

  請參考[官方教學](https://jekyllrb.com/docs/installation)完成安裝，包含相關系統及軟體需求如 [Ruby](https://ruby-lang.org)、GCC 和 Make。

### 工作流程

請先取得專案並進入專案根目錄。

1. 安裝環境

   ```sh
   make install config
   ```

   如欲了解更多指令與選項細節，請執行 `make` 查看幫助訊息和參閱[套件文件](/i18n/zh_TW/src/README.md)。

2. 創建資料

   - **互動指令（建議）**

     ```sh
     python -m src.cli add -R data
     ```

   - **手動建立**

     請參考[範本文件](/i18n/zh_TW/templates/)，並使用慣用的編輯器新增檔案。

3. 建置預覽

   ```sh
   make start SKIP="install config"
   ```

   啟動後請開啟瀏覽器前往 <http://localhost:4000>。

## 提交變更

完成開發與測試後請建立 [PR](https://github.com/nicscda/fist-framework/compare)。

更完整的倉庫分工、本地建置與 commit 前綴說明見 [團隊開發手冊](/i18n/zh_TW/HANDBOOK.md)。要把變更發到公開倉庫請看 [發布 SOP](/i18n/zh_TW/RELEASE.md)。

再次感謝您抽空做出貢獻！

[visualstudiocode]: https://img.shields.io/badge/Visual_Studio_Code-0078D4?style=for-the-badge&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMjggMTI4Ij48cGF0aCBmaWxsPSJ3aGl0ZSIgZmlsbC1ydWxlPSJldmVub2RkIiBkPSJNOTAuNzY3IDEyNy4xMjZhNy45NjggNy45NjggMCAwIDAgNi4zNS0uMjQ0bDI2LjM1My0xMi42ODFhOCA4IDAgMCAwIDQuNTMtNy4yMDlWMjEuMDA5YTggOCAwIDAgMC00LjUzLTcuMjFMOTcuMTE3IDEuMTJhNy45NyA3Ljk3IDAgMCAwLTkuMDkzIDEuNTQ4bC01MC40NSA0Ni4wMjZMMTUuNiAzMi4wMTNhNS4zMjggNS4zMjggMCAwIDAtNi44MDcuMzAybC03LjA0OCA2LjQxMWE1LjMzNSA1LjMzNSAwIDAgMC0uMDA2IDcuODg4TDIwLjc5NiA2NCAxLjc0IDgxLjM4N2E1LjMzNiA1LjMzNiAwIDAgMCAuMDA2IDcuODg3bDcuMDQ4IDYuNDExYTUuMzI3IDUuMzI3IDAgMCAwIDYuODA3LjMwM2wyMS45NzQtMTYuNjggNTAuNDUgNDYuMDI1YTcuOTYgNy45NiAwIDAgMCAyLjc0MyAxLjc5M1ptNS4yNTItOTIuMTgzTDU3Ljc0IDY0bDM4LjI4IDI5LjA1OFYzNC45NDNaIiBjbGlwLXJ1bGU9ImV2ZW5vZGQiLz48L3N2Zz4K
