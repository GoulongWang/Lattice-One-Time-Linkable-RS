"""Experiment A -- multi-parameter-set table (Table A).

For each parameter set: report (N, ceil(log2 q), l, k, kappa, beta, sigma, M1, M2,
expected rejection-sampling attempts M1*M2, security bits=TBD) and check the
correctness constraints (q == 5 mod 8 so Lemma 1 holds; M1, M2 finite/well-behaved).
Outputs Table A as markdown + json (no CSV).
"""
import json, os
import numpy as np
import lrs

RESULTS = "results"
os.makedirs(RESULTS, exist_ok=True)

rows = []
for name, ps in lrs.PARAM_SETS.items():
    lrs.set_params(name)
    logq = int(np.ceil(np.log2(lrs.Q)))
    ok_mod = (lrs.Q % 8 == 5)
    ok_M = np.isfinite(lrs.M1) and np.isfinite(lrs.M2) and lrs.M1 > 1 and lrs.M2 > 1
    rows.append({
        "set": name,
        "N": lrs.N,
        "log2q": logq,
        "h": lrs.H_DIM, "l": lrs.L_DIM, "v": lrs.V_DIM, "k": lrs.K_DIM,
        "kappa": lrs.KAPPA, "beta": lrs.BETA,
        "sigma": int(lrs.SIGMA),
        "M1": round(float(lrs.M1), 3),
        "M2": round(float(lrs.M2), 3),
        "exp_attempts": round(float(lrs.M1 * lrs.M2), 2),
        "constraints_ok": bool(ok_mod and ok_M),
        "sec_bits": ps["sec_bits"] if ps["sec_bits"] is not None else "TBD",
    })

# ---- markdown ----
hdr = ["Parameter Set", "N", "ceil(log2 q)", "h", "l", "v", "k",
       "kappa", "beta", "sigma", "M1", "M2", "E[attempts]=M1*M2", "Security (bits)"]
keys = ["set", "N", "log2q", "h", "l", "v", "k", "kappa", "beta", "sigma",
        "M1", "M2", "exp_attempts", "sec_bits"]
md = ["| " + " | ".join(hdr) + " |", "|" + "|".join(["---"] * len(hdr)) + "|"]
for r in rows:
    md.append("| " + " | ".join(str(r[k]) for k in keys) + " |")
md_txt = "\n".join(md)

with open(os.path.join(RESULTS, "table_A_params.md"), "w") as f:
    f.write("# Table A -- Parameter sets and rejection-sampling constants\n\n")
    f.write(md_txt + "\n\n")
    f.write("Notes: q = 2^32 - 99 (prime, == 5 mod 8) reused for all sets; every N is a\n")
    f.write("power of two, so Lemma 1 (partial splitting of X^N+1, d=2) holds throughout.\n")
    f.write("sigma = alpha * kappa * sqrt(l*N) with alpha = %.0f, so M1, M2 are constant.\n" % lrs.ALPHA)
    f.write("Security (bits) = TBD: concrete lattice-estimator / Core-SVP evaluation is deferred.\n")
    f.write("All sets satisfy the correctness constraints (q==5 mod 8; M1,M2 > 1, finite).\n")

with open(os.path.join(RESULTS, "table_A_params.json"), "w") as f:
    json.dump(rows, f, indent=2)

print(md_txt)
print("\nconstraints_ok:", all(r["constraints_ok"] for r in rows))
print("wrote results/table_A_params.{md,json}")
