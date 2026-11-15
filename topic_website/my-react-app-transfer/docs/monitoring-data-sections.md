# 監測頁的新舊資料

兩頁上方維持實機即時監測、每秒刷新及台灣時間顯示。取樣／判斷時間超過 SQL Server 目前時間 10 分鐘的資料，不再留在上方。異常事件依可確認的實際發生時間分類。

下方「舊資料」區讀取同一套 SQL 資料表。既有非即時來源、無法確認時間的紀錄也在此查閱，不混入上方判斷及圖表。CNN 顯示最近 200 筆舊量測，AI 顯示最近 50 筆舊判斷與 50 筆舊異常事件；下方每 30 秒更新，與上方每秒輪詢分開。

API 沿用 `/api/cnn`、`/api/ai`，以 `archive=true` 讀取舊資料，登入及角色檢查不變。查詢以十分鐘條件的互補集合取舊資料，不刪除、不搬動 SQL 紀錄。沒有可信實際時間時顯示「未提供」，不將相對時間當真實時間。

前端每次成功刷新依 API 的 serverNow 淘汰超過十分鐘的上方資料，即使沒有新 UID，舊紀錄也不會永久留在即時區。

驗證：

```
node --test tests/live_data.test.mjs
python -m unittest discover -s tests -p test_live_data.py -v
npm run lint
npm run build
python tests/check_archive_layout.py
```

最後一項使用 SQL Server 連線專屬暫存表與 Edge，確認一分鐘內資料在上方、十一分鐘前資料在下方，兩頁順序正確，不修改正式資料表。
