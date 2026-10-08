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
執行環境是 Apple M2（macOS arm64）+ Python 3.11.9 + numpy 2.4.6，在不同機器benchmark 時間可能會些微不同。完整環境在 `results/raw.json` 的 `env` 欄位。
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 使用說明
```bash
python3 correctness.py # 正確性檢查，約 50 秒
python3 benchmark.py   # 1. 完整跑完約 24 mins，看到 ALL DONE 為結束

# 產論文數據
python3 performance.py # 讀 raw.json，產生 performance.{json,md}
python3 latex.py       # 讀 performance.json，產生 performance.tex
python3 figure.py      # 讀 performance.json，產生 performance.png
```

## License
Copyright (C) 2026 Guolong Wang

本專案採用 GNU General Public License v3.0 或更新版本授權，詳見 [LICENSE](LICENSE)。
