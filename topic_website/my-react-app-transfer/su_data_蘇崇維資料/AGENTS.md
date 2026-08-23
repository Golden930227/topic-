# Project Instructions

## File and Folder Naming Rules

本專案新增、整理、重新命名檔案與資料夾時，必須遵守以下規則。

### 1. 一般資料夾使用「ASCII ID + 中文說明」

格式：

<ascii_id>_<中文說明>

例如：

- su_data_蘇崇維資料
- zhang_ai_張風發模型
- pi_comm_樹莓派通訊
- web_ui_網站介面
- cnn_monitor_CNN監測
- test_data_測試資料

ASCII 前綴是穩定識別碼。
中文部分只用於方便人類閱讀。

搜尋、腳本、自動化與 Codex 操作時，應優先使用 ASCII 前綴辨識資料夾。

---

### 2. 不要使用完整中文拼音

禁止建立過長名稱，例如：

su_chong_wei_zi_liao_yu_chu_li

應改成：

su_data_蘇崇維資料

ASCII ID 必須短、固定、容易搜尋。

---

### 3. 機器高度依賴的名稱使用純 ASCII

以下項目優先使用純 ASCII：

- Git repository
- Python module / package
- npm project
- React source files
- API route
- script
- config
- import path
- build/deployment 相關檔案

例如：

data_preprocessing.py
model_train.py
model_predict.py
pi_client.py
web_frontend
cnn_monitor

不要因為方便閱讀而把 Python module、npm package 等核心名稱改成中文。

---

### 4. 程式碼不要依賴中文名稱

如果資料夾名稱為：

su_data_蘇崇維資料

程式、自動化腳本與 Codex 搜尋時，應盡量依賴：

su_data

而不是依賴完整中文名稱。

如果中文名稱變更，不應造成整個系統失效。

---

### 5. 禁止容易混淆的特殊字元

名稱中避免：

- Emoji
- 全形英數字
- 全形空格
- 花式引號
- 特殊破折號
- 不必要符號

分隔符統一優先使用半形：

_

例如：

su_data_蘇崇維資料

---

### 6. 不確定名稱時

如果 Codex 不確定某個資料夾或檔案應如何命名：

1. 先查看現有專案結構。
2. 優先沿用既有 ASCII ID。
3. 不要自行建立另一套命名規則。
4. 不要只因名稱不好看就擅自重新命名既有路徑。
5. 若重新命名可能影響 import、API、設定檔或部署，先檢查引用位置。

---

## Existing ID Convention

目前建議使用：

- su_data = 蘇崇維資料／資料處理
- zhang_ai = 張風發 AI 模型
- pi_comm = Raspberry Pi 通訊
- web_ui = 網站前端
- cnn_monitor = CNN 監測
- test = 測試
- docs = 文件
- output = 輸出結果
- archive = 舊版本

新增分類時，沿用相同原則。

---

## Safety Rule

重新命名或移動任何既有檔案前：

1. 搜尋整個專案中的引用。
2. 檢查 Python import。
3. 檢查硬編碼路徑。
4. 檢查 React / JavaScript import。
5. 檢查 API、launcher、config 與部署設定。
6. 確認修改後功能不會中斷。

不要為了整理資料夾而破壞目前可以運作的功能。

大量自動生成檔案造成目錄混亂時，不要逐一重新命名產物；優先找到 generator/output path，從產生端修改目錄結構。