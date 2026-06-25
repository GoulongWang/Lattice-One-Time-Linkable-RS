"""Experiment C1 + C2 -- correctness gate and rejection-retry distribution.

For a given (param-set, ring-size n), run R independent trials.  Each trial:
  * sign a fresh message (state-chained to the previous trial -> same signer),
  * check Verify == 1,
  * check the chained pair Links (== 1) and a different-signer pair does NOT (==0).
Collect the rejection-sampling attempt count of every signature (C2).

Results merged into correctness_results.json keyed by "param:n".
Usage:  python3 correctness_gate.py <param_set> <n> [reps] [budget_s]
"""
import sys, json, os, time
import numpy as np
import lrs

os.makedirs("results", exist_ok=True)

param = sys.argv[1]
n     = int(sys.argv[2])
reps  = int(sys.argv[3]) if len(sys.argv) > 3 else 20
BUDGET_S = float(sys.argv[4]) if len(sys.argv) > 4 else 30.0
OUT = "results/correctness_results.json"

lrs.set_params(param)
rng = np.random.default_rng(100 + n)
lrs._rng = np.random.default_rng(200 + n)
pp = lrs.setup(rng)

# two signers: index 0 (chain under test) and index 1 (for non-link check)
keys = [lrs.keygen(pp, rng) for _ in range(max(n, 2))]
L = [pk for (pk, sk, st) in keys[:n]] if n >= 2 else [keys[0][0]]
# ensure ring has n members
while len(L) < n:
    L.append(lrs.keygen(pp, rng)[0])
sk0 = keys[0][1]
sk1 = keys[1][1]

verify_ok = link_ok = nonlink_ok = 0
retries = []
trials = 0
anchor = None         # (msg, sig) of the FIRST signature (the linkable-tag anchor)
state = None
# one different-signer signature, reused for the non-link test
sigD, _ = lrs.sign(pp, b"diff-signer", L, sk1, None, 1)

t0 = time.perf_counter()
for r in range(reps):
    msg = f"ct-{param}-{n}-{r}".encode()
    sig, state = lrs.sign(pp, msg, L, sk0, state, 0)
    retries.append(lrs._LAST_RETRIES)
    trials += 1
    if lrs.verify(pp, msg, L, sig) == 1:
        verify_ok += 1
    if anchor is not None:
        am, asig = anchor   # link each later signature against the first (same signer)
        if lrs.link(pp, am, msg, L, L, asig, sig) == 1:
            link_ok += 1
        if lrs.link(pp, msg, b"diff-signer", L, L, sig, sigD) == 0:
            nonlink_ok += 1
    else:
        anchor = (msg, sig)
    print(f"  {param} n={n} trial {r+1}/{reps}  verify_ok={verify_ok}  retries={retries[-1]}", flush=True)
    if r + 1 >= 5 and (time.perf_counter() - t0) > BUDGET_S:
        print(f"  [budget {BUDGET_S}s reached after {r+1} trials]", flush=True)
        break

link_trials = trials - 1   # link/non-link checks start from the 2nd trial
entry = {
    "param": param, "n": n, "trials": trials,
    "verify_success": f"{verify_ok}/{trials}",
    "verify_rate": verify_ok / trials,
    "link_success": f"{link_ok}/{link_trials}",
    "nonlink_success": f"{nonlink_ok}/{link_trials}",
    "all_pass": (verify_ok == trials and link_ok == link_trials and nonlink_ok == link_trials),
    "retries_mean": float(np.mean(retries)),
    "retries_max": int(np.max(retries)),
    "retries_all": retries,
    "M1M2_theory": float(lrs.M1 * lrs.M2),
}

data = {}
if os.path.exists(OUT):
    with open(OUT) as f:
        data = json.load(f)
data[f"{param}:{n}"] = entry
with open(OUT, "w") as f:
    json.dump(data, f, indent=2)

print(f"  -> verify {entry['verify_success']}  link {entry['link_success']}  "
      f"nonlink {entry['nonlink_success']}  all_pass={entry['all_pass']}  "
      f"retries mean {entry['retries_mean']:.1f} (theory {entry['M1M2_theory']:.1f}) max {entry['retries_max']}")
