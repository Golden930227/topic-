# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.


## 訪客入口

訪客使用 Google 登入後直接進入 `/visitor`，不再顯示訪客資料登記或讀寫 Firestore `visitors/{uid}`。舊 `/visitor-register` 在登入檢查後導回訪客入口；未登入者仍須先登入。既有 Firestore 資料不刪除，不部署或放寬 Firestore 規則。員工白名單與員工頁面權限維持原設定。

後端 Firebase 身分驗證不再要求訪客表單，但仍驗證登入憑證及員工白名單。可執行 `python -m unittest discover -s tests -p test_visitor_auth.py -v` 驗證新舊訪客皆不會查詢 Firestore，且員工驗證仍保留。
