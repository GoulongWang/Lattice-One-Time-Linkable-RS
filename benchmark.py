"""Benchmark one ring size; merge into benchmark_results.json.
Usage:  python3 benchmark.py <n> <reps>
"""
import sys, time, json, os, platform
import numpy as np
import lrs

n    = int(sys.argv[1])
reps = int(sys.argv[2]) if len(sys.argv) > 2 else 4
KG_REPS = 30
OUT = "benchmark_results.json"

rng = np.random.default_rng(2024 + n)
lrs._rng = np.random.default_rng(7 + n)

pp = lrs.setup(rng)

# KeyGen timing (ring-size independent)
t = []
for _ in range(KG_REPS):
    s = time.perf_counter(); lrs.keygen(pp, rng); t.append(time.perf_counter() - s)
keygen_ms = float(np.median(t) * 1e3)

keys = [lrs.keygen(pp, rng) for _ in range(n)]
L = [pk for (pk, sk, st) in keys]
pk, sk, st = keys[0]

sign_t, ver_t = [], []
for r in range(reps):
    msg = f"bm-{n}-{r}".encode()
    s = time.perf_counter(); sig, _ = lrs.sign(pp, msg, L, sk, None, 0); sign_t.append(time.perf_counter() - s)
    s = time.perf_counter(); v = lrs.verify(pp, msg, L, sig); ver_t.append(time.perf_counter() - s)
    assert v == 1
    print(f"  n={n} rep {r+1}/{reps}  sign={sign_t[-1]*1e3:7.1f}ms  verify={ver_t[-1]*1e3:7.1f}ms", flush=True)

pkb, skb, sgb = lrs.sizes_bits(n)
entry = {
    "keygen_ms": keygen_ms,
    "sign_ms":   float(np.median(sign_t) * 1e3),
    "verify_ms": float(np.median(ver_t) * 1e3),
    "pk_kb":  pkb / 8 / 1024,
    "sk_kb":  skb / 8 / 1024,
    "sig_kb": sgb / 8 / 1024,
}

data = {"env": platform.platform(), "results": {}}
if os.path.exists(OUT):
    with open(OUT) as f:
        data = json.load(f)
data.setdefault("results", {})[str(n)] = entry
with open(OUT, "w") as f:
    json.dump(data, f, indent=2)
print(f"  saved n={n}: {entry}", flush=True)
