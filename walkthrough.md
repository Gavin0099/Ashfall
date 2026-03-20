# Project Walkthrough: Ashfall Evolution & Governance

本文件記錄 `Ashfall` 專案的演進路徑，分為「專案里程碑」與「核心專題深挖」兩大部分，以確保開發邏輯與治理邊界的清晰。

## 🧪 數據口徑與實驗框架 (Data Glossary)
為了確保數值分析的可信度，請參考以下實驗口徑：

| 實驗類型 | 規模 (Scope) | 目的 | 常見指標範圍 |
| :--- | :--- | :--- | :--- |
| **Campaign Run** | 90-run, Full journey | 驗證端到端遊戲勝率 | 勝率 (Victory Rate) 40%~50% |
| **Sandbox Lab** | 30-step, Middle-game | 驗證流派平衡與 Synergy | 存活率 (Win Rate) 12%~14% |
| **Stress Test** | 5-run, Bad-Luck | 驗證生存地板 (Floor) | 存活步數 (Lifespan) 13~15 |
| **Causal Loop (v2.2)** | 30-run, Diagnosics | 驗證治理與自動收斂 | 達標率 (Reach Rate) 80% |

---

# PART I: 專案演進里程碑 (Milestones)

### Phase 7.0: 環境與資源平衡 [src/run_engine.py]
- **目標**: 解決極低勝率 (2%) 與高輻射死亡率。
- **成果**: 引入輻射寬限點、強化防毒面具、提升醫療包回血。勝率從 2% 提升至 **43%** (Campaign Run)。

### Phase 8.0: AI 治理框架導入 (Operational Readiness)
- **目標**: 建立 AI 協作的技術邊界與驗證自動化。
- **成果**: 同步法典與 51 項治理工具，建立 5/5 Phase Gates。
- **治理實效案例**: `test_failure_paths.py` 因平衡公式變動產生 Drift，被 Gate 即時攔截並完成修復，證明了治理邊界的有效性。

### Phase 9.0: 世界深度與任務系統 [src/event_engine.py]
- **目標**: 引入持久化任務旗標 (Flags) 與商人經濟。
- **成果**: 實作了商人節點、廢料貨幣交易與精英敵人 (被動技能機制)。

### Phase 10.0: 互動式儀表板 (Playtest Dashboard) [ui/]
- **目標**: 提升開發者與玩家的可視化決策能力。
- **成果**: 建立 FastAPI 橋接器與高質感 React 介面。

---

# PART II: 核心專題深挖 (Thematic Deep Dives)

## ⚖️ 平衡治理 (Balance Governance)
Ashfall 的平衡開發已從「手動調參」進化為「證據導向 (Evidence-Guided)」的診斷體系。

### 1. 診斷與收斂 (v2.2 Causal Loop)
- **死亡分類 (Taxonomy)**: 診斷出 Step 13 死亡牆源於 `ATTRITION_CRISIS` (持續耗損) 而非單次暴擊。
- **節奏補償 (Pacing Buffer)**: 透過 `Last Stand` (絕地求生) 機制實作「安全網」，大幅提升了中期的生存地板至 30 步。

### 2. 標籤本體系統 (Tag Ontology)
- **Primary vs. Secondary**: 區分核心流派 (Archetype) 與戰術機制 (Mechanism)。
- **Bridge Perk Audit**: 建立審計機制，確保 `scout_mechanic` 等橋接 Perk 不會因過度萬用而導致流派邊界模糊 (Pick Rate 穩定在 26.7%)。

## 🏛️ AI 治理體系 (Governance Infrastructure)

### 1. 治理工具分級 (Tool Classes)
我們將 51 項工具按職責與風險等級進行分級：
- **[BLOCKING]**: Phase Gates 必備。攔截 Contract 違規 (如 `contract_validator.py`)。
- **[DIAGNOSTIC]**: 輔助診斷。檢查 PLAN 新鮮度與趨勢 (如 `plan_freshness.py`)。
- **[HYGIENE]**: 倉庫整潔。定期清理記憶與垃圾內容 (如 `memory_janitor.py`)。

### 2. Metadata 職責邊界 (Metadata Matrix)
為防止 AI 記憶漂移 (Drift)，明確定義了四類核心文件的職責：
- **SOUL.md**: 核心指令集 (內化規則)。
- **IDENTITY.md**: 技術角色定位與標籤 (靜態屬性)。
- **USER.md**: 外部協作者上下文 (偏好配置)。
- **AGENTS.md**: 工作空間操作規範 (現行任務)。

# PART III: 治理實效實例 (Evidence of Effectiveness)

治理框架不僅是文件，而是真實攔截並導正開發漂移 (Drift) 的機制。

### 案例：`test_failure_paths.py` 迴歸攔截
- **情境**: 在實施 V2.2 的 `Last Stand` (絕地求生) 補償機制時，開發者（我）修改了底層 healing 權重。
- **Drift**: 這次改動無意中改變了 `test_radiation_attrition` 的預期生存步數，導致既有的驗證腳本失敗。
- **攔截**: **Phase Gate 2 (Gameplay Validation)** 在 Commit 前即時報錯，攔截了這次潛在的「隱性邏輯更改」。
- **導正**: 通過 `violation_triage.py` 診斷後，確認這是「數值進化而非 Bug」，隨即同步更新了測試案例與 [PT1_CHECKLIST.md](file:///e:/BackUp/Git_EE/Ashfall/PT1_CHECKLIST.md)，確保規則與實作再次對齊。

---

## ✅ 結論
`Ashfall` 已經從一個單純的代碼專案變更為一個 **「被治理的開發系統」**。數據不再執行孤立的數字，而是跨越開發、治理與玩家體驗的決策鏈條。
