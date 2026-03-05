# Linear ↔ PLAN.md 同步策略：Source of Truth 定義

> **適用範圍**: 使用 `governance_tools/linear_integrator.py` 進行 Linear 整合的專案
> **最後更新**: 2026-03-05

---

## 核心原則：PLAN.md 為主、Linear 為從

```
PLAN.md  ──(同步到)──▶  Linear Issues
   │                         │
   │◀──(狀態回寫，人工觸發)───┘
   │
   └── Git commit 觸發 freshness check
```

**PLAN.md 是 Single Source of Truth**，原因：

| 考量點 | PLAN.md | Linear |
|--------|---------|--------|
| 版本控制 | ✅ Git 歷史可查 | ❌ 無 diff 追溯 |
| 離線存取 | ✅ 本地檔案 | ❌ 需要網路 |
| AI 可讀 | ✅ Markdown 直讀 | ❌ 需要 API 呼叫 |
| 視覺化管理 | ❌ 純文字 | ✅ Kanban/Backlog |
| 團隊協作 | ❌ 較弱 | ✅ 評論、指派、通知 |

**結論**：PLAN.md 定義「要做什麼」，Linear 負責「可見性與協作」。

---

## 操作規則

### 規則 1：新任務先寫 PLAN.md

```
❌ 不要做：直接在 Linear 建 Issue → 再嘗試反寫 PLAN.md
✅ 正確做法：在 PLAN.md 加任務 → 執行 --sync 推送到 Linear
```

### 規則 2：狀態更新以 PLAN.md 為準

- 任務完成 → 在 PLAN.md 標記 `[x]` → commit → （可選）手動在 Linear 關閉 Issue
- **不要**只在 Linear 關閉，而不更新 PLAN.md

### 規則 3：Linear ID 寫回本地

`--sync` 執行後，`linear_integrator` 會在任務後面加 `[LINEAR:XXX-123]` 標記。
這個標記：
- 防止重複建立相同 Issue
- 提供快速跳轉連結
- 是雙向連結的唯一橋梁

### 規則 4：衝突解法

| 情境 | 解法 |
|------|------|
| PLAN.md 有任務，Linear 沒有 | 執行 `--sync` |
| Linear 有 Issue，PLAN.md 沒有 | 手動在 PLAN.md 補記，再標記 LINEAR ID |
| 兩邊狀態不一致 | 以 PLAN.md 為準，手動更新 Linear |
| Linear Issue 被刪除 | 移除 PLAN.md 中的 `[LINEAR:XXX-123]` 標記，下次 `--sync` 會重建 |

---

## 不支援的功能（明確邊界）

- ❌ Linear → PLAN.md 自動反寫（避免雙向同步競爭）
- ❌ Linear 上的評論/附件同步到本地
- ❌ 子 Issue / Epic 階層對應（PLAN.md 是平面清單）
- ❌ 多 Team 批次同步（每次指定單一 `--team-id`）

---

## 工具使用流程

```bash
# 1. 查看可用 Team
python governance_tools/linear_integrator.py --list-teams

# 2. 同步未完成任務到 Linear（含 0.5s 批次間隔，避免 rate limit）
python governance_tools/linear_integrator.py --sync --team-id <TEAM_ID>

# 3. CI/dashboard 用 JSON 輸出
python governance_tools/linear_integrator.py --sync --team-id <TEAM_ID> --format json
```

---

## 安全性

`linear_integrator` 在送出前會掃描 Issue title 與 description，若偵測到以下類型會**拒絕送出**：

| 類型 | 範例 |
|------|------|
| `API_KEY` | `lin_api_*`, `sk-*`, `xoxb-*` |
| `CREDENTIAL` | `password=xxx`, `token: yyy` |
| `PRIVATE_KEY` | `-----BEGIN PRIVATE KEY-----` |
| `POSSIBLE_SECRET` | 40+ 字元 base64 blob |

若誤觸（例如正常的 base64 ID），使用 `--format json` 查看具體錯誤後，
清理任務描述中的可疑字串即可。

---

## 相關文件

- [PLAN.md](../PLAN.md) — 主計畫文件
- [governance_tools/linear_integrator.py](../governance_tools/linear_integrator.py) — 工具原始碼
- [governance/02_workflow.md](../governance/02_workflow.md) — 整體工作流程
