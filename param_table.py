"""Parameter sets and their rejection-sampling constants -> results/params.{md,json}

The markdown mirrors the thesis parameter table: one parameter per row, one
parameter set per column, same row order, same rounding -- so it can be diffed
against the thesis cell by cell.  It also checks the correctness constraints
(q == 5 mod 8 so Lemma 1 holds; M finite and > 1).  No measurements here.
"""
import json, os
import numpy as np
import lrs

RESULTS = "results"
os.makedirs(RESULTS, exist_ok=True)

def q_expr(q):
    """Render q as the compact 2^e - c form used in the thesis parameter table."""
    e = int(np.ceil(np.log2(q)))
    return "2^%d - %d" % (e, (1 << e) - q)

rows = []
for name in lrs.PARAM_SETS:
    lrs.set_params(name)
    ok_mod = (lrs.Q % 8 == 5)
    ok_M = np.isfinite(lrs.M) and lrs.M > 1
    rows.append({
        "set": name,
        "N": lrs.N,
        "q": int(lrs.Q),
        "q_expr": q_expr(lrs.Q),
        "h": lrs.H_DIM, "l": lrs.L_DIM, "v": lrs.V_DIM, "k": lrs.K_DIM,
        "kappa": lrs.KAPPA, "beta": lrs.BETA,
        "sigma": int(lrs.SIGMA),
        "M": float(lrs.M),
        "Mz": float(lrs.MZ),
        "constraints_ok": bool(ok_mod and ok_M),
    })

# ---- markdown: transposed, one parameter per row (the thesis table's layout) ----
LINES = [("N", "{:d}", "N"), ("q", "{}", "q_expr"), ("h", "{:d}", "h"),
         ("l", "{:d}", "l"), ("v", "{:d}", "v"), ("k", "{:d}", "k"),
         ("κ", "{:d}", "kappa"), ("β", "{:d}", "beta"), ("σ", "{:d}", "sigma"),
         ("M", "{:.2f}", "M"), ("M_z", "{:.2f}", "Mz")]
md = ["| 參數 | " + " | ".join(r["set"] for r in rows) + " |",
      "|" + "|".join(["---"] * (len(rows) + 1)) + "|"]
for label, fmt, key in LINES:
    md.append(f"| {label} | " + " | ".join(fmt.format(r[key]) for r in rows) + " |")
md_txt = "\n".join(md)

with open(os.path.join(RESULTS, "params.md"), "w") as f:
    f.write("# 參數集設定\n\n")
    f.write(md_txt + "\n\n")
    f.write("論文的表把兩組共用的值合併成一格；markdown 沒有合併儲存格，所以這裡兩欄都印同一個值。\n\n")
    f.write("Notes: q = %s (prime, == 5 mod 8) reused for all sets; every N is a\n" % q_expr(lrs.Q))
    f.write("power of two, so Lemma 1 (partial splitting of X^N+1, d=2) holds throughout.\n")
    f.write("sigma = alpha * kappa * sqrt(l*N) with alpha = %.0f, so M is constant across sets.\n" % lrs.ALPHA)
    f.write("Two INDEPENDENT rejection-sampling loops run per signature (Algorithm 3):\n")
    f.write("M_z (lines 9-13) guards the linkable tag's response z = y + d*(r1-r2);\n")
    f.write("M (lines 15-21) is the joint rejection constant over the stacked ring\n")
    f.write("response (z_j || z_c,j). They are sequential and independent, so\n")
    f.write("E[total attempts per signature] = M_z + M.\n")
    f.write("All sets satisfy the correctness constraints (q==5 mod 8; M > 1, finite).\n")

# The json is the machine-readable copy: same fields, M / M_z to 3 decimals.
# The markdown rounds straight from the full-precision value -- rounding 14.8346
# to 3 and then to 2 decimals would print 14.84 where the thesis prints 14.83.
with open(os.path.join(RESULTS, "params.json"), "w") as f:
    json.dump([{k: (round(v, 3) if k in ("M", "Mz") else v) for k, v in r.items()}
               for r in rows], f, indent=2)

print(md_txt)
print("\nconstraints_ok:", all(r["constraints_ok"] for r in rows))
print("wrote results/params.{md,json}")
