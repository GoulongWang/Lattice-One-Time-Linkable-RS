"""Performance figure: per-algorithm running time against ring size, drawn from
results/performance.json with a LINEAR ring-size axis, in the thesis fonts."""
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
KAI_ASSET = "/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/BiauKai.ttc"
FONT_FILES = [
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",   # macOS native path
    f"{H}/fonts/BiauKaiTC.ttf",                                 # TC face extracted from BiauKai.ttc
    *glob.glob(KAI_ASSET),                                      # macOS downloadable asset
]
for f in FONT_FILES:
    if os.path.exists(f): fm.fontManager.addfont(f)
avail = {f.name for f in fm.fontManager.ttflist}
KAI = next((k for k in ("BiauKaiTC", "BiauKaiHK", "DFKai-SB") if k in avail), None)
if "Times New Roman" not in avail or KAI is None:
    # No substitute font: the thesis format mandates 標楷體, so a figure drawn in
    # anything else cannot be used.
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
    assert s["n"] == POW2, f"{param}: measured ring sizes {s['n']} != the ones the thesis reports {POW2}"
    ns = s["n"]; g = lambda k: s[k]
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
fig.savefig("results/performance.png", dpi=200)
print("font:", pick, "-> results/performance.png")
