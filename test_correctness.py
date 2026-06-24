import numpy as np
import lrs

rng = np.random.default_rng(12345)
lrs._rng = np.random.default_rng(999)

print(f"q = {lrs.Q}  (q mod 8 = {lrs.Q % 8}),  N={lrs.N}")
print(f"M1={lrs.M1:.3f}  M2={lrs.M2:.3f}  (expected retry budget ~ M1*M2={lrs.M1*lrs.M2:.1f})\n")

pp = lrs.setup(rng)

# build a ring of n keypairs
n = 3
keys = [lrs.keygen(pp, rng) for _ in range(n)]
L = [pk for (pk, sk, s) in keys]

# --- 1. genuine signature verifies ---
signer = 1
pk, sk, st = keys[signer]
sig, st2 = lrs.sign(pp, b"vote-A", L, sk, st, signer)
v = lrs.verify(pp, b"vote-A", L, sig)
print(f"[1] genuine signature verifies      : {v}  (expect 1)")

# --- 2. tampered message fails ---
v_bad = lrs.verify(pp, b"vote-B", L, sig)
print(f"[2] wrong message rejected           : {v_bad}  (expect 0)")

# --- 3. two signatures from the SAME sk link ---
sig2, _ = lrs.sign(pp, b"claim-prize", L, sk, st2, signer)
ok2 = lrs.verify(pp, b"claim-prize", L, sig2)
lk = lrs.link(pp, b"vote-A", b"claim-prize", L, L, sig, sig2)
print(f"[3] 2nd signature verifies           : {ok2}  (expect 1)")
print(f"    Link(same signer) = {lk}  (expect 1)")

# --- 4. signatures from DIFFERENT sk do not link ---
pkB, skB, stB = keys[2]
sigB, _ = lrs.sign(pp, b"vote-A", L, skB, stB, 2)
lk2 = lrs.link(pp, b"vote-A", b"vote-A", L, L, sig, sigB)
print(f"[4] Link(different signers) = {lk2}  (expect 0)")

# --- 5. size check vs thesis Table 2 ---
print("\nSize check (formula, thesis Table 3):")
for nn, paper in [(1, 54.1), (8, 202.9), (32, 712.9)]:
    pkb, skb, sgb = lrs.sizes_bits(nn)
    print(f"  n={nn:<3} PK={pkb/8/1024:.2f}KB  SK={skb/8/1024:.2f}KB  "
          f"Sig={sgb/8/1024:.2f}KB  (paper {paper}KB)")
