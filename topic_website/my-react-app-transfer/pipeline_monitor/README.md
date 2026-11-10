# WindMind Pipeline Monitoring Center

本機開發版，只有一個 Streamlit 服務、四個頁面。沒有模型訓練、EDR、隔離功能或 SQL 寫入。

## 啟動與存取

```powershell
python -m pip install -r requirements-monitor.txt
.\start_all.cmd
```

網址：http://127.0.0.1:8501。從專案 `.windmind-logs/monitor-access.txt` 取得本機存取碼，輸入頁面後才能讀取監控資料。存取碼不放在網址、啟動參數或 Git，也不由網站訪客選單提供。這只是額外的本機開發鎖，**不是 Firebase 員工權限驗證**，本機可讀取該檔案的人仍可進入。

獨立啟動：`powershell -NoProfile -ExecutionPolicy Bypass -File .\start_pipeline_monitor.ps1`。同一程式已在執行時沿用；8501 若被其他程式占用則警告，不終止或覆蓋。監控失敗不會停止 5173、5174、5175、8000。`start_all.cmd` 保留雙擊啟動及失敗時暫停功能。

只允許 `server.address=127.0.0.1`，手動改為公開綁定時資料頁會拒絕執行。不要用公開反向代理轉送這個開發版。`.windmind-logs` 是本機執行資料，包含存取碼、程序輸出及事件 SQLite；不要上傳或提供給訪客。若需輪替存取碼，先停止**本監控程序**、更換該檔案，再啟動；不用終止其他服務。

## A：已確認的來源（2026-11-10）

|來源|實際位置／觀察|用途與限制|
|---|---|---|
|Gateway|`../../rasberry_pi_to_sql/wind-turbine-docs/docs/flow/gateway_and_sql/Gateway.py`|會啟動 `fake_esp32.py`，不是已證實的真實硬體來源；本功能不啟動或修改它|
|驗證函式|同目錄 `FOR_CNN.py` 的 `for_cnn_receive_from_gateway`|僅檢查 ch1/ch2 整數；明確回報模型尚未連接。`elapsed_time` 是程式執行經過秒數，不是推論耗時|
|Gateway 範例表|`cnn_result_log`、`sensor_summary`|範例使用另外一個 SQL instance；目前網站 SQL 沒有這兩張表，顯示未提供|
|Gateway 日誌|同目錄 `gateway.log`、`sql_preview.log`；上層另有舊 `gateway.log`|已有歷史模擬資料；不將檔案修改時間當成真實接收成功，不顯示原始日誌|
|網站 SQL|與 `sql_api.py` 相同，環境變數 `SQL_SERVER` / `SQL_DATABASE`；Windows 整合驗證|預設 instance 與 database 沿用原 API；不顯示連線字串或憑證|
|網站表|`dbo.dc_measurements`、`dbo.ai_predictions`、`dbo.anomaly_events`|已實際查驗欄位；時間為 nvarchar，使用 TRY_CONVERT(datetimeoffset)；查詢結果時間轉文字以相容 ODBC|
|另外的 SQL 表|`grand_measurements`、`grand_ai_predictions`、`grand_anomaly_events`|已發現但目前 API 沒使用，不能冒充網站資料來源|
|FastAPI|`su_data_*/data_preprocessing/output/pages/sql_api.py`，`/api/health`、`/api/ai`、`/api/cnn`|HTTP 探測及格式檢查，不更動原端點|
|React|`src/pages/AiModelPage.jsx`、`CNNMonitorPage.jsx` 包入各自獨立 dashboard|每個 dashboard 有 API fetch，但沒有前端顯示完成回報；不得稱 React 正常|
|登入|`src/App.jsx` 的 Firebase Google 登入與前端 email 白名單|無 Streamlit 可驗證的員工 session；不修改訪客登入、Firestore Rules 或白名單|

SQL 最新樣本：網站資料的量測時間約為 2000-01-01，`inserted_at` 為 2026-10-26；grand 資料則於 2026-11-07 入庫。上游 `is_real_device=1`、`source_type` 與 `model_version` 只是記錄欄位，不能單憑這些值宣稱硬體在線或模型已載入。網站樣本版本為 `6.0.2-dc`，grand 為 `7.0.0-grand`；本機未找到可確認為現行四分類推論的模型載入程式或權重。

需求四類為 normal、voltage_sag、load_spike、severe_fault。現有 API 的欄位是 `probability_severe_anomaly`；保持原欄位與標籤，不建立推測映射、不重新訓練、不更動 CSV。

## B：四頁與已提供指標

0. **總覽**：三條 pipeline 的真實可觀察狀態；未知不顯示綠燈。量測新鮮度、最新記錄／入庫時間、最近一分鐘來源時間筆數、探測錯誤與延遲時間軸。
1. **P1**：顯示真實硬體資料尚未提供及已發現日誌的存在／大小／修改時間。接收率、最近真實接收紀錄與圖表、格式錯誤／空值／缺值／通訊中斷／傳輸延遲皆顯示未提供，絕不使用 fake_esp32 日誌充數。
2. **P2**：SQL 連線／讀取狀態、預測結果與信心度折線、SQL 記錄的版本、資料新鮮度、最近 100 筆識別碼重複檢查、SQL 異常事件表。模型載入、實際推論成功失敗與耗時、SQL 寫入成功失敗、連續樣本缺漏與 commit 延遲尚未提供。
3. **P3**：三個 API 的 HTTP／回應格式／connected 狀態、延遲、回傳筆數、最後成功主動探測、最近最多 500 筆探測事件內的失敗數、SQL/API 最新識別碼與欄位比較。**API 正常與 React 顯示確認分開**；React 目前為未知。不同時間探測的比較差異僅警告，不宣稱資料遺失。

每 3 秒重繪目前頁面；一個 Streamlit 程序只建立一個 cache_resource 背景收集器，所有使用者共享。SQL/API 每 15 秒探測一批，切頁和手動刷新不會立即增加 SQL 查詢。API 本身也會讀 SQL，因此一併限流。SQL query timeout=3 秒、API timeout=2 秒；每表最多讀取 100 筆，統計使用資料庫聚合（資料量大時應由 DBA 檢查時間欄位索引／查詢成本，不由監控改 schema）。收集器與 Gateway 資料傳輸無任何同步依賴。

## C：獨立監控事件

持久化於 `.windmind-logs/pipeline-events.sqlite3`，不接觸原資料表。欄位為 timestamp（UTC）、pipeline、component、event_type、status、latency_ms、error_message、trace_id。每個 probe 以 `uuid4` 產生新識別碼，**不使用 run_id**；目前是探測識別碼，不是跨 Gateway／CNN／SQL 的端到端 trace。資料欄位白名單排除原始 JSON、run_id、來源檔案路徑；錯誤僅保留固定描述／HTTP 狀態，沒有原始 DB 例外。

背景每批探測本身是監控心跳，保留 7 天，每頁最多看 500 個事件。這些次數是**本中心觀察到的探測結果**，不是生產系統所有 HTTP／推論／寫入總數。沒有把檔案 mtime 或 API 成功冒充 Gateway 心跳。

要完成缺少指標，需先提供目前正式硬體 Gateway 與 CNN 推論寫入程式，再於接收、驗證、推論、commit 的實際成功／失敗分支加非阻塞事件發送、可信新 trace ID 與來源／接收雙時間戳。先有實際分支與型別才能量測；此版不修改模擬 Gateway 以製造假即時資料。

## 正式員工驗證方案（未實作）

1. React 將登入者 Firebase ID token 送到同源後端，後端使用 Firebase Admin SDK `verify_id_token(..., check_revoked=True)`，驗證正確 project、簽章、有效期及已驗證 email；再檢查由伺服器管理的 employee claim／UID allowlist。前端白名單只作 UI，不作授權依據。
2. 後端建立短效、可撤銷的伺服器 session，使用 Secure/HttpOnly/SameSite cookie；不把 ID token 放網址或 Streamlit query params，也不硬編碼服務帳戶私鑰。
3. 受保護的同源反向代理於 Streamlit HTTP 與 WebSocket 握手／重連驗證 session 和 employee 權限；上游僅允許私有網路／loopback，禁止繞過代理直連。若傳遞身分標頭，代理必須刪除客戶端同名標頭並提供短效簽名斷言，由 Streamlit 驗證。
4. 權限撤銷與 session 到期需中斷或重新驗證既有 WebSocket；加入訪客、過期 token、撤銷員工權限與繞過代理測試後，才可宣稱正式員工權限完成。Firestore Rules 不需放寬。

參考：[Firebase ID token 驗證](https://firebase.google.com/docs/auth/admin/verify-id-tokens)、[工作階段撤銷](https://firebase.google.com/docs/auth/admin/manage-sessions)、[Streamlit fragment](https://docs.streamlit.io/develop/concepts/architecture/fragments)。

## D / E：驗證

```powershell
python -m unittest discover -s tests -p test_pipeline_monitor.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_all.ps1 -NoBrowser
python tests/check_pipeline_live.py
powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\check_monitor_port.ps1
python tests/check_startup_failure.py
```

測試包含真實 loopback HTTP server 的 200、503、停止後拒絕連線；以測試替身注入 SQL 連線失敗；來源缺少時 Gateway 未知；資料空白／停止更新／未來時間的狀態；SQL/API 比較；SQLite 關閉、歷史與 UUID 唯一性；安全欄位及文字時間 SQL 回歸；AppTest 四頁空資料呈現、錯誤存取碼、未驗證隱藏資料、公開 bind 拒絕。所有替身只在 tests 中，沒有作為即時資料載入。

真實硬體 Gateway／CNN 尚無可啟停來源，因此**未宣稱已做實體 Gateway 停機或正常推論測試**。SQL 服務不中止、不更動資料，以故障注入測試失敗分支；API 中斷使用隔離 HTTP server，避免中斷原網站。實際 SQL 唯讀驗證已確認三張網站表可讀，資料停滯為警告、每分鐘筆數 0。現有 API 健康探測曾回 503，監控如實顯示失敗，不以此驗證全流程正常。

Git 僅提交本功能的監控程式、依賴、啟動腳本、忽略規則、測試及本文件；一鍵啟動所需但原先尚未追蹤的既有 `sql_api.py` 也納入版本管理，保持原有端點行為。既有未提交的登入／選單／Gateway 移動等變更不混入。
