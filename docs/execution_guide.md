# Ashfall 執行指南 (Execution Guide)

本指南說明如何執行 Ashfall 原型及其相關驗證工具。

## 1. 環境準備 (Environment Setup)

確保您的環境已安裝專案所需的依賴項目：

```bash
pip install -r requirements.txt
```

## 2. 執行核心遊戲原型 (Interactive CLI)

Ashfall 的主要體驗是透過 CLI 進行的互動式生存遊戲。

```bash
python scripts/play_cli_run.py
```

- **選擇種子 (Seed)**: `python scripts/play_cli_run.py 123` (預設為 101)
- **調整難度**: `python scripts/play_cli_run.py --difficulty hard`
- **幫助選單**: 在遊戲中輸入 `H` 可以查看生存手冊。

## 3. 執行驗證管道 (Validation Pipeline)

如果您正在進行開發或想要驗證數據完整性，可以使用以下腳本：

- **Phase A 數據驗證**: `python scripts/validate_phase_a.py` (包含地圖、敵人與事件數據)
- **平衡性模擬 (50 Runs)**: `python scripts/run_balance_metrics.py`
- **可玩性檢查 (5 Runs)**: `python scripts/run_playability_check.py`

## 4. 執行 FastAPI 範例 (Secondary Demo)

本專案包含一個獨立的 FastAPI 待辦事項示範應用：

```bash
# 啟動後端伺服器 (預設 http://localhost:8000)
python examples/todo-app-demo/src/main.py
```

## ⚠️ 注意事項：儀表板 UI

在 `README.md` 與 `walkthrough.md` 中提到的 **Phase 10.0 互動式儀表板 (Vite + React)** 目前在根目錄似乎尚未上傳或缺失。目前主要的互動與測試應以 `play_cli_run.py` 為主。

---
*本指南由 Antigravity 自動生成。*
