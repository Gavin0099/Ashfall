# PLAN.md — Ashfall

> **專案類型**: 單機 roguelite 生存策略遊戲原型
> **技術棧**: Markdown Specs + JSON Schema + Python (planned runtime)
> **複雜度**: L2
> **預計工期**: 2026/03/09 ~ 2026/05/01
> **最後更新**: 2026-03-17
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
├─ [✓] Phase v0.3: Meta Progression 擴展階段 (2026-03-17 完成)
├─ [✓] Phase v0.4: Product Specialization 產品特化 (2026-03-17 完成)
├─ [✓] Phase v0.5: Character Archetypes 角色職業系統 (2026-03-17 完成)
├─ [✓] Phase v0.6: Advanced Mechanics & World Depth 進階機制與世界深度 (2026-03-17 完成)
├─ [✓] Phase v0.7: Meta Progression Depth & Polish 系統深度與打磨 (2026-03-17 完成)
├─ [✓] Phase v0.8: Content Pack & Final Polish 內容擴展與最終打磨 (2026-03-17 完成)
├─ [✓] Phase v0.9: Narrative Depth & Quest Chains 劇情深度與任務鏈 (2026-03-17 完成)
├─ [✓] Phase v1.0: Advanced Character System 進階角色系統 (2026-03-17 完成)
├─ [✓] Phase v1.1: Character Factory Framework 角色生成工廠 (2026-03-17 完成)
├─ [✓] Phase v1.2: Perks & Dynamic Progression 成長系統 (2026-03-17 完成)
├─ [✓] Phase v1.3: Durability & Repair System 耐久度與修復系統 (2026-03-17 完成)
├─ [✓] Phase v1.4: Ruins & Camp Special Nodes 遺蹟與營地系統 (2026-03-17 完成)
└─ [ ] Phase 7.0: Environment & Resource Tuning 環境威脅調整與資源優化 (進行中)
```

**當前階段：Phase 7.0 進行中 — 目標：解決勝率過低問題，最佳化輻射公式與廢料產出。**
