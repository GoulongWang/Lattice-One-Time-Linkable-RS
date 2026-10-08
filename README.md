# 基於晶格之後量子可連結環簽章方案
## 檔案說明

```
lrs.py                  方案實作：Setup / KeyGen / Sign / Verify / Link
correctness.py          正確性檢查（改完程式先跑這個）
benchmark.py            效能測量
performance.py          整理測量數據：計算各演算法平均時間
latex.py                效能表（LaTeX）
figure.py               效能圖（論文圖）
results/raw.json        原始量測資料
```

## 環境
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 使用說明
```bash
python3 correctness.py # 正確性檢查，約 50 秒
python3 performance.py # 讀 raw.json，產生 performance.{json,md}
python3 latex.py       # 讀 performance.json，產生 performance.tex
python3 figure.py      # 讀 performance.json，產生 performance.png
```

## 重新量測（只有在改動 lrs.py 之後才需要）

效能量測可續跑——每簽完一次就存檔，超過時間預算就停，再執行一次會從停的地方接下去：

```bash
python3 benchmark.py 600     # 跑 600 秒後暫停
python3 benchmark.py 600     # 接續
# ... 重複到印出 ALL DONE
```

完整跑完約 **24 分鐘**的計算量（330 次簽章）。跑完後重新執行上一節的算繪指令。

> ⚠️ `benchmark.py` 會把結果**合併**進既有的 `results/raw.json`。
> 要從頭量測請先刪掉該檔，否則會混到舊資料。

## 資料格式

**`results/raw.json`** — `points` 以 `"<參數集>:<n>"` 為鍵，每個點存下**每一次**的原始計時（ms）
而非只存平均，所以標準差、中位數、分位數事後都算得出來：

| 欄位 | 內容 |
|---|---|
| `keygen` / `sign` / `verify` / `link` | 每次計時的陣列（ms） |
| `pk_kb` / `sk_kb` / `sig_kb` | 金鑰與簽章大小 |


## 交接注意事項
**1. 四個演算法的重複次數不一樣，不要誤以為是統一的。**
看 `benchmark.py` 開頭的常數：

| 演算法 | 次數 |
|---|---|
| KeyGen | 30 |
| Sign | lrs-1024 全部 30；lrs-2048 為 20，n=32 降為 12，n=64 降為 8 |
| Verify | 每個簽章驗多次，實際約 32–60 |
| Link | 50（**重複連結同一對簽章**） |

在 lrs-2048 參數集中，當 n 越大一次簽章的時間會變很長，為了測量時間方便，次數做了以上調整。

**2. 量測環境是 Linux aarch64 + Python 3.10.12 + numpy 2.2.6。**
**不同機器重跑時間可能會些微不同**。
確切環境記在 `results/raw.json` 的 `env` 欄位。
