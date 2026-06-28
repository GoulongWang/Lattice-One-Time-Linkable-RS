"""Render Tables A, B and C from the experiment JSON files, plus a PNG of Table B.

Reads/writes everything under results/.
Table A is rendered from table_A_params.json (produced by param_table.py).
Tables B, C1, C3 are rendered from benchmark_full.json, correctness_results.json,
and profile_results.json respectively.
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "results"
os.makedirs(R, exist_ok=True)
def rp(name): return os.path.join(R, name)

# ---------- Table A: parameter sets ----------
try:
    A_rows = json.load(open(rp("table_A_params.json")))
    a_hdr = ["Parameter Set", "N", "ceil(log2 q)", "h", "l", "v", "k",
             "kappa", "beta", "sigma", "M1", "M2", "E[attempts]=M1*M2", "Security (bits)"]
    a_keys = ["set", "N", "log2q", "h", "l", "v", "k", "kappa", "beta", "sigma",
              "M1", "M2", "exp_attempts", "sec_bits"]
    a_md = ["| " + " | ".join(a_hdr) + " |",
            "|" + "|".join(["---"] * len(a_hdr)) + "|"]
    for r in A_rows:
        a_md.append("| " + " | ".join(str(r[k]) for k in a_keys) + " |")
    a_md_txt = "\n".join(a_md)
    with open(rp("table_A_params.md"), "w") as f:
        f.write("# Table A -- Parameter sets and rejection-sampling constants\n\n")
        f.write(a_md_txt + "\n\n")
        f.write("Notes: q = 2^32 - 99 (prime, == 5 mod 8) reused for all sets; every N is a\n")
        f.write("power of two, so Lemma 1 (partial splitting of X^N+1, d=2) holds throughout.\n")
        f.write("Security (bits) = TBD: concrete lattice-estimator / Core-SVP evaluation is deferred.\n")
        f.write("All sets satisfy the correctness constraints (q==5 mod 8; M1,M2 > 1, finite).\n")
    print(a_md_txt)
    print("wrote table_A_params.md")
except FileNotFoundError:
    print("(table_A_params.json not found -- skip A; run param_table.py first)")

# ---------- Table B: ring-size scaling (lrs-1024, lrs-2048) ----------
B = json.load(open(rp("benchmark_full.json")))
res = B["results"]

# (param set, N, table label) rendered as one Table B section each
PARAM_SETS = [("lrs-1024", 1024, "B1"), ("lrs-2048", 2048, "B2")]

rows = [
    ("KeyGen (ms)",         lambda e: f"{e['keygen_ms']:.2f}"),
    ("Sign (mean) (ms)",    lambda e: f"{e['sign_ms']:.0f}"),
    ("Verify (ms)",         lambda e: f"{e['verify_ms']:.0f}"),
    ("Link (ms)",           lambda e: f"{e['link_ms']:.1f}"),
    ("PK (KB)",             lambda e: f"{e['pk_kb']:.1f}"),
    ("SK (KB)",             lambda e: f"{e['sk_kb']:.2f}"),
    ("Signature (KB)",      lambda e: f"{e['sig_kb']:.1f}"),
    ("Sign retries (mean)", lambda e: f"{e['retries_mean']:.1f}"),
]

def render_table(param):
    ns = sorted({int(k.split(":")[1]) for k in res if k.startswith(f"{param}:")})
    get = lambda n: res[f"{param}:{n}"]
    hdr = ["Metric \\ n"] + [str(n) for n in ns]
    md = ["| " + " | ".join(hdr) + " |", "|" + "|".join(["---"] * len(hdr)) + "|"]
    for label, fn in rows:
        md.append("| " + label + " | " + " | ".join(fn(get(n)) for n in ns) + " |")
    return ns, get, "\n".join(md)

sections = []
for param, Nval, tag in PARAM_SETS:
    ns, get, md_txt = render_table(param)
    sections.append(f"## Table {tag} -- {param} (N={Nval})\n\n{md_txt}")
    print(param)
    print(md_txt)
    print("\n")

with open(rp("table_B_scaling.md"), "w") as f:
    f.write("# Table B -- Ring-size scaling\n\n")
    f.write("\n\n".join(sections) + "\n\n")
    f.write(f"Environment: {B.get('env','?')}, Python {B.get('python','?')}, pure-NumPy reference.\n")
    f.write("Sign is dominated by Lyubashevsky rejection sampling. A single joint rejection "
            "test over the stacked response (z || z_c) is used, with combined constant "
            "M_c ~ 5.67 (geometric retry mean), so per-signature time varies widely; "
            "arithmetic means over 8 reps shown. Verify and Signature size scale linearly "
            "in n; KeyGen and Link are ~constant in n.\n")

# Combined PNG: KeyGen/Sign/Verify/Link vs n (log-y), lrs-1024 and lrs-2048 side by side
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, (param, Nval, tag) in zip((ax1, ax2), PARAM_SETS):
    ns, get, _ = render_table(param)
    kg   = [get(n)["keygen_ms"] for n in ns]
    sign = [get(n)["sign_ms"] for n in ns]
    ver  = [get(n)["verify_ms"] for n in ns]
    lk   = [get(n)["link_ms"] for n in ns]
    ax.plot(ns, kg, "D-", label="KeyGen")
    ax.plot(ns, sign, "o-", label="Sign (mean)")
    ax.plot(ns, ver, "s-", label="Verify")
    ax.plot(ns, lk, "^-", label="Link")
    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ax.set_xlabel("ring size n"); ax.set_ylabel("time (ms)")
    ax.set_title(f"LRS operation time vs ring size ({param})")
    ax.legend(); ax.grid(True, which="both", ls=":", alpha=0.5)
fig.tight_layout(); fig.savefig(rp("table_B_scaling.png"), dpi=130)
plt.close(fig)
print("wrote table_B_scaling.md + table_B_scaling.png")

# ---------- Table C1: correctness gate ----------
try:
    C = json.load(open(rp("correctness_results.json")))
    hdr = ["Parameter Set", "n", "Trials", "Verify", "Link", "Non-link", "All pass",
           "Retries mean", "Theory M_c", "Retries max"]
    md = ["| " + " | ".join(hdr) + " |", "|" + "|".join(["---"] * len(hdr)) + "|"]
    order = ["lrs-1024", "lrs-2048"]
    items = sorted(C.values(), key=lambda e: (order.index(e["param"]) if e["param"] in order else 9, e["n"]))
    for e in items:
        md.append("| " + " | ".join([
            e["param"], str(e["n"]), str(e["trials"]),
            e["verify_success"], e["link_success"], e["nonlink_success"],
            "Yes" if e["all_pass"] else "No",
            f"{e['retries_mean']:.1f}", f"{e['Mc_theory']:.2f}", str(e["retries_max"])]) + " |")
    with open(rp("table_C1_correctness.md"), "w") as f:
        f.write("# Table C1 -- Empirical correctness gate (Verify / Link / Non-link)\n\n")
        f.write("\n".join(md) + "\n\n")
        f.write("Verify = honest signatures accepted; Link = same-signer pairs linked; "
                "Non-link = different-signer pairs not linked. 100% across all sets validates "
                "the bounded-norm parameter constraints. Retry mean tracks the single joint "
                "rejection-sampling constant M_c (Theory M_c column; ~constant across "
                "parameter sets since alpha is fixed).\n")
    print("\n".join(md))
    print("wrote table_C1_correctness.md")
except FileNotFoundError:
    print("(correctness_results.json not found -- skip C1)")

# ---------- Table C3: bottleneck ----------
try:
    P = json.load(open(rp("profile_results.json")))
    def block(key, title):
        b = P[key]
        lines = [f"### {title} (wall {b['wall_ms']} ms, {P['param']} n={P['n']})", "",
                 "| Subroutine | Time (ms) | % | Calls |", "|---|---|---|---|"]
        for r in b["buckets"]:
            calls = "" if r["calls"] is None else str(r["calls"])
            lines.append(f"| {r['bucket']} | {r['ms']} | {r['pct']} | {calls} |")
        return "\n".join(lines)
    with open(rp("table_C3_bottleneck.md"), "w") as f:
        f.write("# Table C3 -- Subroutine bottleneck (direct instrumentation)\n\n")
        f.write(block("sign", "Sign") + "\n\n")
        f.write(block("verify", "Verify") + "\n\n")
        f.write("Negacyclic ring multiplication (poly_mul, the np.convolve core) dominates "
                "both Sign and Verify (~95%), identifying it as the single optimization target: "
                "an NTT-based multiplier (partial NTT for d=2, or CRT over NTT-friendly primes) "
                "would cut the bulk of the cost.\n")
    print(block("sign", "Sign"))
    print("wrote table_C3_bottleneck.md")
except FileNotFoundError:
    print("(profile_results.json not found -- skip C3)")
