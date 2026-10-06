"""Thesis Figure 7 (same style as make_tables.py) redrawn from the re-run data
(results/rerun_summary.json), with a LINEAR ring-size axis."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

# Thesis fonts: English/digits in Times New Roman, Chinese in 標楷體 (BiauKai TC).
# Font files are registered explicitly (macOS keeps BiauKai as a downloadable asset);
# matplotlib falls back glyph-by-glyph from the first family to the second.
import glob, os
H = os.path.expanduser("~")
FONT_FILES = [
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",       # macOS native path
    f"{H}/mnt/Supplemental/Times New Roman.ttf",                     # Cowork VM mount
    f"{H}/fonts/BiauKaiTC.ttf",                                      # TC face extracted from BiauKai.ttc
    *glob.glob("/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/BiauKai.ttc"),
]
for f in FONT_FILES:
    if os.path.exists(f): fm.fontManager.addfont(f)
avail = {f.name for f in fm.fontManager.ttflist}
KAI = next((k for k in ("BiauKaiTC", "BiauKaiHK", "DFKai-SB") if k in avail), None)
assert "Times New Roman" in avail and KAI, f"missing thesis fonts (found Kai={KAI})"
plt.rcParams["font.family"] = ["Times New Roman", KAI]
plt.rcParams["mathtext.fontset"] = "stix"
pick = f"Times New Roman + {KAI}"
plt.rcParams["axes.unicode_minus"] = False

S = json.load(open("results/rerun_summary.json"))
POW2 = [1, 2, 4, 8, 16, 32, 64]
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, param in zip(axes, ("lrs-1024", "lrs-2048")):
    s = S[param]
    idx = [i for i, n in enumerate(s["n"]) if n in POW2]          # powers of two only
    ns = [s["n"][i] for i in idx]; g = lambda k: [s[k][i] for i in idx]
    ax.plot(ns, g("sign"),   "o-", color="C1", label="Sign")
    ax.plot(ns, g("verify"), "s-", color="C2", label="Verify")
    ax.plot(ns, g("link"),   "^-", color="C3", label="Link")
    ax.plot(ns, g("keygen"), "D-", color="C0", label="KeyGen")
    ax.set_xticks(POW2, ["1", "", "4", "8", "16", "32", "64"]);  # "2" too close to "1" on a linear axis
    ax.set_xlim(0, 66); ax.set_ylim(bottom=0)
    ax.set_xlabel("環成員人數 n"); ax.set_ylabel("執行時間 (ms)")
    ax.set_title(f"LRS 各演算法執行時間（{param}）")
    ax.legend(); ax.grid(True, which="both", ls=":", alpha=0.5)
fig.tight_layout()
fig.savefig("results/fig7_linear.png", dpi=200); fig.savefig("results/fig7_linear.pdf")
print("font:", pick, "-> results/fig7_linear.png / .pdf")
