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
python3 benchmark.py 30000 # 參數為時間預算（秒），完整跑完約 2 小時 10 分（Apple M2），看到 ALL DONE 為結束

# 產論文數據
python3 performance.py # 讀 raw.json，產生 performance.{json,md}
python3 latex.py       # 讀 performance.json，產生 performance.tex
python3 figure.py      # 讀 performance.json，產生 performance.png
```

`benchmark.py` 的注意事項：
- 不加參數時，時間預算只有 160 秒，到時間會印出 `PAUSED` 並停下。每次 Sign 量完都會存進 `results/raw.json`，再執行一次就會從中斷的地方繼續。
- 如果 `results/raw.json` 已經是完整資料，程式會直接印出 `ALL DONE`，不會重新量測。要在自己的電腦上從頭量，請先把 `results/raw.json` 刪除或改名。

## License
Copyright (C) 2026 Guolong Wang

本專案採用 GNU General Public License v3.0 或更新版本授權，詳見 [LICENSE](LICENSE)。
