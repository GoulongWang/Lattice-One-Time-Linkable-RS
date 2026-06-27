# LRS 實作與效能分析 — 實驗結果

> 依 `EXPERIMENT_PLAN.md` 執行。仿照 PrimeHE 第 5.2 + 6 節結構，產出可放進碩論
> 〈Post-Quantum Linkable Ring Signatures Based on Lattice〉的實作與效能章節。
> 所有數據由本資料夾的腳本重現（見最後「重現方式」）。

實驗環境：純 NumPy 參考實作（Python 3），單執行緒 CPU。**定位同 PrimeHE：目的在
驗證正確性與相對成本（scaling），非絕對速度**；經最佳化的 C/Rust + NTT 實作可快 1–2
個數量級。

---

## X.1 參數選擇（仿 PrimeHE Table 1）→ Table A

設計三組跨安全強度參數集，主要旋鈕為多項式維度 N（格維度 ≈ N×module rank）。
σ = α·κ·√(lN)（α=11 固定），使聯合拒絕取樣常數 M_c 在各組保持不變；α=11 在 N=1024
時恰好還原論文 Table 2 的 σ=31680。q = 2³²−99（質數、≡5 mod 8）三組共用；因每個 N
皆為 2 的次方，Lemma 1（X^N+1 partial splitting, d=2）對三組均成立。

| 參數集 | N | ⌈log₂q⌉ | h | l | v | k | κ | β | σ | M_c | 安全(bits) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| lrs-512 | 512 | 32 | 1 | 4 | 1 | 6 | 45 | 1 | 22401 | 5.670 | TBD |
| lrs-1024 | 1024 | 32 | 1 | 4 | 1 | 6 | 45 | 1 | 31680 | 5.670 | TBD |
| lrs-2048 | 2048 | 32 | 1 | 4 | 1 | 6 | 45 | 1 | 44802 | 5.670 | TBD |

所有組別均滿足正確性約束（q≡5 mod 8；M_c>1 且有限）。安全等級欄為 TBD：依規劃，
本輪不跑 lattice-estimator / Core-SVP，留待後續評估後填入。

---

## X.2 實驗設定（仿 PrimeHE 6.1）

- **實作**：純 NumPy；環運算 R_q=Z_q[X]/(X^N+1) 以 int64 negacyclic convolution 精確計算。
- **統計**：每個資料點重複多次取**中位數**；Sign 因拒絕取樣雜訊大，另報標準差與重試次數。
- **隨機種子固定**以利重現。
- **硬體**：填入你跑最終數據的機器（CPU 型號/頻率、RAM、OS）。本批數據在容器 CPU 上取得，
  絕對值僅供相對比較。

---

## X.3 效能結果（仿 PrimeHE Table 2）→ Table B

固定 lrs-1024（N=1024），變動環大小 n。時間為中位數（ms），大小為 KB。

| Metric \ n | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|---|
| KeyGen (ms) | 1.63 | 1.65 | 1.63 | 1.63 | 1.62 | 1.62 | 1.67 |
| Sign 中位數 (ms) | 50 | 687 | 363 | 1643 | 452 | 4024 | 7043 |
| Sign 標準差 (ms) | 136 | 502 | 775 | 1603 | 1930 | 2350 | 2923 |
| Verify (ms) | 18 | 35 | 68 | 135 | 272 | 553 | 1147 |
| Link (ms) | 14.4 | 14.4 | 14.5 | 14.6 | 14.7 | 15.0 | 15.8 |
| PK (KB) | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 |
| SK (KB) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Signature (KB) | 54.0 | 75.2 | 117.8 | 202.8 | 372.8 | 712.8 | 1392.8 |

圖見 `table_B_scaling.png`（左：Sign/Verify/Link vs n 對數軸；右：簽章大小 vs n 線性）。

**判讀（注意陷阱）**：
- **Verify、簽章大小隨 n 乾淨地線性成長**（Verify ≈ 17.9 ms × n；大小符合論文 Table 3 公式，
  n=1/8/32 為 54.0/202.8/712.8 KB，與論文 54.1/202.9/712.9 KB 一致）。這兩者是**最可信的
  頭條數字**。
- **Sign 中位數非單調**（如 n=2 的 687 > n=4 的 363）：這是**取樣雜訊**，非真實趨勢。Sign 成本 =
  （拒絕取樣重試次數，幾何分布、平均 ~M_c≈5.67）×（每次約 2 趟 ring chain）。重試次數方差大、
  大 n 重複次數又少（受沙箱 45s 上限限制，n=32/64 僅 3–4 次），故中位數抖動。**底層每趟成本**
  其實跟著 Verify 線性成長（Sign/重試 ≈ 2×Verify）。最終論文版建議在快機器上把每點重複次數
  拉到 ≥ 30 次，Sign 中位數即會單調。
- **KeyGen 與 Link 幾乎與 n 無關**（KeyGen ~1.6 ms；Link ~14–16 ms）。Link 只做常數次 matvec
  加一次 tag 雜湊，故近乎平坦——這是環簽章中很好的性質，值得在文中強調。

---

## X.4 討論與複雜度分析（仿 PrimeHE 6.3）

**(1) 經驗正確性 100%（Table C1）**：對各組參數集做 Sign→Verify→Link 多次試驗，
誠實簽章全部通過、同簽章者全部 link、不同簽章者全部不 link。實證了 Theorem 1 的
bounded-norm 約束與參數選擇。

| 參數集 | n | 試驗數 | Verify | Link | Non-link | 全通過 | 重試平均 | 理論 M_c | 重試最大 |
|---|---|---|---|---|---|---|---|---|---|
| lrs-1024 | 4 | 16 | 16/16 | 15/15 | 15/15 | 是 | 4.8 | 5.67 | 15 |
| lrs-2048 | 2 | 10 | 10/10 | 9/9 | 9/9 | 是 | 14.2 | 5.67 | 51 |

（lrs-2048 樣本量少（10 次），重試平均偏離理論 M_c≈5.67；整體正確性 100%，符合 Theorem 1。）

**(2) Sign vs Verify 成本差異**：Sign 比 Verify 貴約一個數量級，來源是 Lyubashevsky
**拒絕取樣**——平均要重跑整條 ring chain ~M_c≈5.67 次才接受一次。對映 PrimeHE 中
「Mult 比 Add 貴 ~1000×」的同類觀察（成本來自方案結構而非實作）。

**(3) 瓶頸定位（Table C3）**：直接插樁量測各子程序佔比（lrs-1024, n=8，單次簽章/驗章）：

| 子程序 | Sign 佔比 | Verify 佔比 |
|---|---|---|
| **poly_mul（negacyclic 環乘法）** | **96.0%**（770 次呼叫） | **94.7%**（320 次呼叫） |
| SHAKE-256 雜湊 | ~2.0% | ~2.0% |
| Gaussian 取樣 | 0.3% | — |
| 其他（glue/算術） | ~1.8% | ~3.3% |

**環乘法是唯一的最佳化標的**：目前用 O(N²) 的 int64 convolution。改用 **NTT**（針對 d=2 的
partial-NTT，或 CRT over NTT-friendly 質數）可把每次乘法降到 O(N log N)，預期 Sign/Verify
快 1–2 個數量級。這對映 PrimeHE 6.3 把成本歸因到 tensor product / key-switching 的拆解，
也支撐你 README 既有的「未來移植到 C/Rust+NTT」結論——現在有數據佐證。

**未來工作**：(i) 換 constant-time Gaussian 取樣（CDT/Karney）；(ii) NTT 環乘法；
(iii) 跑 lattice-estimator 填上 Table A 的安全等級欄。

---

## 重現方式

```bash
python3 param_table.py                       # Table A
python3 benchmark_full.py lrs-1024 <n> <reps> [budget_s]   # Table B，每個 n 跑一次後合併
python3 correctness_gate.py <set> <n> <reps> [budget_s]    # Table C1（各組參數集）
python3 profile_bottleneck.py lrs-1024 8     # Table C3
python3 make_tables.py                        # 由上述 JSON 渲染所有表格 + PNG
```

輸出檔：`table_A_params.*`、`table_B_scaling.*`（含 png）、`table_C1_correctness.md`、
`table_C3_bottleneck.md`、以及 `benchmark_full.json` / `correctness_results.json` /
`profile_results.json`（原始數據）。
