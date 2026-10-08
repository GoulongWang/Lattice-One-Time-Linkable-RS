"""Resumable timing sweep over ring sizes: KeyGen / Sign / Verify / Link.

Ring sizes are the powers of two the thesis table and figure report. Evenly
spaced sizes (24, 40, 48, 56) used to be measured as well, to support a linear
fit in n; that fit is no longer reported anywhere, and those points cost more
than half the sweep, so they are gone.

Each invocation works through the job queue until --budget seconds elapse, saving
raw timings after every rep to results/raw.json (so it can be called
repeatedly; it resumes where it stopped).

Usage: python3 benchmark.py [budget_seconds]
"""
import sys, time, json, os, platform
import numpy as np
import lrs

RAW = "results/raw.json"
NS = [1, 2, 4, 8, 16, 32, 64]
PARAMS = ["lrs-1024", "lrs-2048"]
_SR = {"lrs-1024": 30, "lrs-2048": 20}
def sign_reps(param, n):   # lrs-2048 large rings cost ~10 s per signature, so fewer reps
    if param == "lrs-2048" and n >= 64: return 8
    return 12 if (param == "lrs-2048" and n >= 32) else _SR[param]
VERIFY_REPS = 30      # timed on each produced signature, cycled
KG_REPS, LINK_REPS = 30, 50
budget = float(sys.argv[1]) if len(sys.argv) > 1 else 160.0
t0 = time.perf_counter()

data = json.load(open(RAW)) if os.path.exists(RAW) else {
    "env": platform.platform(), "python": platform.python_version(),
    "numpy": np.__version__, "points": {}}
def save(): json.dump(data, open(RAW, "w"), indent=1)

_ctx = {}
def ctx(param, n):
    key = (param, n)
    if key not in _ctx:
        _ctx.clear()
        lrs.set_params(param)
        rng = np.random.default_rng(2024 + n)
        lrs._rng = np.random.default_rng(7 + n)
        pp = lrs.setup(rng)
        keys = [lrs.keygen(pp, rng) for _ in range(n)]
        _ctx[key] = (pp, rng, [k[0] for k in keys], keys[0][1])
    return _ctx[key]

def ms(f):
    s = time.perf_counter(); r = f(); return r, (time.perf_counter() - s) * 1e3

done_all = True
for param in PARAMS:
    for n in NS:
        P = data["points"].setdefault(f"{param}:{n}", {
            "param": param, "n": n, "keygen": [], "sign": [], "verify": [], "link": [],
            "state": None, "chain": 0})
        if len(P["sign"]) >= sign_reps(param, n) and len(P["link"]) >= LINK_REPS:
            continue
        if time.perf_counter() - t0 > budget:
            done_all = False; break
        pp, rng, L, sk = ctx(param, n)
        if not P["keygen"]:
            for _ in range(KG_REPS):
                P["keygen"].append(ms(lambda: lrs.keygen(pp, rng))[1])
        # Sign / Verify: fresh first-time signatures (state=None) for i.i.d. reps,
        # plus one second-time signature for Link (built once, below).
        while len(P["sign"]) < sign_reps(param, n):
            if time.perf_counter() - t0 > budget:
                break
            r = len(P["sign"])
            msg = f"rr-{param}-{n}-{r}".encode()
            (sig, st), t = ms(lambda: lrs.sign(pp, msg, L, sk, None, 0))
            P["sign"].append(t)
            vs = []
            for _ in range(max(1, VERIFY_REPS // sign_reps(param, n) + 1)):
                v, tv = ms(lambda: lrs.verify(pp, msg, L, sig)); assert v == 1; vs.append(tv)
            P["verify"].extend(vs)
            save()
        if len(P["sign"]) < sign_reps(param, n):
            done_all = False; break
        if len(P["link"]) < LINK_REPS:
            m1, m2 = b"link-first", b"link-second"
            s1, st = lrs.sign(pp, m1, L, sk, None, 0)
            s2, _ = lrs.sign(pp, m2, L, sk, st, 0)     # second-time sig carries r1-r2
            assert lrs.verify(pp, m2, L, s2) == 1
            assert lrs.link(pp, m1, m2, L, L, s1, s2) == 1
            for _ in range(LINK_REPS):
                P["link"].append(ms(lambda: lrs.link(pp, m1, m2, L, L, s1, s2))[1])
            pkb, skb, sgb = lrs.sizes_bits(n)
            P.update(pk_kb=pkb/8192, sk_kb=skb/8192, sig_kb=sgb/8192)
            save()
        print(f"{param} n={n}: sign {np.mean(P['sign']):.0f}ms verify {np.mean(P['verify']):.1f}ms "
              f"link {np.mean(P['link']):.1f}ms", flush=True)
    else:
        continue
    break
print("ALL DONE" if done_all else f"PAUSED after {time.perf_counter()-t0:.0f}s", flush=True)
