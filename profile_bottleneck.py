"""Experiment C3 -- subroutine bottleneck profiling (direct instrumentation).

Wraps the scheme's key subroutines with accumulating timers + call counters and
runs one Sign and one Verify (default lrs-128, n=8).  This attributes wall time to
scheme-level operations directly (cProfile pushes numpy's C-level convolution into
an opaque "other" bucket, so we time the Python entry points instead):
  poly_mul        -- negacyclic ring multiplication (the np.convolve core),
  Gaussian sample -- discrete-Gaussian vector sampling,
  SHAKE hashing   -- H / H2 / tag challenge hashing.
Everything not captured is reported as "other (glue/arith)".
Outputs profile_results.json + a printed table.
"""
import sys, json, time, os
import numpy as np
import lrs

os.makedirs("results", exist_ok=True)

param = sys.argv[1] if len(sys.argv) > 1 else "lrs-128"
n     = int(sys.argv[2]) if len(sys.argv) > 2 else 8
lrs.set_params(param)

# ---- instrument: wrap subroutines with timer + counter ----------------------
STATS = {}   # name -> [total_seconds, calls]
def _wrap(modname, label):
    orig = getattr(lrs, modname)
    STATS[label] = [0.0, 0]
    def wrapped(*a, **k):
        s = time.perf_counter()
        r = orig(*a, **k)
        STATS[label][0] += time.perf_counter() - s
        STATS[label][1] += 1
        return r
    setattr(lrs, modname, wrapped)
    return orig

orig_poly  = _wrap("poly_mul", "poly_mul (ring mult)")
orig_gauss = _wrap("sample_gaussian_vec", "Gaussian sampling")
orig_h2    = _wrap("H2_challenge", "SHAKE-256 hashing (H2)")
orig_ht    = _wrap("H_ternary", "SHAKE-256 hashing (H)")

rng = np.random.default_rng(11)
lrs._rng = np.random.default_rng(22)
pp = lrs.setup(rng)
keys = [lrs.keygen(pp, rng) for _ in range(n)]
L = [pk for (pk, sk, st) in keys]
sk = keys[0][1]

def reset():
    for k in STATS:
        STATS[k][0] = 0.0; STATS[k][1] = 0

def report(label, wall):
    measured = sum(v[0] for v in STATS.values())
    rows = []
    for k, (t, c) in sorted(STATS.items(), key=lambda kv: -kv[1][0]):
        rows.append({"bucket": k, "ms": round(t * 1e3, 2),
                     "pct": round(100 * t / wall, 1), "calls": c})
    other = wall - measured
    rows.append({"bucket": "other (glue/arith)", "ms": round(other * 1e3, 2),
                 "pct": round(100 * other / wall, 1), "calls": None})
    print(f"\n=== {label} ({param}, n={n}) wall {wall*1e3:.0f} ms ===")
    for r in rows:
        c = "" if r["calls"] is None else f"  x{r['calls']}"
        print(f"  {r['bucket']:26s} {r['ms']:8.1f} ms  {r['pct']:5.1f}%{c}")
    return {"label": label, "wall_ms": round(wall * 1e3, 1), "buckets": rows}

# ---- Sign ----
lrs._rng = np.random.default_rng(123)
reset()
s = time.perf_counter()
sig, _ = lrs.sign(pp, b"profile-msg", L, sk, None, 0, rng=np.random.default_rng(123))
sign_res = report("Sign", time.perf_counter() - s)
sign_retries = lrs._LAST_RETRIES

# ---- Verify ----
reset()
s = time.perf_counter()
lrs.verify(pp, b"profile-msg", L, sig)
ver_res = report("Verify", time.perf_counter() - s)

out = {"param": param, "n": n, "sign_retries": sign_retries,
       "sign": sign_res, "verify": ver_res}
with open("results/profile_results.json", "w") as f:
    json.dump(out, f, indent=2)
print(f"\n(sign used {sign_retries} rejection attempt(s))")
print("wrote results/profile_results.json")
