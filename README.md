# 基於晶格之後量子可連結環簽章方案
## 檔案說明

```
lrs.py                  方案實作：Setup / KeyGen / Sign / Verify / Link
correctness.py          正確性檢查（改完程式先跑這個）
benchmark.py            效能測量
performance.py          整理測量數據：計算各演算法平均時間
figure.py               效能圖（論文圖）
results/raw.json        原始量測資料
```

## 環境
執行環境是 Apple M2（macOS arm64）+ Python 3.11.9 + numpy 2.4.6，在不同機器benchmark 時間可能會些微不同。完整環境在 `results/raw.json` 的 `env` 欄位。
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 使用說明
```bash
python3 correctness.py # 正確性檢查，約 50 秒
python3 benchmark.py   # 1. 完整跑完約 24 mins。若不小心中斷沒差，raw.json 會紀錄已經寫入的資料，
                       #    下次同指令可以直接重跑。它會接續上次沒跑完的地方直到結束。測量完的地方會跳過。
                       # 2. 若想要從頭完整測量，記得先刪掉舊的 raw.json，否則會混到舊資料，然後再重新產生新資料。
                       # 3. 看到 ALL DONE 為結束

# 產論文數據
python3 performance.py # 讀 raw.json，產生 performance.{json,md}
python3 figure.py      # 讀 performance.json，產生 performance.png
```