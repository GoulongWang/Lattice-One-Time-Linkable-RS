# Lattice-based One-Time Linkable Ring Signature — 參考實作與效能量測

碩論〈Post-Quantum Linkable Ring Signatures Based on Lattice〉的實作與實驗程式碼。
純 NumPy 參考實作，單執行緒。**目的是驗證正確性與分析相對成本（scaling），不是追求絕對速度**
——經最佳化的 C/Rust + NTT 實作可以快 1–2 個數量級。

本 README 只講「怎麼跑」。**實驗數字與其解讀請看論文本文**，這裡刻意不放任何數據，
以免兩邊對不起來。

---

## 檔案結構

```
lrs.py                  方案實作：Setup / KeyGen / Sign / Verify / Link、環運算、參數集
test_correctness.py     正確性檢查（兩組參數集各四項，~50 秒，改完程式先跑這個）

param_table.py          參數集與拒絕取樣常數（對應論文的參數表）
bench_scaling.py        效能量測：對各環大小 n 計時（可續跑）
analyze_scaling.py      彙總量測結果：各演算法平均、Sign 標準差、重試次數
make_perf_table.py      效能表（LaTeX，可 \input 進論文）
plot_perf_figure.py     效能圖（論文字型、線性 n 軸）

results/
  scaling_raw.json          ← 原始量測資料（唯一被追蹤的量測結果）
```

**`results/` 裡只有這一個檔案進版控。** 其餘所有圖、表、摘要都是從它算出來的，
執行腳本就會重建（幾秒鐘），因此被 `.gitignore` 擋掉。

這是刻意的：這個 repo 過去兩次都踩到「產物過期」——存進去的表格和論文章節草稿，
在參數改掉之後沒有跟著更新，而光看檔案是分不出它是新的還是舊的。
**唯一事實來源是 `results/scaling_raw.json` 加上程式碼。**

---

## 環境

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt     # numpy, matplotlib
```

只有 `plot_perf_figure.py` 需要論文字型（Times New Roman + 標楷體），找不到會直接停下來，
並列出它找過的**每一條路徑**與各自有沒有命中。macOS 把標楷體放在系統的 downloadable asset 裡，
所以腳本有明確註冊字型檔。在沒有這些字型的機器上，其餘三支腳本照跑不誤——
數字都在 `scaling_summary.md` 和 `performance.tex` 裡。

**腳本刻意不退回其他字型。** 論文格式規定中文用標楷體，換字型畫出來的圖本來就不能放進論文；
生一張看起來沒問題、實際上用不了的圖，比直接擋下來更糟。字型怎麼補：

| 平台 | Times New Roman | 標楷體 |
|---|---|---|
| macOS | 系統內建 | 開「字體簿」搜尋「標楷體」按下載 |
| Windows | 系統內建 | 系統內建 DFKai-SB |
| Linux | 裝 `ttf-mscorefonts-installer` | 沒有，須從 macOS/Windows 複製字型檔過來 |

複製來的字型檔放到錯誤訊息列出的任一路徑即可（例如 `~/fonts/BiauKaiTC.ttf`）。

---

## 從零重建所有圖表

`scaling_raw.json` 已經在版控裡，所以**不需要重跑量測**，直接算繪即可：

```bash
python3 analyze_scaling.py      # → scaling_summary.{json,md}
python3 make_perf_table.py      # → performance.tex          （讀 scaling_summary.json）
python3 plot_perf_figure.py     # → performance_figure.png（讀 scaling_summary.json）
python3 param_table.py          # → params.{md,json}          （純參數，不含量測）
```

`analyze_scaling.py` 必須先跑，另外兩支讀它產生的 `scaling_summary.json`。

## 重新量測（只有在改動 lrs.py 之後才需要）

**先跑正確性檢查**，再花時間量測：

```bash
python3 test_correctness.py     # ~50 秒，lrs-1024 與 lrs-2048 都驗
```

效能量測可續跑——每簽完一次就存檔，超過時間預算就停，再執行一次會從停的地方接下去：

```bash
python3 bench_scaling.py 600     # 跑 600 秒後暫停
python3 bench_scaling.py 600     # 接續
# ... 重複到印出 ALL DONE
```

完整跑完約 **24 分鐘**的計算量（330 次簽章）。跑完後重新執行上一節的算繪指令。

> ⚠️ `bench_scaling.py` 會把結果**合併**進既有的 `scaling_raw.json`。
> 要從頭量測請先刪掉該檔，否則會混到舊資料。

---

## 資料格式

**`results/scaling_raw.json`** — `points` 以 `"<參數集>:<n>"` 為鍵，每個點存下**每一次**的原始計時（ms）
而非只存平均，所以標準差、中位數、分位數事後都算得出來：

| 欄位 | 內容 |
|---|---|
| `keygen` / `sign` / `verify` / `link` | 每次計時的陣列（ms） |
| `retries_tag` / `retries_ring` | 每次簽章的兩種拒絕取樣次數 |
| `pk_kb` / `sk_kb` / `sig_kb` | 金鑰與簽章大小 |
| `Mz` / `M` | 該參數集的理論拒絕取樣常數（論文參數表的 M_z 與 M） |

頂層另有 `env` / `python` / `numpy` 記錄量測環境。

環大小只有 2 的次方（1, 2, 4, 8, 16, 32, 64），也就是論文的表與圖報告的那些。

---

## 給接手者的注意事項

這幾點是踩過坑才知道的，照順序看：

**1. Sign 的標準差跟平均同一個量級，這是正常的，不是量測壞掉。**
Sign 的成本 =（拒絕取樣重試次數）×（單趟成本），而重試次數服從幾何分布——
幾何分布本身就是重尾的，變異係數接近 1。
Sign 有兩個獨立的重試迴圈（見第 5 點），總重試次數是兩個幾何分布之和，
變異係數約 **0.74**；實測 14 個資料點的 `std/mean` 平均 **0.718**（範圍 0.50–1.38），吻合。
**這反而是實作正確的佐證**，不要試圖「修掉」它。
（若誤以為只有單一迴圈、M = 20.5，算出來會是 0.975，對不上實測。）
這兩個數字不用自己算：`analyze_scaling.py` 的摘要每組參數都會印出實測變異係數與理論值。

**2. 表上報的是平均，不是中位數。**
理論預測的是期望值 `E[Sign] = M_total × 單趟成本`，而重試次數是幾何分布、右尾很長，
中位數會系統性低估。`analyze_scaling.py` 只算平均與標準差，刻意不提供中位數。

**3. 四個演算法的重複次數不一樣，不要誤以為是統一的。**
看 `bench_scaling.py` 開頭的常數：

| 演算法 | 次數 |
|---|---|
| KeyGen | 30 |
| Sign | lrs-1024 全部 30；lrs-2048 為 20，n=32 降為 12，n=64 降為 8 |
| Verify | 每個簽章驗多次，實際約 32–60 |
| Link | 50（**重複連結同一對簽章**，所以它的標準差量到的是計時抖動，不是演算法變異） |

lrs-2048 大 n 的次數較少是因為單次簽章要十幾秒。實際次數都存在 `scaling_raw.json` 裡，
`analyze_scaling.py` 的摘要也會印出來——**寫論文時請照實引用，不要寫成統一的 30 次**。

**4. 量測環境是 Linux aarch64 + Python 3.10.12 + numpy 2.2.6。**
`requirements.txt` 刻意不釘版本（釘死會讓人在別的平台裝不起來，而程式只用到 numpy 最基本的功能）。
但**換機器重跑的話絕對時間一定會不同**，所以論文裡比較的應該是相對成本與 scaling，不是絕對毫秒數。
確切環境記在 `scaling_raw.json` 的 `env` 欄位。

**5. 簽章有兩個獨立的拒絕取樣迴圈，不要只實作一個。**
這是曾經出過的錯：原本的 `sign()` 只做了環回應的聯合測試（`M`），
漏掉連結標記自己的測試（`M_z`，對應 Algorithm 3 第 9–13 行）。
少了它，`z = y + d·(r1−r2)` 的分布會洩漏秘密隨機值。
兩個迴圈依序獨立執行，所以期望嘗試次數是 `M_z + M ≈ 20.5`（相加，不是相乘）。
細節見 `lrs.py` 中 `sign()` 的 docstring。

**6. int64 的精確性餘裕只剩約 4 倍。**
`poly_mul` 用 `np.convolve` 在 int64 上做精確卷積。在目前的 `q = 2⁴⁰ − 195`、`N = 2048` 下，
卷積中間值峰值約 `2⁶⁰·⁸`，距離 int64 上限 `2⁶³` 不遠。
**想再加大 `q` 或試 `N = 4096` 以上之前**，先看 `lrs.py` 的 `_check_int64_headroom()`——
它每次 `set_params()` 都會估算並在逼近上限時警告。真的溢位的話不會報錯，會靜默算出錯誤結果。

**7. 簽章鏈的身分錨點是「第一張簽章」，不是兩兩比對。**
`sign()` 在第一次簽章時把 state 記成 `(m, L)`，之後每一次都原樣帶著不改
（`lrs.py` 的 `new_state = state`）。所以每張後續簽章帶的差值都以錨點的 `r1` 為基準，
**每一張都連得回第 1 張，但兩張後續簽章之間連不起來**：

| `new_state` | 1↔2 | 1↔3 | 2↔3 |
|---|---|---|---|
| `state`（目前的實作） | 1 | 1 | 0 |
| `(m, L)`（改成每次更新） | 1 | 0 | 1 |

`new_state = state` 那行看起來很像「忘了更新」，但**改掉它會壞掉連結性**，
而且只比對 1↔2 是分不出來的（兩種寫法都回 1）——
這就是 `test_correctness.py` 第 3 項要簽三張簽章的原因。
至於 `2↔3 == 0`，那是設計而非限制；真的想讓任兩張都連得起來，
等於改動論文裡 linkability 的定義，請先回論文確認，不要直接把測試裡那行刪掉。

---

## 參數集

安全性主要隨多項式維度 `N` 提升。高斯寬度 `σ = α·κ·√(lN)`（`α = 11` 固定），
使拒絕取樣常數在各組保持不變。`q = 2⁴⁰ − 195`（質數、`≡ 5 mod 8`）兩組共用；
因每個 `N` 都是 2 的次方，partial splitting 引理（`X^N+1`，`d = 2`）對兩組均成立。

目前定義了 `lrs-1024`（N=1024）與 `lrs-2048`（N=2048），完整數值跑 `python3 param_table.py` 即得。
安全等級（bits）尚未以 lattice-estimator / Core-SVP 評估，是留給後續的工作。

---

## 注意

- 高斯取樣用的是四捨五入的連續常態分布，對 PoC 足夠，但**不是常數時間**。
- 環乘法是 `O(N²)` 的 int64 convolution，尚未實作 NTT——這是最明顯的最佳化標的。
- 這是論文用的研究程式碼，**不是**常數時間實作，請勿用於正式環境。
