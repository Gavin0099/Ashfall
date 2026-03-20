# AI 治理框架導入 (Phase 8.0) 成果展示

成功將最新的 `ai-governance-framework` (Alpha v1.5+) 導入至 `Ashfall` 專案，建立更強固的 AI 協作與治理邊界。

## 關鍵改進項目

### 1. 治理法典與元數據同步
- **8 大法典升級**: 同步更新了 `ARCHITECTURE.md`, `TESTING.md`, `SYSTEM_PROMPT.md` 等核心文件，確保開發準則與框架最新版本對齊。
- **元數據導入**: 根目錄新增 `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md` 等，為 AI 提供清晰的行為軌跡與記憶管理規範。

### 2. 工具集升級與驗證 [governance_tools/]
- **同步 51 項治理工具**: 包含最新的 `memory_janitor.py`, `contract_validator.py` 以及新加入的 `violation_triage.py`。
- **相容性修復**: 針對新框架引起的 `test_failure_paths.py` (輻射損害判定) 進行了微調，確保 Phase Gates 能在新平衡公式下正確通過。

## 驗證結果

- **Governance Smoke Test**: ✅ Passed (ok=True)
- **Phase Gate Verification**: ✅ Passed (5/5 Gates OK)
  - Gate 1: Governance Unit Tests (Pytest) - **Passed**
  - Gate 2: Gameplay Validation Pipeline - **Passed**
  - Gate 3: PLAN Freshness - **Passed**
  - Gate 4: Governance Tools - **Passed**
  - Gate 5: Required Docs - **Passed**

---

# 環境與資源平衡調整 (Phase 7.0) 成果展示

在本次 Phase 7.0 中，我們鎖定了原先極低的勝率 (2%) 以及過高的輻射死亡率 (75%) 進行了深度優化。通過調整底層公式、修正模擬邏輯、加強資源獲取以及關鍵 BOSS 數值微調，我們成功將勝率提升至 **43%**。

## 關鍵改進項目

### 1. 輻射公式與裝備優化 [src/run_engine.py]
- **低級寬限**: 引入了 `(total_rad - 1) // 2` 公式，讓低輻射等級的玩家不再受到立即損害，提供了生存緩衝。
- **防毒面具強化**: 移動時有 50% 機率不消耗耐用度，大幅提升了面具的續航力。

### 2. 戰鬥邏輯與生存提升 [src/combat_engine.py]
- **醫療包強化**: 回復量從 8 HP 提升至 **10 HP**。
# Walkthrough: Perk Balance Infrastructure Expansion

本階段將 Perk 系統從「單點功能」提升至「可量化的平衡基礎建設 (Balance Infrastructure)」，建立了語義標籤、分層協同、平衡實驗室與玩家視圖。

## 📊 Balance Lab: 模擬實驗結果 (30 Steps)

| 策略 (Strategy) | 存活率 (Win Rate) | 廢料平均 | Perk 數量 | 主要死因 | Synergy 觸發 (T1/T2) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Survival** | 14.0% | 51 | 3.1 | Combat (43) | Step 0 / Step 10 |
| **Scavenge** | 12.0% | 58 | 3.0 | Combat (45) | Step 0 / Step 17 |
| **Hybrid** | 14.0% | 51 | 3.0 | Combat (43) | Step 0 / Step 16 |
| **Random** | 10.0% | 58 | 3.0 | Combat (45) | Step 0 / Step 17 |

> [!NOTE]
> **T1: 0** 表示 Tier 1 (2 Perks) 在初期（Step 0-5）即達成，流派傾向確立極快。
> **T2: 10-17** 表示 Tier 2 (4 Perks) 在中期達成，符合設計預期。

### 🚨 [STRESS TEST] Low-Roll Survival Floor
在極端倒楣（資源最低 roll、戰鬥傷害最高 roll）的情況下：
*   **Survival Floor**: 0% (所有策略均無法達到 30 步)。
*   **平均壽命**: 11-14 步。
*   **結論**: 目前的「下限保護」不足，未來需針對生存流派增加更強的低血量補償或保底食物。

## 🛠️ 核心變動

### 1. 語義標籤層 (Semantic Tagging)
在 [perks.json](file:///e:/BackUp/Git_EE/Ashfall/data/perks.json) 中將 **Mechanic Tags** (loot, food, radiation) 與 **Design Archetypes** (scavenger, survivor) 分離。一個 Perk 現在可以擁有多個機制標籤，支持更靈活的混搭。

### 2. 分層協同邏輯 (Tiered Synergy 2/4/6)
在 [modifiers.py](file:///e:/BackUp/Git_EE/Ashfall/src/modifiers.py) 實作了全域分層獎勵：
*   **Tier 1 (2 個)**: 基礎屬性加成 (如 Scrap +2)。
*   **Tier 2 (4 個)**: 核心機制強化 (如 輻射減免)。
*   **Tier 3 (6 個)**: 終極回報 (Capstone Padding)。

### 3. 玩家中心 HUD (Build Analysis UI)
重新設計了 [BuildAnalysis.jsx](file:///e:/BackUp/Git_EE/Ashfall/ui/src/components/BuildAnalysis.jsx)：
*   **Tier Progress Bars**: 直觀顯示各流派進度 (2/4/6)。
*   **Mechanism Tags**: 顯示具體的機制堆疊。
*   **Collapsible Details**: 隱藏冗長的 Debug 數據，優先顯示遊戲性相關的 Synergy 來源。

## ✅ 結論
我們現在不僅讓 Perk 能夠運作，更擁有了一套可以**精準觀察、量化模擬、並針對「極端值」進度修復**的開發體系。

## 驗證截圖/紀錄


---
- **治療門檻調優**: AI 治療門檻從 HP <= 6 提升至 **HP <= 8**，有效防止被高傷敵人（如 Overseer）直接擊殺。
- **無窮循環防護**: 增加了 100 回合戰鬥限制，解決了因防禦力持平導致的模擬卡死。

### 3. 資源獲取與事件優化 [schemas/event_template_catalog.json]
- **起始物資修正**: 修正了模擬腳本跳過起始節點的 Bug，現在所有玩家都能正確領取起始裝備與物資（彈藥 +2, 醫療包 +1）。
- **輻射清除路徑**: 在科技型事件中增加了輻射清除選項，讓玩家具備主動管理輻射的能力。
- **掉落率提補**: 提升了基礎敵人的彈藥與醫療包掉落。

### 4. 最終挑戰平衡 [schemas/enemy_catalog.json]
- **最終監察者 (Overseer)**: HP 從 50 瘋狂下調至 **25**。在目前 AI 模擬的簡單行為模式下，原本的 50 HP 是不可逾越的高牆。

## 驗證結果

### 模擬數據對比 (90 Runs)

| 指標 | 調整前 (Pre-7.0) | 調整後 (Final 7.0) | 改善幅度 |
| :--- | :--- | :--- | :--- |
| **勝率 (Victory Rate)** | **2%** | **43%** | **+2050%** |
| **主要死因 (Primary Death)** | 輻射 (75%) | 戰鬥 (100%) | 消滅輻射殺手 |
| **平均剩餘彈藥** | 0.88 | 2.60 | +195% |
| **平均剩餘醫療包** | 0.73 | 2.70 | +270% |
| **平均剩餘廢料** | 132.8 | 69.1 | 資源循環更健康 |

---

> [!IMPORTANT]
> 調整後的數據顯示 `radiation_death` 已幾乎歸零，玩家目前的死亡鏈多半源於連續戰鬥後的 HP 耗盡，這符合末世生存遊戲的設計預期——資源管理與戰鬥風險的權衡。

## 驗證截圖/紀錄


---

# 世界深度與任務演進 (Phase 9.0) 成果展示

在 Phase 9.0 中，我們為 `Ashfall` 引入了更豐富的世界互動機制，包括持久化的任務旗標、商人交易系統以及更具挑戰性的精英敵人機制。

## 關鍵改進項目

### 1. 任務旗標系統 (Quest Flag System) [src/event_engine.py]
- **持久化狀態**: 在 `RunState` 中新增了 `flags` 字典，允許事件根據玩家之前的選擇改變後續發展。
- **條件過濾**: 事件選項現在支援 `required_flags` 檢查，確保任務線的邏輯正確性。
- **動態更新**: 透過 `set_flags` 機制，玩家的抉擇能即時反映在世界軌跡中。

### 2. 商人與物資交易 (Merchant & Barter) [src/run_engine.py / schemas]
- **廢料經濟**: 實作了 `resource_requirement` 檢查，讓廢料 (Scrap) 成為真正的交易貨幣。
- **商人節點**: 在地圖中新增了 `trade` 類型節點，並設計了專屬的 `evt_merchant_caravan` (商人商隊) 事件。
- **多樣化商品**: 玩家可以在商人處穩定購買食物、彈藥及醫療包，提升了中後期的生存容錯率。

### 3. 精英敵人強化 (Elite Enemy Mechanics) [src/combat_engine.py]
- **被動技能 (Passives)**: 為 `EnemyState` 引入了被動技能清單。
- **能量護盾 (Shielded)**: 固定減少 1 點受到的傷害，增加了擊殺高防敵人的難度。
- **荊棘反震 (Thorns)**: 玩家每次攻擊命中時會受到 1 點反傷，迫使玩家在高 HP 時才發動猛攻。
- **日誌反饋**: 戰鬥日誌現在會清晰標註被動技能的觸發（如：【荊棘】反震！）。

## 驗證結果

### 專屬驗證腳本 (`verify_phase_9_features.py`)
- **Quest Flags**: ✅ Passed (Filtering & Setting OK)
- **Merchant Costs**: ✅ Passed (Resource blocking & Deduction OK)
- **Elite Passives**: ✅ Passed (Shielded reduction & Thorns reflection OK)

### 模擬路徑分析 (standard_journey)
- **商人互動**: 玩家在 `node_trade_1` 成功花費 5 廢料購買 5 食物，廢料從 13 降至 8，食物從 10 增至 15。
- **精英挑戰**: BOSS 戰中精英屬性及數值計算正確，戰鬥日誌符合預期。

---


---

# 互動式儀表板 (Phase 10.0) 成果展示

在 Phase 10.0 中，我們成功將 `Ashfall` 從純文字模擬引擎轉化為具有現代感的 **互動式網頁遊戲原型 (Playtest Dashboard)**。

## 關鍵技術亮點

### 1. API 橋接器 (FastAPI Bridge) [src/api_server.py]
- **引擎封裝**: 使用 FastAPI 將現有的 Python `RunEngine` 封裝，透過 REST API 曝露遊戲狀態。
- **端點實作**: 支援 `/api/run/start` (初始化)、`/api/run/state` (取得狀態) 及 `/api/run/select` (執行決策)。
- **CORS 支援**: 已配置跨來源資源共用，確保 Vite 開發伺服器能順利存取後端數據。

### 2. 現代化前端架構 (Vite + React) [ui/]
- **高效能框架**: 使用 Vite 搭配 React 建立單頁面應用程式 (SPA)。
- **組件化設計**: 實作了 `ResourcePanel` (資源面板)、`StoryViewport` (敘事視窗) 與 `ActionConsole` (行動控制台)。
- **狀態驅動介面**: 介面根據 API 回傳的 `RunState` 自動切換「事件決策」與「地圖移動」模式。

### 3. 高質感視覺系統 [ui/src/index.css]
- **末世廢土美學**: 採用深色模式、霓虹綠亮點與玻璃擬態 (Glassmorphism) 設計。
- **動態回饋**: 實作了血量條/物資條的平滑補間動畫 (Tweening) 與敘事文本的打字機效果。
- **響應式佈局**: 透過 CSS Grid 實現三欄式專業遊戲控制台介面。

## 本地執行指南

> [!IMPORTANT]
> 執行 UI 前請確保已安裝 `fastapi` 與 `uvicorn`：`pip install fastapi uvicorn`

1.  **啟動後端**: 在根目錄執行 `python src/api_server.py` (預設為 http://localhost:8000)。
2.  **啟動前端**: 在 `ui/` 目錄執行 `npm run dev` (預設為 http://localhost:5173)。
3.  **開始體驗**: 打開瀏覽器訪問前端路徑，點擊 "Start New Exploration" 即可開始遊戲。

---

> [!TIP]
> 透過此 UI，開發者可以直接在瀏覽器中體驗「商人決策」與「精英敵人戰鬥」的壓力感，這對於後續的數值微調與節奏掌控具有極大價值。
