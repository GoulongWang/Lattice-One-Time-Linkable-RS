# LRS 實作與效能分析 — 實驗規劃

> 目標：仿照 *PrimeHE: The First Leveled Homomorphic Encryption Scheme over NTRUPrime*（Lin & Tso, NCCU）第 5.2 + 6 節的「實作與效能分析」寫法，為你的碩論〈Post-Quantum Linkable Ring Signatures Based on Lattice〉產出對等的章節所需的全部實驗。本文件**只規劃要做什麼實驗**，不含程式執行。

---

## 0. 現況盤點（你已經有的）

| 項目 | 現況 | 對應 PrimeHE |
|---|---|---|
| 演算法實作 | `lrs.py`：Setup / KeyGen / Sign / Verify / Link（Alg 1–5），R_q = Z_q[X]/(X^N+1) | 已對應 Section 6.1「實作核心演算法」|
| 正確性測試 | `test_correctness.py`：簽章驗證、竄改拒絕、同/異 key linking、size 比對 | 對應 6.3「Empirical Correctness 100%」|
| 效能 benchmark | `benchmark.py`：固定參數、變動 n（目前 1/8/32），量 KeyGen/Sign/Verify + 三種 size | 對應 Table 2 雛形 |
| 參數集 | **僅一組**（Table 2：N=1024, q=2³²−99, h=1, l=4, v=1, k=6, κ=45, β=1, σ=31680） | **缺**：PrimeHE 有 5 組跨安全強度 |

**三個主要缺口**（也就是這次要補的實驗）：
1. **多組安全參數表**（仿 PrimeHE Table 1）— 目前只有一組。
2. **環尺寸 scaling 完整化**（仿 Table 2）— 補 Link 欄、擴大 n 範圍、加統計量。
3. **操作分解 / 瓶頸分析**（仿 6.3）— 目前只有定性討論，缺量化拆解。

> 註：依你的決定，本輪**不做** lattice estimator / Core-SVP 安全強度估計；參數表中的「安全等級」欄位先留 placeholder（TBD），日後補。

---

## 1. 目標章節結構（對映 PrimeHE）

你的論文「實作與效能分析」章節建議切成 4 小節，逐一對映 PrimeHE：

| 你的小節 | 內容 | PrimeHE 對映 |
|---|---|---|
| X.1 參數選擇 | 多組參數集 + 正確性約束驗證（+ 安全欄位 TBD） | 5.2 / Table 1 |
| X.2 實驗設定 | 語言、硬體、固定參數、統計方法 | 6.1 |
| X.3 效能結果 | 環尺寸 scaling 時間/大小表 | 6.2 / Table 2 |
| X.4 討論與分析 | 正確性、操作間成本比較、瓶頸定位 | 6.3 |

---

## 2. 實驗 A — 多組安全參數表（仿 Table 1）

**目的**：證明方案可在多個安全強度下實例化，而非只跑一組 demo。這是 PrimeHE 與你目前最大的差距。

**做法**：
1. 設計 **3–5 組參數集**，命名比照 PrimeHE（如 `lrs-light` / `lrs-128` / `lrs-192`，或用 N 命名 `lrs1024` / `lrs2048`）。
2. 調整安全強度的主要旋鈕：**N（多項式維度）** 與 **module rank k, l**；q 隨之重選（必須維持 `q ≡ 5 (mod 8)` 使 Lemma 1 partial-splitting 成立、且 q 足夠大滿足 rejection / 範數約束）。
3. 每換一組參數，**必須重算** σ、T₁=κ√(lN)、T₂=κ√(kN)、以及拒絕常數 M₁、M₂，並確認 M₁·M₂ 落在可接受重試次數（PrimeHE 對應「correctness constraints」檢查）。
4. 對每組驗證正確性約束成立（見實驗 C 的 correctness gate）。

**表格樣板（Table A）**：

| 參數集 | N | ⌈log₂ q⌉ | h | l | v | k | κ | β | σ | M₁·M₂(期望重試) | 安全等級(bits) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| lrs-light | … | … | 1 | … | 1 | … | … | 1 | … | … | TBD |
| lrs-128 | 1024 | 32 | 1 | 4 | 1 | 6 | 45 | 1 | 31680 | ~11 | TBD |
| lrs-192 | … | … | 1 | … | 1 | … | … | 1 | … | … | TBD |

> PrimeHE 的對應欄是 (p, log₂q, w, d=2p, β, Core-SVP bits)；你的對應物是 (N, log₂q, module ranks, σ, 安全 bits)。

**需要的 code 修改**：把 `lrs.py` 開頭那組硬編碼常數抽成 `PARAM_SETS = {"lrs-128": {...}, ...}`，讓 `setup/keygen/...` 接受一個 params dict。

---

## 3. 實驗 B — 環尺寸 scaling 效能表（仿 Table 2）

**目的**：呈現各操作隨環大小 n（ring members）的時間與簽章大小成長，這是環簽章效能分析的核心圖表。

**做法**：
1. 固定一組主參數集（建議 `lrs-128`，即現有 Table 2 參數）。
2. 變動 **n = 1, 2, 4, 8, 16, 32, 64**（PrimeHE 是換參數集當欄，你的環簽章天然多了 n 這個軸 — 更有看頭，建議用 n 當主欄）。
3. 量測五個操作：**KeyGen、Sign、Verify、Link、（可選）Setup**。
   - **新增 Link 欄**：目前 benchmark 缺，必加（PrimeHE Add/Mult 對映 → 你的 Verify/Link）。
4. 量測三種大小：**PK、SK、Signature**（已有；Signature 隨 n 線性成長是重點）。
5. 統計：每點重複 ≥ 8 次（Sign 因 rejection 很 noisy，建議 ≥ 16 次），報 **中位數 + 標準差**（或 min/median/max）。KeyGen 與 n 無關，可單獨多跑（現有 KG_REPS=30 即可）。

**表格樣板（Table B）**：

| n（ring size） | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|---|
| KeyGen (ms) | | | | | | | |
| Sign (ms) | | | | | | | |
| Verify (ms) | | | | | | | |
| Link (ms) | | | | | | | |
| PK (KB) | | | | | | | |
| SK (KB) | | | | | | | |
| Signature (KB) | | | | | | | |

**預期觀察（供 X.4 討論引用）**：
- Verify、Signature 大小 **隨 n 線性**（一次 AOS ring pass）。
- Sign 由 **rejection sampling 重試** 主導、雜訊大。
- KeyGen 幾乎與 n 無關。

**需要的 code 修改**：`benchmark.py` 加 Link 計時欄、把 n 清單擴成 1–64、輸出標準差；`sizes_bits` 已支援 n。

---

## 4. 實驗 C — 操作分解 / 瓶頸分析（仿 6.3）

**目的**：把 PrimeHE 6.3「Add vs Mult 成本差 ~1000×、KeyGen evk 是瓶頸」這種量化洞見，對應到你的方案。

**三個子實驗**：

**C1. 正確性 gate（仿 "100% success rate"）**
對**每一組參數集 × 每個 n**，跑 R 次（如 R=100）完整 Sign→Verify→Link，統計成功率。目標：全數 100%，用以實證你 Theorem 1 的 bounded-norm / 約束。輸出一句「across all parameter sets and ring sizes, Verify and Link succeeded 100%」。

**C2. Rejection sampling 行為**
在 `sign` 內加計數器，記錄每次成功簽章前的**重試次數**，畫分佈/平均，並與理論 M₁·M₂ 比對（驗證實作的拒絕率符合預期）。這是你 Sign 雜訊與成本的根因。

**C3. 子程序時間佔比（瓶頸定位）**
在 Sign / Verify 內對主要子步驟計時（如 `poly_mul` 累計時間、commitment、ring-chain hash、Gaussian 取樣），report 各佔比。對映 PrimeHE「multiplication 由 tensor product + key-switch 主導」的拆解。預期 `poly_mul`（negacyclic convolution）為主瓶頸 → 自然導出「未來用 NTT / C/Rust 可加速 1–2 個數量級」的結論（你 README 已有此論點，這裡用數據支撐）。

**表格/圖樣板（Table C）**：

| 子程序 | Sign 佔比 (%) | Verify 佔比 (%) | 備註 |
|---|---|---|---|
| poly_mul（環乘法） | | | 預期主瓶頸 |
| Gaussian 取樣 | | | |
| commitment（MLWE/MSIS） | | | |
| ring-chain hash（SHAKE-256） | | | |
| rejection 檢查 | | | |

**需要的 code 修改**：在 `lrs.py` 加輕量 instrumentation（全域計數器 / `time.perf_counter` 累加），或包一層 profiler；C1 直接擴充 `test_correctness.py` 成迴圈版。

---

## 5. 實驗設定（仿 6.1，章節 X.2 要寫的內容）

照 PrimeHE 6.1 的揭露標準，論文裡務必交代：
- **語言/環境**：Python 3 + NumPy 參考實作；明說「目的是驗證正確性與相對成本，非絕對速度」（PrimeHE 對 SageMath 也是這樣定位）。
- **硬體**：CPU 型號/頻率、RAM、OS（`benchmark.py` 已存 `platform.platform()`；建議再補 CPU 型號與 RAM）。PrimeHE 寫的是 Intel i7-9750H @2.60GHz。
- **統計方法**：重複次數、取中位數、固定隨機種子（你已用 `default_rng(2024+n)`）。
- **固定設定**：例如 module ranks、β=1 ternary、σ 來源（σ=α·T）。

---

## 6. 程式修改清單（工程 checklist）

按相依順序：
1. **參數化**：`lrs.py` 常數 → `PARAM_SETS` dict；`setup/keygen/sign/verify/link/sizes_bits` 接收 params。（實驗 A 前置）
2. **新參數集**：定義 3–5 組，逐組重算 σ、M₁、M₂、重選 q（q≡5 mod 8）。
3. **Link 計時**：`benchmark.py` 加 Link 欄。
4. **n 範圍 + 統計量**：n=1…64；輸出中位數與標準差。
5. **Instrumentation**：retry 計數器（C2）、子程序計時（C3）。
6. **正確性迴圈**：`test_correctness.py` → 全參數集 × 多 n × R 次（C1）。
7. **製表**：`make_table.py` 擴充輸出 Table A/B/C（md + png + csv）。

---

## 7. 注意事項 / 易踩雷

- **換 N 必連動**：σ、T₁、T₂、M₁、M₂ 全要重算；q 要重選且維持 `q ≡ 5 (mod 8)`（否則 Lemma 1 challenge 差可逆性失效）。不要只改 N 不改其他。
- **Sign 時間雜訊大**：rejection 重試是幾何分布，務必多次取中位數，否則表格不穩。
- **記憶體 / 大 n**：n=64 時簽章 ~1.4 MB 量級且 ring-chain 變長，注意時間/記憶體（PrimeHE 也遇到 OOM，可比照在討論裡誠實揭露）。
- **安全欄位 TBD**：本輪不跑 estimator，表格安全 bits 留 placeholder，並在文中註明「concrete security estimation 留待後續以 lattice-estimator 評估」。
- **定位措辭**：跟 PrimeHE 一致，強調數字是「未最佳化 pure-NumPy 參考實作的相對 scaling」，避免被審查者當絕對效能比較。

---

## 8. 建議執行順序

1. 工程修改 1–2（參數化 + 參數集）→ 跑 **實驗 A** 出 Table A。
2. 工程修改 3–4 → 跑 **實驗 B** 出 Table B（主圖表）。
3. 工程修改 5–6 → 跑 **實驗 C**（C1 正確性 → C2 重試 → C3 瓶頸）。
4. 工程修改 7 製表 → 寫章節 X.1–X.4。
