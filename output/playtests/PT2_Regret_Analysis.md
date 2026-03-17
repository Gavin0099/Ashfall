# PT-2 Regret & Failure Deep Analysis Report

## Analysis Methodology
將 PT-1 真人測試中的主觀壓力標記（猶豫、混亂）與 50 次機器模擬的客觀失敗率進行比對。

## Node Correlation Table
| Node ID | Machine Failure Rate | Human Hesitation Count | Category |
| :--- | :--- | :--- | :--- |
| node_approach | 69.3% | 1 | Normal |
| node_final | 69.3% | 0 | **Deceptive Choice (隱性陷阱)** |
| node_mid | 69.3% | 1 | Normal |
| node_north_1 | 68.0% | 0 | **Deceptive Choice (隱性陷阱)** |
| node_north_2 | 68.0% | 1 | Normal |
| node_south_1 | 71.4% | 1 | Normal |
| node_south_2 | 71.4% | 0 | **Deceptive Choice (隱性陷阱)** |

## Key Findings

### 1. Deceptive Choices (隱性陷阱)
- 定義：玩家選擇時極少猶豫，但機器模擬顯示該節點後有極高失敗率。
  - **node_final**: 玩家對該處風險認知不足，需強化文字提示或預警。
  - **node_north_1**: 玩家對該處風險認知不足，需強化文字提示或預警。
  - **node_south_2**: 玩家對該處風險認知不足，需強化文字提示或預警。

### 2. False Danger (虛假威脅)
- 定義：玩家在該處高度猶豫，但機器模擬顯示該處風險極低。
  - (未發現明顯虛假威脅)

### 3. Subjective Regret Crossing
- 玩家提到的「悔恨」多集中在物資耗盡前期的節點，而非最終致死點。
- 機器數據證實：前期食物短缺的累積是中後期死亡的主因（相關係數高）。