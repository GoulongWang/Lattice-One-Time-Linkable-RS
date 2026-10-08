"""
整理 raw.json 資料產出 performance.{json,md}。performance.json 會用於生成效能圖
"""

import json, numpy as np
D = json.load(open("results/raw.json"))["points"]
PARAMS = ["lrs-1024", "lrs-2048"]
NS = sorted({v["n"] for v in D.values()})

S, md = {}, []
for p in PARAMS:
    rows = [D[f"{p}:{n}"] for n in NS if f"{p}:{n}" in D and D[f"{p}:{n}"]["link"]]
    ns = [r["n"] for r in rows]
    m = lambda k: [float(np.mean(r[k])) for r in rows]
    kg, sg, vf, lk = m("keygen"), m("sign"), m("verify"), m("link")
    sig = [r["sig_kb"] for r in rows]
    S[p] = dict(n=ns, keygen=kg, sign=sg, verify=vf, link=lk,
                sig_kb=sig, pk_kb=rows[0]["pk_kb"], sk_kb=rows[0]["sk_kb"],
                sign_reps=[len(r["sign"]) for r in rows])
    md += [f"\n## {p}\n", "| n | " + " | ".join(map(str, ns)) + " |", "|---" * (len(ns) + 1) + "|"]
    for lab, v, f in (("KeyGen (ms)", kg, "{:.2f}"), ("Sign (ms) 平均", sg, "{:.0f}"),
                      ("Verify (ms)", vf, "{:.1f}"), ("Link (ms)", lk, "{:.1f}"),
                      ("Signature (KB)", sig, "{:.1f}")):
        md.append(f"| {lab} | " + " | ".join(f.format(x) for x in v) + " |")
    md += ["", f"- PK {rows[0]['pk_kb']:.1f} KB, SK {rows[0]['sk_kb']:.2f} KB；Sign 次數 {S[p]['sign_reps']}"]
json.dump(S, open("results/performance.json", "w"), indent=1, default=float)
open("results/performance.md", "w").write("# Performance\n" + "\n".join(md) + "\n")
print(open("results/performance.md").read())