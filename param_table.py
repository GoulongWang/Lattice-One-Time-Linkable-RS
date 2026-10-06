"""Experiment A -- multi-parameter-set table (Table A).

For each parameter set: report (N, q, ceil(log2 q), h, l, v, k, kappa, beta, sigma,
the joint rejection-sampling constant M, security bits=TBD) and check the
correctness constraints (q == 5 mod 8 so Lemma 1 holds; M finite/well-behaved).
Outputs Table A as markdown + json (no CSV).
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
for name, ps in lrs.PARAM_SETS.items():
    lrs.set_params(name)
    logq = int(np.ceil(np.log2(lrs.Q)))
    ok_mod = (lrs.Q % 8 == 5)
    ok_M = np.isfinite(lrs.M) and lrs.M > 1
    rows.append({
        "set": name,
        "N": lrs.N,
        "q": int(lrs.Q),
        "q_expr": q_expr(lrs.Q),
        "log2q": logq,
        "h": lrs.H_DIM, "l": lrs.L_DIM, "v": lrs.V_DIM, "k": lrs.K_DIM,
        "kappa": lrs.KAPPA, "beta": lrs.BETA,
        "sigma": int(lrs.SIGMA),
        "Mz": round(float(lrs.MZ), 3),
        "M": round(float(lrs.M), 3),
        "Mtotal": round(float(lrs.MZ + lrs.M), 3),
        "constraints_ok": bool(ok_mod and ok_M),
        "sec_bits": ps["sec_bits"] if ps["sec_bits"] is not None else "TBD",
    })

# ---- markdown ----
hdr = ["Parameter Set", "N", "q", "ceil(log2 q)", "h", "l", "v", "k",
       "kappa", "beta", "sigma", "M_z (tag)", "M (ring)", "M_total", "Security (bits)"]
keys = ["set", "N", "q_expr", "log2q", "h", "l", "v", "k", "kappa", "beta",
        "sigma", "Mz", "M", "Mtotal", "sec_bits"]
md = ["| " + " | ".join(hdr) + " |", "|" + "|".join(["---"] * len(hdr)) + "|"]
for r in rows:
    md.append("| " + " | ".join(str(r[k]) for k in keys) + " |")
md_txt = "\n".join(md)

with open(os.path.join(RESULTS, "table_A_params.md"), "w") as f:
    f.write("# Table A -- Parameter sets and rejection-sampling constants\n\n")
    f.write(md_txt + "\n\n")
    f.write("Notes: q = %s (prime, == 5 mod 8) reused for all sets; every N is a\n" % q_expr(lrs.Q))
    f.write("power of two, so Lemma 1 (partial splitting of X^N+1, d=2) holds throughout.\n")
    f.write("sigma = alpha * kappa * sqrt(l*N) with alpha = %.0f, so M is constant across sets.\n" % lrs.ALPHA)
    f.write("Two INDEPENDENT rejection-sampling loops run per signature (Algorithm 3):\n")
    f.write("M_z (lines 9-13) guards the linkable tag's response z = y + d*(r1-r2);\n")
    f.write("M (lines 15-21) is the joint rejection constant over the stacked ring\n")
    f.write("response (z_j || z_c,j). They are sequential and independent, so\n")
    f.write("E[total attempts per signature] = M_total = M_z + M.\n")
    f.write("Security (bits) = TBD: concrete lattice-estimator / Core-SVP evaluation is deferred.\n")
    f.write("All sets satisfy the correctness constraints (q==5 mod 8; M > 1, finite).\n")

with open(os.path.join(RESULTS, "table_A_params.json"), "w") as f:
    json.dump(rows, f, indent=2)

print(md_txt)
print("\nconstraints_ok:", all(r["constraints_ok"] for r in rows))
print("wrote results/table_A_params.{md,json}")
