# Copyright (C) 2026 Guolong Wang
# SPDX-License-Identifier: GPL-3.0-or-later
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

# 論文字體: Times New Roman, 標楷體 (BiauKai TC)
# 要跑記得改字體路徑
import glob, os
H = os.path.expanduser("~")
KAI_ASSET = "/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/BiauKai.ttc"
FONT_FILES = [
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    f"{H}/fonts/BiauKaiTC.ttf",
    *glob.glob(KAI_ASSET),
]
for f in FONT_FILES:
    if os.path.exists(f): fm.fontManager.addfont(f)
avail = {f.name for f in fm.fontManager.ttflist}
KAI = next((k for k in ("BiauKaiTC", "BiauKaiHK", "DFKai-SB") if k in avail), None)
if "Times New Roman" not in avail or KAI is None:
    missing = [n for n, ok in (("Times New Roman", "Times New Roman" in avail), ("標楷體", KAI)) if not ok]
    raise SystemExit("缺少字型：" + "、".join(missing))
plt.rcParams["font.family"] = ["Times New Roman", KAI]
plt.rcParams["mathtext.fontset"] = "stix"
pick = f"Times New Roman + {KAI}"
plt.rcParams["axes.unicode_minus"] = False

S = json.load(open("results/performance.json"))
POW2 = [1, 2, 4, 8, 16, 32, 64]
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, param in zip(axes, ("lrs-1024", "lrs-2048")):
    s = S[param]
    ns = s["n"]; g = lambda k: s[k]
    ax.plot(ns, g("sign"),   "o-", color="C1", label="Sign")
    ax.plot(ns, g("verify"), "s-", color="C2", label="Verify")
    ax.plot(ns, g("link"),   "^-", color="C3", label="Link")
    ax.plot(ns, g("keygen"), "D-", color="C0", label="KeyGen")
    ax.set_xticks(POW2, ["1", "", "4", "8", "16", "32", "64"]);  # 2 太靠近 1，所以只畫線標示
    ax.set_xlim(0, 66); ax.set_ylim(bottom=0)
    ax.set_xlabel("環成員人數 n"); ax.set_ylabel("執行時間 (ms)")
    ax.set_title(f"LRS 各演算法執行時間（{param}）")
    ax.legend(); ax.grid(True, which="both", ls=":", alpha=0.5)
fig.tight_layout()
fig.savefig("results/performance.png", dpi=200)
print("font:", pick, "-> results/performance.png")
