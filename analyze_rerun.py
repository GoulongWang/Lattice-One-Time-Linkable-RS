"""Analyse results/rerun_raw.json: tables, linear fits (R^2), log-log slopes, figure
with LINEAR n axis.  Writes results/rerun_summary.{json,md}, results/fig6_3_linear.{png,pdf}."""
import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.font_manager as fm
D = json.load(open("results/rerun_raw.json"))["points"]
PARAMS = ["lrs-1024", "lrs-2048"]
NS = sorted({v["n"] for v in D.values()})
DOUBLING = [1, 2, 4, 8, 16, 32, 64]

def fit(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    b, a = np.polyfit(x, y, 1); yh = a + b * x
    r2 = 1 - ((y - yh) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return a, b, r2
def loglog_slope(x, y):
    return np.polyfit(np.log2(x), np.log2(y), 1)[0]

S, md = {}, []
for p in PARAMS:
    rows = [D[f"{p}:{n}"] for n in NS if f"{p}:{n}" in D and D[f"{p}:{n}"]["link"]]
    ns = [r["n"] for r in rows]
    m = lambda k: [float(np.mean(r[k])) for r in rows]
    kg, sg, vf, lk, tc = m("keygen"), m("sign"), m("verify"), m("link"), m("verify_tagcheck")
    sig = [r["sig_kb"] for r in rows]
    # Sign model over all raw reps: t = a*tag_retries + (b + c*n)*ring_retries
    X, Y = [], []
    for r in rows:
        for t, rt, rr in zip(r["sign"], r["retries_tag"], r["retries_ring"]):
            X.append([rt, rr, rr * r["n"]]); Y.append(t)
    X, Y = np.array(X, float), np.array(Y)
    coef, *_ = np.linalg.lstsq(X, Y, rcond=None)
    raw_r2 = 1 - ((Y - X @ coef) ** 2).sum() / ((Y - Y.mean()) ** 2).sum()
    Mz, Mc = rows[0]["Mz"], rows[0]["Mc"]
    sign_exp = [Mz * coef[0] + Mc * (coef[1] + coef[2] * n) for n in ns]
    S[p] = dict(n=ns, keygen=kg, sign=sg, sign_expected=sign_exp, verify=vf, verify_tagcheck=tc,
                link=lk, sig_kb=sig, pk_kb=rows[0]["pk_kb"], sk_kb=rows[0]["sk_kb"],
                sign_reps=[len(r["sign"]) for r in rows],
                retries_tag=[float(np.mean(r["retries_tag"])) for r in rows],
                retries_ring=[float(np.mean(r["retries_ring"])) for r in rows],
                Mz=Mz, Mc=Mc, sign_model_raw_R2=raw_r2, sign_model_samples=len(Y), sign_model_ms=dict(per_tag_attempt=coef[0], per_ring_attempt_const=coef[1],
                                                 per_ring_attempt_per_member=coef[2]),
                fit={k: dict(zip(("a", "b", "R2"), fit(ns, v))) for k, v in
                     (("verify", vf), ("sign", sg), ("sign_expected", sign_exp), ("sig_kb", sig))},
                loglog_slope={k: loglog_slope(ns, v) for k, v in (("verify", vf), ("sign", sg), ("sig_kb", sig))})
    md += [f"\n## {p}\n", "| n | " + " | ".join(map(str, ns)) + " |", "|---" * (len(ns) + 1) + "|"]
    for lab, v, f in (("KeyGen (ms)", kg, "{:.2f}"), ("Sign (ms) 實測平均", sg, "{:.0f}"),
                      ("Sign (ms) 期望值 M_z·t_tag+M_c·t_ring(n)", sign_exp, "{:.0f}"),
                      ("Verify (ms)", vf, "{:.1f}"), ("　其中第2行 z 檢查 (ms)", tc, "{:.3f}"),
                      ("Link (ms)", lk, "{:.1f}"), ("Signature (KB)", sig, "{:.1f}")):
        md.append(f"| {lab} | " + " | ".join(f.format(x) for x in v) + " |")
    F = S[p]["fit"]; L = S[p]["loglog_slope"]
    md += ["", f"- PK {rows[0]['pk_kb']:.1f} KB, SK {rows[0]['sk_kb']:.2f} KB；Sign 次數 {S[p]['sign_reps']}",
           f"- Verify ≈ {F['verify']['a']:.2f} + {F['verify']['b']:.2f}·n ms，R² = {F['verify']['R2']:.5f}；log-log 斜率 {L['verify']:.3f}",
           f"- Sign(期望) ≈ {F['sign_expected']['a']:.0f} + {F['sign_expected']['b']:.1f}·n ms，R² = {F['sign_expected']['R2']:.5f}；實測平均 R² = {F['sign']['R2']:.4f}",
           f"- Sign 逐次模型 t = {coef[0]:.1f}·(tag 次數) + ({coef[1]:.1f} + {coef[2]:.2f}·n)·(ring 次數) ms，{len(Y)} 筆單次簽章 R² = {raw_r2:.4f}（實測平均的波動來自重試次數 ~ Geom(1/M)）",
           f"- Signature ≈ {F['sig_kb']['a']:.1f} + {F['sig_kb']['b']:.2f}·n KB，R² = {F['sig_kb']['R2']:.6f}",
           f"- 平均重試：tag {np.mean(S[p]['retries_tag']):.2f}（M_z={Mz:.2f}），ring {np.mean(S[p]['retries_ring']):.2f}（M_c={Mc:.2f}）"]
json.dump(S, open("results/rerun_summary.json", "w"), indent=1, default=float)
open("results/rerun_summary.md", "w").write("# 重跑實驗結果（Verify 含演算法 4 第 2 行）\n" + "\n".join(md) + "\n")

KAI = ["BiauKaiTC", "BiauKaiHK", "DFKai-SB", "Kaiti TC", "STKaiti", "Kaiti SC", "Noto Sans CJK TC", "Noto Sans CJK JP"]
avail = {f.name for f in fm.fontManager.ttflist}; pick = next((f for f in KAI if f in avail), None)
if pick: plt.rcParams["font.sans-serif"] = [pick] + plt.rcParams["font.sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
for ax, p in zip(axes, PARAMS):
    s = S[p]; n = np.array(s["n"]); xx = np.linspace(0, 64, 100)
    for key, lab, mk, c in (("sign", "Sign（實測平均）", "o", "C1"), ("verify", "Verify", "s", "C2")):
        ax.plot(n, np.array(s[key]) / 1e3, mk, color=c, label=lab)
    f = s["fit"]["sign_expected"]; ax.plot(xx, (f["a"] + f["b"] * xx) / 1e3, "-", color="C1", lw=1,
        label=f"Sign 期望值 M_z·t_tag+M_c·t_ring(n)（單次模型 R²={s['sign_model_raw_R2']:.4f}）")
    f = s["fit"]["verify"]; ax.plot(xx, (f["a"] + f["b"] * xx) / 1e3, "-", color="C2", lw=1,
        label=f"Verify 線性擬合 (R²={f['R2']:.4f})")
    ax.plot(n, np.array(s["link"]) / 1e3, "^-", color="C3", label="Link")
    ax.plot(n, np.array(s["keygen"]) / 1e3, "D-", color="C0", label="KeyGen")
    ax.set_xlim(0, 66); ax.set_ylim(bottom=0); ax.set_xticks([1, 8, 16, 24, 32, 40, 48, 56, 64])
    ax.set_xlabel("環成員人數 n（線性刻度）"); ax.set_ylabel("執行時間 (s)")
    ax.set_title(f"各演算法執行時間（{p}）"); ax.grid(True, ls=":", alpha=.5); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig("results/fig6_3_linear.png", dpi=200); fig.savefig("results/fig6_3_linear.pdf")
print(open("results/rerun_summary.md").read()); print("font:", pick)
