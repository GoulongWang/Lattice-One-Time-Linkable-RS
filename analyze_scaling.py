"""Summarise results/scaling_raw.json into results/scaling_summary.{json,md}.

scaling_summary.json is the interface make_perf_table.py and plot_perf_figure.py read:
per ring size n, the mean cost of each algorithm plus the key/signature sizes.

It also carries the figures the README's handover notes rely on (Sign's standard
deviation, the per-point repetition counts, and the measured rejection-sampling
retry counts against the theoretical M_z / M_c) so those claims can be re-checked
rather than taken on trust. No plots and no curve fitting: the thesis figure is
drawn by plot_perf_figure.py."""
import json, numpy as np
D = json.load(open("results/scaling_raw.json"))["points"]
PARAMS = ["lrs-1024", "lrs-2048"]
NS = sorted({v["n"] for v in D.values()})

S, md = {}, []
for p in PARAMS:
    rows = [D[f"{p}:{n}"] for n in NS if f"{p}:{n}" in D and D[f"{p}:{n}"]["link"]]
    ns = [r["n"] for r in rows]
    m = lambda k: [float(np.mean(r[k])) for r in rows]
    kg, sg, vf, lk = m("keygen"), m("sign"), m("verify"), m("link")
    sg_sd = [float(np.std(r["sign"], ddof=1)) for r in rows]
    sig = [r["sig_kb"] for r in rows]
    Mz, Mc = rows[0]["Mz"], rows[0]["Mc"]
    S[p] = dict(n=ns, keygen=kg, sign=sg, sign_std=sg_sd, verify=vf, link=lk,
                sig_kb=sig, pk_kb=rows[0]["pk_kb"], sk_kb=rows[0]["sk_kb"],
                sign_reps=[len(r["sign"]) for r in rows],
                retries_tag=m("retries_tag"), retries_ring=m("retries_ring"),
                Mz=Mz, Mc=Mc)
    md += [f"\n## {p}\n", "| n | " + " | ".join(map(str, ns)) + " |", "|---" * (len(ns) + 1) + "|"]
    for lab, v, f in (("KeyGen (ms)", kg, "{:.2f}"), ("Sign (ms) 平均", sg, "{:.0f}"),
                      ("　Sign 標準差 (ms)", sg_sd, "{:.0f}"), ("Verify (ms)", vf, "{:.1f}"),
                      ("Link (ms)", lk, "{:.1f}"), ("Signature (KB)", sig, "{:.1f}")):
        md.append(f"| {lab} | " + " | ".join(f.format(x) for x in v) + " |")
    cv = [s / x for s, x in zip(sg_sd, sg)]
    # Total retries = sum of two independent geometrics (tag, ring) -> CV of the sum
    cv_theory = np.sqrt(Mz * Mz - Mz + Mc * Mc - Mc) / (Mz + Mc)
    md += ["", f"- PK {rows[0]['pk_kb']:.1f} KB, SK {rows[0]['sk_kb']:.2f} KB；Sign 次數 {S[p]['sign_reps']}",
           f"- Sign 變異係數 std/mean：實測平均 {np.mean(cv):.3f}（範圍 {min(cv):.2f}–{max(cv):.2f}）"
           f"，兩個獨立幾何分布之和的理論值 {cv_theory:.3f}",
           f"- 平均重試：tag {np.mean(S[p]['retries_tag']):.2f}（M_z={Mz:.2f}），"
           f"ring {np.mean(S[p]['retries_ring']):.2f}（M_c={Mc:.2f}）"]
json.dump(S, open("results/scaling_summary.json", "w"), indent=1, default=float)
open("results/scaling_summary.md", "w").write("# 量測摘要（由 scaling_raw.json 重算）\n" + "\n".join(md) + "\n")
print(open("results/scaling_summary.md").read())
