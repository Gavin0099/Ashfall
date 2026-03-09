# Demo — 治理在運作時長什麼樣子

> 用 5 分鐘看完這個，你就知道這 3 個文件能做什麼。
>
> 場景：你在開發一個 todo 應用，目前在 Phase 1，本週目標是完成基本 CRUD。

---

## 你的 PLAN.md（填好之後）

```markdown
# PLAN.md — Todo App

> 最後更新: 2026-03-09

## 1. 專案概述
目標: 一個簡單的個人 todo 管理工具
技術棧: Python / FastAPI

## 2. 當前狀態
當前階段: Phase 1 — 基本 CRUD

### 本週聚焦
- [ ] GET /todos — 列出所有 todo
- [ ] POST /todos — 新增 todo
- [ ] DELETE /todos/{id} — 刪除 todo

### 反目標（Anti-Goals）
- 不做: 使用者登入（Phase 2 才做）
- 不做: 效能優化
```

---

## 沒有治理時

```
你: 幫我實作 todo app 的登入功能

AI: 好的！我來實作使用者登入。需要以下幾個步驟：
    1. 安裝 python-jose 做 JWT...
    2. 建立 User 資料表...
    3. 實作 /auth/login endpoint...

    [開始寫程式]
```

**問題**: AI 不知道「登入是 Phase 2，現在不做」。它直接開始做，還引入了新的依賴。

---

## 有治理時

```
你: 幫我實作 todo app 的登入功能

AI: [Governance Contract]
    PLAN     = Phase 1 / 基本 CRUD / 尚未開始
    PRESSURE = SAFE (0/200)

    [Decision Summary]
    登入功能在 PLAN.md Anti-Goals 中標記為「Phase 2 才做」，
    不在本週範圍內。

    目前本週聚焦還有 3 個未完成：
    - GET /todos
    - POST /todos
    - DELETE /todos/{id}

    選項：
    A) 繼續本週目標（建議）
    B) 將登入移入本週，但需調整計畫並確認影響
    C) 先做登入，暫時偏離計畫（需你明確授權）

    你的決定？
```

**效果**: AI 主動確認優先級，給你選擇，而不是直接開做。

---

## 多輪對話後的狀態管理

```
（3 天後，新的對話）

你: 繼續上次的工作

AI: [Governance Contract]
    PLAN     = Phase 1 / 基本 CRUD / GET+POST 已完成
    PRESSURE = SAFE (23/200)

    [Decision Summary]
    根據 PLAN.md 和 memory/01_active_task.md：
    - ✅ GET /todos — 完成
    - ✅ POST /todos — 完成
    - ⬜ DELETE /todos/{id} — 尚未開始

    建議從 DELETE /todos/{id} 繼續。要開始嗎？
```

**效果**: 跨 session 的狀態被保留在 `memory/01_active_task.md`。AI 不需要你重新說明現在在哪裡。

---

## 架構邊界違反時

```
你: 在 CRUD API 裡直接呼叫外部 API 取使用者資料比較快

AI: [Governance Contract]
    PLAN     = Phase 1 / 基本 CRUD / DELETE 進行中
    PRESSURE = SAFE (23/200)

    [Decision Summary]
    ⚠️ 架構紅線：PLAN.md §架構紅線 定義「外部 API 呼叫不能進入 CRUD handler 層」。

    這個做法會：
    - 讓 handler 直接依賴外部服務（難以測試）
    - 違反目前的架構邊界設定

    建議：在 Service 層建立 UserService，讓 handler 呼叫 Service。
    這樣符合架構規範，也容易 mock 測試。

    要我照這個方式實作嗎？
```

**效果**: AI 在動手之前，主動指出架構問題並提供合規方案。

---

## 你看到的核心差異

| | 沒有治理 | 有治理 |
|--|---------|--------|
| AI 知道現在在哪個 Phase？ | ✗ | ✅ |
| 超出範圍的任務 | 直接做 | 詢問後再決定 |
| 跨 session 繼續工作 | 需重新說明 | 自動讀取狀態 |
| 架構邊界保護 | 看 AI 心情 | PLAN.md 明確定義 |

---

## 試試看

1. 填好 `PLAN.md`（5 分鐘）
2. 告訴 AI：`請先讀 SYSTEM_PROMPT.md 和 PLAN.md，然後告訴我你的 Governance Contract`
3. 看 AI 輸出是否出現 `[Governance Contract]` 區塊
4. 試著要求一個**不在本週聚焦的功能**，觀察 AI 怎麼反應

如果步驟 3 沒有出現 contract → 確認 SYSTEM_PROMPT.md 有被 AI 讀到。
