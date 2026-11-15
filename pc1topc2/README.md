# PC1 → PC2 CSV 傳檔

流程只有：PC1 產出 CSV → HTTP POST 到 PC2 → PC2 存本機。沒有轉傳 PC3，也不涉及 WindMind、SQL 或模型。

此目錄原先為空。接收邏輯沿用現有 `C:\Users\admin\Downloads\receive_csv.py`／`D:\grand\接收程式\receive_csv.py` 的原始串流收檔方式，集中於本專案並加入可設定輸出路徑、啟動命令及測試。

## 位址與埠

- 已由這台電腦的 `tailscale status --json` 核對：主機 `DESKTOP-H5OBRG3`，DNS `desktop-h5obrg3.tail7bd211.ts.net`，Tailscale IPv4 是 **100.94.181.76**。
- 使用者已確認這台是合併後的 PC2＋PC3，因此該 IP 現在是 PC2 的目的地。發送端不寫死它，每次以 `--pc2-ip` 指定。
- 本流程全部統一 **TCP 8001**、`POST /upload-csv`。不使用或更動網站原本的 8000。
- 沿用直接 HTTP 原始檔案傳送，沒有額外 Token 驗證；可達性由 Tailscale 及現有防火牆／ACL 決定。程式不自動修改網路設定。

## PC2：安裝與啟動

只需安裝接收端依賴；PC1 的 send_csv.py 只使用 Python 標準庫。

```powershell
python -m pip install -r "C:\Users\admin\Downloads\topic\pc1topc2\requirements.txt"
```

直接貼進 PC2 PowerShell：

```powershell
python "C:\Users\admin\Downloads\topic\pc1topc2\receive_csv.py" --host 100.94.181.76 --output-dir "D:\接收區"
```

可省略 `--output-dir`，預設同為 `D:\接收區`；亦可用 `CSV_OUTPUT_DIR` 環境變數設定。每次接收先寫唯一 `.part`，完整接收且非空後才原子改名成唯一 `.csv`；成功回傳 201、file、bytes。空檔回 400；中斷會清除未完成檔案。不解析、重新編碼或改動 CSV 內容。

## PC1：傳送

把 send_csv.py 放到 PC1（或在 PC1 拉取此 Git 專案），在它所在資料夾開 PowerShell，直接貼上：

```powershell
python .\send_csv.py --csv (Read-Host "PC1 的 CSV 完整路徑") --pc2-ip 100.94.181.76
```

也可直接寫路徑，例如 `--csv "C:\data\result.csv"`。成功會印出 PC2 實際儲存檔名與位元組數。失敗回非零退出碼並顯示檔案、HTTP 狀態／PC2 原因、連線原因或逾時。不要用 multipart `-F`；本程式原樣傳送檔案 bytes。

## 驗證

```powershell
cd "C:\Users\admin\Downloads\topic\pc1topc2"
python -m pip install httpx  # 僅單元測試的 TestClient 需要
python -m unittest -v test_transfer.py
python .\test_transfer_live.py --pc2-ip 100.94.181.76 --output-dir "D:\接收區"
```

實際 HTTP 測試會啟動 8001 接收器、傳 sample.csv、核對完整 bytes、SHA-256、兩筆資料與時間欄位、檢查空檔 400 及接收器停止後的錯誤訊息。測試完成會釋放 8001；測試 CSV 留在指定輸出目錄，以回報的唯一檔名核對。

單機透過自身 Tailscale IP 測試不能代替跨機驗收。PC1 真正發送後，另在 PC1、PC2 對原檔與回報檔名執行 `Get-FileHash -Algorithm SHA256`，兩端必須一致。若跨機無法連線，先在 PC1 執行 `Test-NetConnection 100.94.181.76 -Port 8001`，確認 PC2 接收器、Tailscale 連線及既有 ACL／防火牆設定。

本機實測已通過：HTTP 201、131 bytes、2 筆資料，傳前／傳後 SHA-256 均為 `fc33bc788ee2397467c7e8f849f942f138d4a1d6c20f6468b3a8bf84b9f60515`。時間欄位從 `2026-11-15T08:00:00Z` 到 `2026-11-15T08:00:01Z` 原樣保留。空檔 400、CLI 成功輸出與接收器停止後回報連線失敗均已驗證；尚未從另一台 PC1 實際發送。
