"""Performance tables (powers-of-two n) from results/performance.json -> results/performance.tex

One LaTeX table per parameter set, ready to \input into the thesis."""
import json
S = json.load(open("results/performance.json")); POW2 = [1, 2, 4, 8, 16, 32, 64]
out = []
for p in ("lrs-1024", "lrs-2048"):
    s = S[p]
    assert s["n"] == POW2, f"{p}: measured ring sizes {s['n']} != the ones the thesis reports {POW2}"
    row = lambda lab, v, f: f"    {lab} & " + " & ".join(f.format(x) for x in v) + r" \\"
    out += [r"\begin{table}[ht]", r"  \centering", r"  \begin{tabular}{l" + "r" * 7 + "}", r"    \toprule",
            r"    $n$ & " + " & ".join(map(str, POW2)) + r" \\", r"    \midrule",
            row("KeyGen (ms)", s["keygen"], "{:.2f}"), row("Sign (ms)", s["sign"], "{:.0f}"),
            row("Verify (ms)", s["verify"], "{:.0f}"), row("Link (ms)", s["link"], "{:.1f}"),
            r"    \midrule",
            row("PK (KB)", [s["pk_kb"]] * len(s["n"]), "{:.1f}"), row("SK (KB)", [s["sk_kb"]] * len(s["n"]), "{:.2f}"),
            row("Signature (KB)", s["sig_kb"], "{:.1f}"),
            r"    \bottomrule", r"  \end{tabular}", rf"  \caption{{參數集 {p} 實驗結果}}",
            rf"  \label{{tab:result-{p}}}", r"\end{table}", ""]
open("results/performance.tex", "w").write("\n".join(out)); print("\n".join(out))
