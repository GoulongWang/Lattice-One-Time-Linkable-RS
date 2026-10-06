"""Thesis Tables 4 & 5 (powers-of-two n) from results/rerun_summary.json -> results/table4_5.tex"""
import json
S = json.load(open("results/rerun_summary.json")); POW2 = [1, 2, 4, 8, 16, 32, 64]
out = []
for tno, p in ((4, "lrs-1024"), (5, "lrs-2048")):
    s = S[p]; ix = [s["n"].index(n) for n in POW2]
    row = lambda lab, v, f: f"    {lab} & " + " & ".join(f.format(v[i]) for i in ix) + r" \\"
    out += [r"\begin{table}[ht]", r"  \centering", r"  \begin{tabular}{l" + "r" * 7 + "}", r"    \toprule",
            r"    $n$ & " + " & ".join(map(str, POW2)) + r" \\", r"    \midrule",
            row("KeyGen (ms)", s["keygen"], "{:.2f}"), row("Sign (ms)", s["sign"], "{:.0f}"),
            row("Verify (ms)", s["verify"], "{:.0f}"), row("Link (ms)", s["link"], "{:.1f}"),
            r"    \midrule",
            row("PK (KB)", [s["pk_kb"]] * len(s["n"]), "{:.1f}"), row("SK (KB)", [s["sk_kb"]] * len(s["n"]), "{:.2f}"),
            row("Signature (KB)", s["sig_kb"], "{:.1f}"),
            r"    \bottomrule", r"  \end{tabular}", rf"  \caption{{參數集 {p} 實驗結果}}",
            rf"  \label{{tab:result-{p}}}", r"\end{table}", ""]
open("results/table4_5.tex", "w").write("\n".join(out)); print("\n".join(out))
