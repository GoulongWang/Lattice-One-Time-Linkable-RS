"""Experiment B -- ring-size scaling benchmark (Table B).

Runs ONE (param-set, ring-size n) point per invocation and merges the result into
benchmark_full.json, so the full sweep can be built up across several short runs
(the sandbox caps each call at ~45 s).

Usage:  python3 benchmark_full.py <param_set> <n> [reps]
Example: python3 benchmark_full.py lrs-128 8 8

Measures KeyGen / Sign / Verify / Link (median + std, ms) and PK / SK / Signature
sizes (KB), plus the mean rejection-sampling attempt count per signature.
"""
import sys, time, json, os, platform, statistics
import numpy as np
import lrs

os.makedirs("results", exist_ok=True)

param = sys.argv[1]
n     = int(sys.argv[2])
reps  = int(sys.argv[3]) if len(sys.argv) > 3 else 8
BUDGET_S = float(sys.argv[4]) if len(sys.argv) > 4 else 30.0  # stop sign loop after this many s (>=3 reps)
KG_REPS   = 15
LINK_REPS = 50
OUT = "results/benchmark_full.json"

lrs.set_params(param)
rng = np.random.default_rng(2024 + n)
lrs._rng = np.random.default_rng(7 + n)

pp = lrs.setup(rng)

# --- KeyGen timing (ring-size independent) ---
kg = []
for _ in range(KG_REPS):
    s = time.perf_counter(); lrs.keygen(pp, rng); kg.append((time.perf_counter() - s) * 1e3)

keys = [lrs.keygen(pp, rng) for _ in range(n)]
L = [pk for (pk, sk, st) in keys]
pk, sk, st = keys[0]

# --- Sign / Verify timing + retry counts ---
# Sign loop threads the signer state so the timed signatures form a same-signer
# chain (msg differs each rep); the first two are reused for the Link benchmark,
# so Link costs no extra (expensive) signing.
sign_t, ver_t, retries = [], [], []
chain = []          # (msg, sig) for the same signer, state-chained
state = None
loop_start = time.perf_counter()
for r in range(reps):
    msg = f"bm-{param}-{n}-{r}".encode()
    s = time.perf_counter(); sig, state = lrs.sign(pp, msg, L, sk, state, 0); sign_t.append((time.perf_counter() - s) * 1e3)
    retries.append(lrs._LAST_RETRIES)
    s = time.perf_counter(); v = lrs.verify(pp, msg, L, sig); ver_t.append((time.perf_counter() - s) * 1e3)
    assert v == 1, "benchmark signature failed to verify"
    chain.append((msg, sig))
    print(f"  {param} n={n} rep {r+1}/{reps}  sign={sign_t[-1]:8.1f}ms  verify={ver_t[-1]:7.1f}ms  retries={retries[-1]}", flush=True)
    if r + 1 >= 3 and (time.perf_counter() - loop_start) > BUDGET_S:
        print(f"  [time budget {BUDGET_S}s reached after {r+1} reps -- stopping early]", flush=True)
        break

# --- Link timing: reuse the first two same-signer signatures from the chain ---
(mA, sigA), (mB, sigB) = chain[0], chain[1]
assert lrs.link(pp, mA, mB, L, L, sigA, sigB) == 1, "same-signer link failed"
link_t = []
for _ in range(LINK_REPS):
    s = time.perf_counter()
    lrs.link(pp, mA, mB, L, L, sigA, sigB)
    link_t.append((time.perf_counter() - s) * 1e3)

pkb, skb, sgb = lrs.sizes_bits(n)

def med_std(xs):
    return (float(statistics.median(xs)),
            float(statistics.pstdev(xs)) if len(xs) > 1 else 0.0)

kg_m, kg_s   = med_std(kg)
sg_m, sg_s   = med_std(sign_t)
vf_m, vf_s   = med_std(ver_t)
lk_m, lk_s   = med_std(link_t)

entry = {
    "param": param, "n": n, "reps": len(sign_t),
    "keygen_ms": kg_m, "keygen_std": kg_s,
    "sign_ms":   sg_m, "sign_std":   sg_s,
    "verify_ms": vf_m, "verify_std": vf_s,
    "link_ms":   lk_m, "link_std":   lk_s,
    "retries_mean": float(np.mean(retries)),
    "retries_all": retries,
    "pk_kb":  pkb / 8 / 1024,
    "sk_kb":  skb / 8 / 1024,
    "sig_kb": sgb / 8 / 1024,
}

data = {"env": platform.platform(), "python": platform.python_version(), "results": {}}
if os.path.exists(OUT):
    with open(OUT) as f:
        data = json.load(f)
data.setdefault("results", {})[f"{param}:{n}"] = entry
with open(OUT, "w") as f:
    json.dump(data, f, indent=2)

print(f"  -> KeyGen {kg_m:.2f}ms  Sign {sg_m:.1f}±{sg_s:.0f}ms  Verify {vf_m:.1f}ms  "
      f"Link {lk_m:.2f}ms  Sig {entry['sig_kb']:.1f}KB  retries~{entry['retries_mean']:.1f}")
