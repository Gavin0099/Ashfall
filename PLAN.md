# PLAN.md — Ashfall

> **專案類型**: 單機 roguelite 生存策略遊戲原型
> **技術棧**: Markdown Specs + JSON Schema + Python (planned runtime)
> **複雜度**: L2
> **預計工期**: 2026/03/09 ~ 2026/05/01
> **最後更新**: 2026-03-09
> **Owner**: GavinWu
> **Freshness**: Sprint (7d)

---

## 📋 專案目標

**Primary Goal**: 在 CLI 原型中驗證選路是否能穩定產生高壓賭注感。  
**Secondary Goal**: 若原型可重玩性成立，再進入 Steam 上架準備。

Prototype validation contract: `PROTOTYPE_SUCCESS_CRITERIA.md`

**Bounded Context**:
- 回合循環（Run flow / death / victory）
- 地圖節點、事件、敵人資料模型與驗證
- 戰鬥、資源、事件效果解析與狀態更新

**不負責**:
- 美術、音效、UI 動畫
- 連線對戰或雲端同步
- 付費、商城、帳號系統

---

## 🏗️ 當前階段

```
階段進度:
├─ [✓] Phase A: 規格收斂與資料契約       (2026/03/09 完成)
├─ [✓] Phase B: 核心模擬引擎              (2026/03/09 完成)
├─ [✓] Phase C: 戰鬥與資源整合            (2026/03/09 完成)
└─ [🔄] Phase D: Meta 與平衡迭代           (進行中，預計 2026/05/01)
```

**當前 Phase**: **Phase D - Meta 與平衡迭代**

---

## 📦 Phase 詳細規劃

### Phase A: 規格收斂與資料契約 (已完成 ✓)

**目標**: 讓 specs 與 schemas 完整且可機器驗證，成為實作唯一依據。

**任務清單**:
```
規格與模型:
├─ [✓] 1. 讀取現有 specs/game_loop/map/event/combat/resource
├─ [✓] 2. 補齊 specs/meta_progression.md
├─ [✓] 3. 補齊 schemas/enemy_schema.json
└─ [✓] 4. 補齊 schemas/node_schema.json
```

**Gate 條件**:
- [x] `specs/*.md` 全部非空，且每份含「Overview + Rules/Fields」段落
- [x] `schemas/*.json` 可通過 JSON Schema lint（`python -m json.tool` + schema self-check）
- [x] 至少各有 2 筆符合 schema 的範例資料（event/enemy/node）

### Phase B: 核心模擬引擎 (已完成 ✓)

**目標**: 可執行單一 run 的主循環，涵蓋地圖移動與事件選項解析。

**任務清單**:
```
模擬核心:
├─ [✓] 1. 建立 RunState / PlayerState / MapState
├─ [✓] 2. Map 生成與節點連線驗證
├─ [✓] 3. 事件抽取與選項效果套用
├─ [✓] 4. 死亡/勝利判定與 run 結束流程
└─ [✓] 5. deterministic run 驗證與記錄
```

**Gate 條件**:
- [x] 可從 seed 生成地圖並從 start 走到 final node
- [x] 每次進入節點會正確扣除 food 並更新 visited_nodes
- [x] 事件選項 effect 會正確反映到 hp/food/ammo/medkits

### Phase C: 戰鬥與資源整合 (已完成 ✓)

**目標**: 戰鬥流程可與事件與資源系統連動，且具備 failure path 測試。

**任務清單**:
```
戰鬥整合:
├─ [✓] 1. 玩家行動 (Attack / Use Medkit)
├─ [✓] 2. 敵方回合與 damage_range 套用
├─ [✓] 3. combat_chance 觸發與戰鬥收斂
└─ [✓] 4. 資源耗損與補給事件交互驗證
```

**Gate 條件**:
- [x] Attack 必須消耗 ammo，ammo 不足時回傳可預期錯誤
- [x] Combat 在 enemy_hp<=0 或 player_hp<=0 時必定結束
- [x] 每個核心模組至少含 1 invalid input + 1 boundary + 1 failure path 測試

### Phase D: Meta 與平衡迭代 (進行中 🔄)

**目標**: 導入 run 外成長與基本平衡迴圈，形成可迭代原型。

**任務清單**:
```
Meta 與平衡:
├─ [⏳] 1. 定義 meta progression 資源與解鎖條件
├─ [⏳] 2. run 結束獎勵結算
├─ [✓] 3. run analytics log schema 與輸出驗證
├─ [✓] 4. event template system（catalog + deterministic generation）
├─ [✓] 5. 節點/敵人/事件機率調參
└─ [🔄] 6. balancing notes 完成，首輪 playtest protocol 進行中      ← 當前進行中
```

**Gate 條件**:
- [ ] meta progression 規則寫入 spec，並有對應資料欄位
- [ ] 同 seed 可重現同地圖，平衡調整不破壞可重現性
- [x] 至少完成 50 局 analytics log 紀錄（勝率、平均回合、死亡原因、decision trace）
- [x] 至少 1 個不可逆狀態信號已接入主循環，且死亡原因可歸因

---

## 🔥 本週聚焦 (當前 Sprint)

**Sprint 1** (2026/03/09 - 2026/03/15)

**目標**: 啟動 Phase D，建立可分析、可延展的原型資料層。

**任務清單**:
- [x] 補完 `specs/meta_progression.md`（4h）
- [x] 補完 `schemas/enemy_schema.json`（3h）
- [x] 補完 `schemas/node_schema.json`（3h）
- [x] 為三個 schema 各新增 2 筆範例資料（4h）
- [x] 建立 schema 驗證腳本草案（4h）
- [x] 建立 `src/` 狀態模型骨架（6h）
- [x] 實作 map 連線驗證與可達性檢查（5h）
- [x] 串接事件抽取與選項效果套用（6h）
- [x] 建立 deterministic run 測試（同 seed 同結果）（4h）
- [x] 串接戰鬥至事件觸發流程（6h）
- [x] 針對 ammo/medkit 失敗路徑補測（4h）
- [x] 產生 5 局可回放 run log，執行 Playability Gate 初驗（6h）
- [x] 調整事件壓力分布，讓每局壓力選擇 >= 3（6h）
- [x] 建立 run analytics schema 與輸出驗證（4h）
- [x] 建立 event template catalog 與 deterministic instantiation（6h）
- [x] 執行 balance metrics 蒐集（analytics 50 局）（6h）
- [x] 實作最小不可逆狀態（radiation）並接入 analytics（6h）
- [x] 補 interactive CLI warning 與 runtime invariant（6h）

**下一步**:
1. 依 `PLAYTEST_PROTOCOL.md` 與 human playtest log schema 執行第一輪人工 playtest
2. 對比 human regret / hesitation 與 machine `failure_analysis`
3. 規劃 run-end reward 與 meta progression state transition
4. 以受控實驗方式評估 explicit irreversible trade（例如 `max_hp` 交換生存）

**當前阻礙**:
- 無

**決策紀錄（本 Sprint）**:
- `trade` node 在 MVP 採 **event-only variant**（不做完整交易系統 UI/經濟）。

---

## 📊 待辦清單 (Backlog)

### 高優先 (P0)
- [ ] 定義 run state 序列化格式（save/load）
- [ ] 補齊 combat/resource failure-path tests
- [ ] 實作死亡原因結構化 run log

### 中優先 (P1)
- [ ] 補充 `event_schema.effects` 的 effect 欄位限制（可調資源白名單）
- [ ] 增加 map 生成限制（避免死路、保證可達終點）
- [ ] 建立 30 筆事件資料集初版

### 低優先 (P2)
- [ ] 加入難度等級（easy/normal/hard）
- [ ] 增加敵人類型特性（armor, dodge, special attack）
- [ ] 增加 run summary 輸出模板

---

## 🚫 不要做 (Anti-Goals)

❌ **Phase D 禁止**:
- 不要提前啟動 Steamworks / store page / achievements（理由：屬於派生目標）
- 不要先做精美 UI 或大量世界觀文本（理由：不直接驗證 v0.1 核心）
- 不要引入網路或多人功能（理由：超出本階段 Bounded Context）

---

## 🤖 AI 協作規則

**AI 在實作任何功能前，必須確認**:

1. 這項任務是否在「本週聚焦」或「下一步」中
2. 是否符合當前 Phase 的範圍
3. 是否命中 Anti-Goals

**如果不符合上述條件**:
- 先提出偏離點（scope / phase / anti-goal）
- 提供 A/B/C 選項（本週做、下週做、放入 Backlog）
- 待確認後才改動規格或程式

---

## 🧭 真相模型（Truth Model）

- `PLAN.md`：Phase / Milestone / Gate truth（策略層）
- `tasks/TASKS.md`：Sprint / Execution truth（執行層）
- 發生衝突時：先更新 `PLAN.md` 的 Gate/Phase，再同步 `TASKS.md` 任務狀態。

---

## 🎯 Gate 與驗收標準

### Phase A Gate（已完成）

**功能完整性**:
- [x] `specs/` 六份規格皆有可執行規則敘述
- [x] `schemas/` 三份 schema 皆可驗證，且有樣本資料可過驗證

**品質完整性**:
- [x] 建立最小驗證腳本，可一鍵檢查所有 schema 與樣本
- [x] schema 驗證失敗時有明確錯誤訊息（檔名 + 欄位）

### Phase B Gate（已完成）

**主循環可執行**:
- [x] 單局可從 start 走到 final 或死亡
- [x] 同 seed 可重現相同路徑與資源結果

### Phase C Technical Gate（已完成）

**戰鬥/資源整合**:
- [x] Attack 消耗 ammo，ammo 不足時回傳可預期錯誤
- [x] Combat 在 enemy_hp<=0 或 player_hp<=0 時必定結束
- [x] 每個核心模組至少含 1 invalid input + 1 boundary + 1 failure path 測試

### Phase C Playability Gate（已完成）

**玩法驗證**:
- [x] 單局中至少出現 3 次有壓力的選擇
- [x] 不同路線明顯導致不同資源狀態或結局
- [x] 玩家可從 run log 回推死亡原因，不是純靠運氣
- [x] 單局結束後有「想再跑一局」的可觀察訊號（至少 3/5 測試局）

### Prototype Metrics Gate（v0.1）

- [x] 完整 run 完成率：每局均以 victory 或 death 收斂
- [x] 選路分歧有效性：不同路線 outcome signature 有顯著差異（`distinct_outcome_signatures >= 2`）
- [x] 可歸因死亡率：死亡局可由 decision/run log 解釋（目前 100%）
- [x] 壓力節點密度：每局 `pressure_count >= 3`

---

## 📝 已知問題

| ID | 問題 | 嚴重程度 | 狀態 | 負責人 |
|---|---|---|---|---|
| SPEC-001 | `meta_progression.md` 空白 | P0 | ✓ 已修復 | GavinWu |
| SCHEMA-001 | `enemy_schema.json` 空白 | P0 | ✓ 已修復 | GavinWu |
| SCHEMA-002 | `node_schema.json` 空白 | P0 | ✓ 已修復 | GavinWu |

---

## 🔧 技術債務追蹤

| ID | 債務描述 | 預計償還時間 | 優先級 |
|---|---|---|---|
| DEBT-001 | `event_schema.effects` 未限制欄位，易出現非法 key | Phase B | P1 |
| DEBT-002 | 尚無統一的 run log 格式，後續調參比對成本高 | Phase C | P1 |

---

## 📅 里程碑

| 里程碑 | 目標日期 | 狀態 | 交付物 |
|---|---|---|---|
| M1: 規格與 schema 凍結 | 2026/03/15 | 🔄 | 完整 specs + schemas + sample data |
| M2: 可跑通單局主循環 | 2026/03/29 | ⏳ | CLI run loop 原型 |
| M3: 戰鬥與資源整合完成 | 2026/04/12 | ⏳ | 可測試 combat/resource 模組 |
| M4: Meta 與首輪平衡 | 2026/05/01 | ⏳ | 可迭代遊玩原型 v0.1 |
| M5: Steam 上架準備完成 | 2026/06/01 | ⏳ | Steamworks 設定、商店頁素材、首版可發布 build |

---

## 📦 Steam 產品追蹤（不阻塞 Prototype 主線）

- Steam 任務僅在 M1-M4 gate 通過後提升優先級。
- 詳細清單維護於 `tasks/task_steam_release.md`。

---

## 🔄 變更歷史

| 日期 | 變更內容 | 原因 |
|---|---|---|
| 2026/03/09 | 建立 Ashfall 專案 PLAN 初版（依 specs/schemas + governance 規範） | 讓後續開發先有可執行路線與 Gate |
| 2026/03/09 | 完成 Phase A 文件補齊（meta progression、enemy/node schema、samples、驗證腳本）並切換至 Phase B | 排除空白規格阻塞，開始核心模擬引擎 |
| 2026/03/09 | 完成 Phase B-B1 狀態模型骨架（`src/state_models.py`, `src/run_engine.py`） | 讓 B2/B3 可基於一致資料結構開發 |
| 2026/03/09 | 明確記錄最終目標為 Steam 上架，新增 Steam 準備里程碑 | 將產品方向固定為可發行路線 |
| 2026/03/09 | 新增 Steam 上架任務拆解（`tasks/task_steam_release.md`），並推進 B2/B3（map 驗證 + 事件流程骨架） | 將發行任務與核心迴圈並行推進 |
| 2026/03/09 | 新增 `combat_engine` 與 smoke 測試，完成 B3 與 C1 初版 | 先打通事件->戰鬥最小路徑，再補 deterministic 與 failure-path |
| 2026/03/09 | 完成 deterministic run 驗證並關閉 Phase B Gate，切換至 Phase C | 主循環已可穩定重現，開始戰鬥整合與失敗路徑補強 |
| 2026/03/09 | 新增 Phase C Playability Gate，並確定 trade node 採 event-only variant（MVP） | 避免只做 technical correctness，強制驗證可玩性 |
| 2026/03/09 | 事件系統已串接 combat_chance -> 自動戰鬥流程，並通過 smoke/deterministic 驗證 | 打通事件與戰鬥閉環，開始補齊 failure-path 與可玩性驗證 |
| 2026/03/09 | 導入雙層真相模型（PLAN=策略層，TASKS=執行層），並對齊 Phase C Gate 勾選狀態 | 消除 PLAN/TASKS 漂移，避免 AI 誤讀進度 |
| 2026/03/09 | 完成 failure-path tests 與 Playability v1（5 runs）；結果為 3/4 gate 通過（壓力選擇數未達標） | 先建立可重跑的玩法驗證基線，再針對壓力密度做調整 |
| 2026/03/09 | 完成 C6 壓力密度調整與 Playability v2；Phase C Gate 全數通過，切換至 Phase D | 原型驗證 contract 的三項核心指標已達標，進入 meta/balance 迭代 |
| 2026/03/09 | 新增 `SYSTEM_CONSTRAINTS.md`、`schemas/run_analytics_schema.json`、`specs/event_template_system.md` | 鎖定 state contract、防止 AI 漂移，並提升事件內容熵策略 |
| 2026/03/09 | 完成 D3：`output/analytics/` 正式輸出與 `validate_run_analytics.py` 驗證腳本 | 讓後續平衡與 decision trace 具備機器可驗證資料契約 |
| 2026/03/09 | 完成 D4：事件模板目錄與 deterministic instantiation 接入 playability pipeline | 提升內容熵，同時維持 seed 可重現性與 event schema 契約 |
| 2026/03/09 | 完成 D5：20 局 analytics balance sampling 與 route-family metrics 摘要 | 把「可玩」進一步轉成可量化平衡資料，並定位下一步壓力調整方向 |
| 2026/03/09 | 新增 `PLAYTEST_PROTOCOL.md`，定義 v0.1 第一輪人工測試流程與成功標準 | 補上 machine gate 之外的人類玩法驗證流程，避免只看系統數據 |
| 2026/03/09 | 完成 D6：導入 `radiation` 不可逆狀態、travel attrition、analytics 欄位與死亡歸因 | 將「短期資源壓力」升級為「長期代價壓力」，強化 route gamble 感 |
| 2026/03/09 | 新增 weighted regret/blame analysis 與 human playtest log 契約 | 避免單點虛假歸因，並讓 Blind CLI test 能與 machine analytics 直接對照 |
| 2026/03/09 | 完成 D7：發布 `BALANCING_NOTES_v0_1.md`，總結 radiation 後的平衡結論與下一步實驗順序 | 將 machine metrics 轉成明確設計決策，避免在 UI 或新系統前失去焦點 |
| 2026/03/09 | 補 interactive CLI warning、50-run balance sample、runtime invariant 與 gameplay gate CI | 優先修復 repo 信任層與 state correctness，而不是堆疊新功能 |
