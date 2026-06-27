"""
Reference implementation (proof-of-concept) of the lattice-based commitment-tag
Linkable Ring Signature from the thesis:
    "Post-Quantum Linkable Ring Signatures Based on Lattice" (Guolong Wang, NCCU).

Implements Setup / KeyGen / Sign / Verify / Link (Algorithms 1-5) over
R_q = Z_q[X]/(X^N + 1) with the parameter set fixed in the thesis (Table 2):

    q ~ 2^32 (prime, q = 5 mod 8 so Lemma 1 holds with d=2)
    N = 1024,  h = 1,  l = 4,  v = 1,  k = 6
    kappa = 45 (challenge l1 weight),  beta = 1 (ternary sk, r),  sigma = 31680

This is a *correctness + benchmark* reference, not constant-time / optimised code.
Polynomial multiplication uses NumPy int64 negacyclic convolution; an overflow
analysis (matrix entries ~2^31 times short Gaussian/ternary vectors) shows partial
sums stay below 2^63, so int64 is exact here.
"""

import numpy as np
import hashlib
import time

# ----------------------------------------------------------------------------
# Parameter sets
# ----------------------------------------------------------------------------
# Security in this family scales primarily with the polynomial degree N (lattice
# dimension ~ N * module-rank) and the module ranks (l, k).  We expose several
# sets at different N; the Gaussian width sigma is scaled as alpha * kappa *
# sqrt(l*N) with a FIXED alpha so the rejection constants M1, M2 stay constant
# across sets (well-behaved retry count).  alpha = 11 reproduces the thesis
# Table-2 value sigma = 31680 at N = 1024.
#
# q = 2^32 - 99 is prime and == 5 (mod 8); since every N here is a power of two,
# Lemma 1 (partial splitting of X^N+1, d=2) holds for all sets with this q, so a
# single modulus is reused.  The "sec_bits" field is left as None (TBD): concrete
# security estimation (lattice-estimator / Core-SVP) is deferred to future work.
ALPHA = 11.0                 # sigma / (kappa * sqrt(l*N));  alpha=11 -> M1~2.99
Q_DEFAULT = 4294967197       # = 2^32 - 99, prime, == 5 (mod 8)

def _make_set(N, l=4, k=6, h=1, v=1, kappa=45, beta=1, q=Q_DEFAULT, alpha=ALPHA):
    sigma = round(alpha * kappa * np.sqrt(l * N))
    return {"N": N, "Q": q, "H_DIM": h, "L_DIM": l, "V_DIM": v, "K_DIM": k,
            "KAPPA": kappa, "BETA": beta, "SIGMA": float(sigma), "sec_bits": None}

PARAM_SETS = {
    # lower-security lightweight proof-of-concept set
    "lrs-512": _make_set(N=512),
    # thesis Table-2 baseline (sigma rounds to the published 31680)
    "lrs-1024":   _make_set(N=1024),
    # higher-security set
    "lrs-2048":   _make_set(N=2048),
}

# Module globals are (re)bound by set_params(); a default is set at import time
# below so existing scripts that `import lrs` keep working unchanged.
N = Q = QH = H_DIM = L_DIM = V_DIM = K_DIM = KAPPA = BETA = SIGMA = None
T1 = T2 = A1 = A2 = M1 = M2 = None
PARAM_NAME = None

def set_params(name):
    """Rebind module-level parameter globals to the named set in PARAM_SETS."""
    global N, Q, QH, H_DIM, L_DIM, V_DIM, K_DIM, KAPPA, BETA, SIGMA
    global T1, T2, A1, A2, M1, M2, PARAM_NAME
    ps = PARAM_SETS[name] if isinstance(name, str) else name
    PARAM_NAME = name if isinstance(name, str) else "custom"
    N = ps["N"]; Q = ps["Q"]
    H_DIM = ps["H_DIM"]; L_DIM = ps["L_DIM"]; V_DIM = ps["V_DIM"]; K_DIM = ps["K_DIM"]
    KAPPA = ps["KAPPA"]; BETA = ps["BETA"]; SIGMA = ps["SIGMA"]
    assert Q % 8 == 5, "q must be == 5 (mod 8) for Lemma 1 (partial splitting, d=2)"
    QH = Q // 2  # for centered reduction
    # rejection-sampling repetition constants M (Theorem 1), from sigma = alpha*T:
    #   z_j   center v = d*sk,  T  = kappa*sqrt(l*N)
    #   z_c,j center v = d*r2,  T2 = kappa*sqrt(k*N)
    T1 = KAPPA * np.sqrt(L_DIM * N)
    T2 = KAPPA * np.sqrt(K_DIM * N)
    A1 = SIGMA / T1
    A2 = SIGMA / T2
    M1 = np.exp(12.0 / A1 + 1.0 / (2 * A1 * A1))
    M2 = np.exp(12.0 / A2 + 1.0 / (2 * A2 * A2))

set_params("lrs-1024")  # default: thesis Table-2 baseline (backward compatible)

# ----------------------------------------------------------------------------
# Ring arithmetic over R_q = Z_q[X]/(X^N + 1).  A polynomial is an int64[N].
# ----------------------------------------------------------------------------
def center(a):
    """Centered representative in (-q/2, q/2]."""
    a = a % Q
    a = np.where(a > QH, a - Q, a)
    return a.astype(np.int64)

def poly_mul(a, b):
    """Negacyclic multiplication a*b mod (X^N+1) mod q, exact via int64."""
    # full convolution length 2N-1
    conv = np.convolve(a.astype(np.int64), b.astype(np.int64))
    res = np.zeros(N, dtype=np.int64)
    res[:N] = conv[:N]
    # wrap: X^N = -1
    res[:N - 1] -= conv[N:2 * N - 1]
    return center(res)

def poly_add(a, b):
    return center(a + b)

def poly_sub(a, b):
    return center(a - b)

# vector = list of polynomials;  matrix = list of rows, each row a list of polys
def matvec(mat, vec):
    """mat (rows x cols) times vec (cols) -> result (rows) over R_q."""
    out = []
    for row in mat:
        acc = np.zeros(N, dtype=np.int64)
        for aij, vj in zip(row, vec):
            acc = acc + poly_mul(aij, vj)
        out.append(center(acc))
    return out

def vec_add(u, w):
    return [poly_add(a, b) for a, b in zip(u, w)]

def vec_sub(u, w):
    return [poly_sub(a, b) for a, b in zip(u, w)]

def scalar_vec(c, vec):
    """polynomial c times each entry of vec."""
    return [poly_mul(c, v) for v in vec]

# ----------------------------------------------------------------------------
# Samplers
# ----------------------------------------------------------------------------
_rng = np.random.default_rng()

def sample_uniform_poly(rng):
    return center(rng.integers(0, Q, size=N, dtype=np.int64))

def sample_uniform_vec(rng, dim):
    return [sample_uniform_poly(rng) for _ in range(dim)]

def sample_uniform_mat(rng, rows, cols):
    return [[sample_uniform_poly(rng) for _ in range(cols)] for _ in range(rows)]

def sample_ternary_vec(rng, dim):
    """S_beta^dim, beta=1 : coefficients uniform in {-1,0,1}."""
    return [rng.integers(-BETA, BETA + 1, size=N, dtype=np.int64) for _ in range(dim)]

def sample_gaussian_vec(rng, dim, sigma=SIGMA):
    """Discrete Gaussian (rounded continuous) of width sigma, dim polynomials."""
    return [np.rint(rng.normal(0.0, sigma, size=N)).astype(np.int64) for _ in range(dim)]

def sample_challenge(seed_bytes):
    """C = { c in R : l_inf=1, l1 = kappa }.  Deterministic from seed."""
    rng = np.random.default_rng(int.from_bytes(hashlib.sha256(seed_bytes).digest()[:8], "little"))
    c = np.zeros(N, dtype=np.int64)
    positions = rng.choice(N, size=KAPPA, replace=False)
    signs = rng.integers(0, 2, size=KAPPA) * 2 - 1
    c[positions] = signs
    return c

# ----------------------------------------------------------------------------
# Hashes.  H : {0,1}* -> S_beta^k  (ternary);  H2 : {0,1}* -> C (challenge)
# ----------------------------------------------------------------------------
def _digest(*parts):
    h = hashlib.shake_256()
    for p in parts:
        if isinstance(p, (bytes, bytearray)):
            h.update(p)
        elif isinstance(p, np.ndarray):
            h.update(p.astype(np.int64).tobytes())
        elif isinstance(p, list):
            for x in p:
                h.update(np.asarray(x, dtype=np.int64).tobytes())
        else:
            h.update(str(p).encode())
    return h

def H_ternary(*parts):
    """Hash to S_beta^k : k ternary polynomials."""
    raw = _digest(b"H", *parts).digest(K_DIM * N)
    arr = np.frombuffer(raw, dtype=np.uint8).astype(np.int64)
    arr = (arr % 3) - 1  # {0,1,2} -> {-1,0,1}
    return [arr[i * N:(i + 1) * N].copy() for i in range(K_DIM)]

def H2_challenge(*parts):
    seed = _digest(b"H2", *parts).digest(32)
    return sample_challenge(seed)

def tag_challenge(t1, t2, c1, c2, m, L):
    """Challenge d used for the linkable tag (shared by Sign line 11 and Link)."""
    return H2_challenge(b"TAG", _vecbytes(t1), _vecbytes(t2),
                        _vecbytes(c1, c2), m, _vecbytes(*L))

def _vecbytes(*vecs):
    """Stable byte encoding of polynomial vectors for hashing."""
    out = bytearray()
    for v in vecs:
        for p in v:
            out += center(np.asarray(p)).tobytes()
    return bytes(out)

# ----------------------------------------------------------------------------
# Scheme : Algorithms 1-5
# ----------------------------------------------------------------------------
def setup(rng=None):
    rng = rng or _rng
    A  = sample_uniform_mat(rng, H_DIM, L_DIM)                  # h x l
    # B1 = [ I_v | B1' ]   (v x k)
    B1 = []
    for i in range(V_DIM):
        row = []
        for j in range(K_DIM):
            if j < V_DIM:
                p = np.zeros(N, dtype=np.int64); p[0] = 1 if j == i else 0
                row.append(p)
            else:
                row.append(sample_uniform_poly(rng))
        B1.append(row)
    # B2 = [ 0^{l x v} | I_l | B2' ]   (l x k)
    B2 = []
    for i in range(L_DIM):
        row = []
        for j in range(K_DIM):
            if j < V_DIM:
                row.append(np.zeros(N, dtype=np.int64))
            elif j < V_DIM + L_DIM:
                p = np.zeros(N, dtype=np.int64); p[0] = 1 if (j - V_DIM) == i else 0
                row.append(p)
            else:
                row.append(sample_uniform_poly(rng))
        B2.append(row)
    return {"A": A, "B1": B1, "B2": B2}

def keygen(pp, rng=None):
    rng = rng or _rng
    sk = sample_ternary_vec(rng, L_DIM)        # S_beta^l
    pk = matvec(pp["A"], sk)                    # h
    return pk, sk, None  # state s = None (bottom)

def commit(pp, x_vec, r_vec):
    """Com(x; r): c1 = B1 r (v),  c2 = B2 r + x (l)."""
    c1 = matvec(pp["B1"], r_vec)
    c2 = vec_add(matvec(pp["B2"], r_vec), x_vec)
    return c1, c2

def _rej_accept(z_polys, v_polys, sigma, M):
    """Lyubashevsky rejection sampling acceptance test."""
    z = np.concatenate([np.asarray(p, dtype=np.float64) for p in z_polys])
    vv = np.concatenate([np.asarray(p, dtype=np.float64) for p in v_polys])
    inner = float(np.dot(z, vv))
    nv2 = float(np.dot(vv, vv))
    val = np.exp((-2.0 * inner + nv2) / (2.0 * sigma * sigma)) / M
    return _rng.random() < min(1.0, val)

# instrumentation: number of rejection-sampling attempts used by the last sign()
_LAST_RETRIES = 0

def sign(pp, m, L, sk, state, signer_index, rng=None, _max_retry=400):
    """Algorithm 3.  L is list of public keys (each a vec of h polys)."""
    global _LAST_RETRIES
    rng = rng or _rng
    n = len(L)
    j = signer_index

    # ---- linkable tag (first-signature path: s = bottom) -------------------
    if state is None:
        r1 = H_ternary(_vecbytes(sk), m, _vecbytes(*L))
        r2 = r1
        new_state = (m, L)
    else:
        m1, L1 = state
        r1 = H_ternary(_vecbytes(sk), m1, _vecbytes(*L1))
        r2 = H_ternary(_vecbytes(sk), m, _vecbytes(*L))
        new_state = state
    c1, c2 = commit(pp, sk, r2)                       # c = Com(sk; r2)

    for _attempt in range(_max_retry):
        y = sample_gaussian_vec(rng, K_DIM)
        B1y = matvec(pp["B1"], y)
        B2y = matvec(pp["B2"], y)
        d_tag = tag_challenge(B1y, B2y, c1, c2, m, L)
        r_diff = vec_sub(r1, r2)
        z_tag = vec_add(y, scalar_vec(d_tag, r_diff))   # = y when r1=r2
        I = {"z": z_tag, "d": d_tag, "c1": c1, "c2": c2}

        # ---- ring (AOS chaining) -------------------------------------------
        u   = sample_gaussian_vec(rng, L_DIM)
        u_c = sample_gaussian_vec(rng, K_DIM)
        d = [None] * n
        z   = [None] * n
        z_c = [None] * n
        a_j = matvec(pp["A"],  u)
        b_j = matvec(pp["B1"], u_c)
        g_j = vec_add(matvec(pp["B2"], u_c), u)
        d[(j + 1) % n] = H2_challenge(_vecbytes(*L), _tagbytes(I), m,
                                      _vecbytes(a_j), _vecbytes(b_j), _vecbytes(g_j))
        i = (j + 1) % n
        while i != j:
            z[i]   = sample_gaussian_vec(rng, L_DIM)
            z_c[i] = sample_gaussian_vec(rng, K_DIM)
            alpha = vec_sub(matvec(pp["A"], z[i]),  scalar_vec(d[i], L[i]))
            beta  = vec_sub(matvec(pp["B1"], z_c[i]), scalar_vec(d[i], c1))
            gamma = vec_sub(vec_add(matvec(pp["B2"], z_c[i]), z[i]), scalar_vec(d[i], c2))
            d[(i + 1) % n] = H2_challenge(_vecbytes(*L), _tagbytes(I), m,
                                          _vecbytes(alpha), _vecbytes(beta), _vecbytes(gamma))
            i = (i + 1) % n

        # signer responses
        z[j]   = vec_add(u,   scalar_vec(d[j], sk))
        z_c[j] = vec_add(u_c, scalar_vec(d[j], r2))

        # rejection sampling (Theorem 1)
        v1 = scalar_vec(d[j], sk)
        v2 = scalar_vec(d[j], r2)
        if not _rej_accept(z[j], v1, SIGMA, M1):
            continue
        if not _rej_accept(z_c[j], v2, SIGMA, M2):
            continue

        sig = {"d1": d[0], "z": z, "z_c": z_c, "I": I}
        _LAST_RETRIES = _attempt + 1   # total attempts incl. the accepted one
        return sig, new_state
    raise RuntimeError("signing exceeded retry budget")

def _tagbytes(I):
    return _vecbytes(I["z"]) + _vecbytes([I["d"]]) + _vecbytes(I["c1"], I["c2"])

def _norm2(polys):
    z = np.concatenate([np.asarray(p, dtype=np.float64) for p in polys])
    return float(np.sqrt(np.dot(z, z)))

def verify(pp, m, L, sig):
    n = len(L)
    bound_z   = 2 * SIGMA * np.sqrt(L_DIM * N)
    bound_zc  = 2 * SIGMA * np.sqrt(K_DIM * N)
    for i in range(n):
        if _norm2(sig["z"][i]) > bound_z:   return 0
        if _norm2(sig["z_c"][i]) > bound_zc: return 0
    I = sig["I"]
    c1, c2 = I["c1"], I["c2"]
    e = sig["d1"]
    for i in range(n):
        alpha = vec_sub(matvec(pp["A"], sig["z"][i]),  scalar_vec(e, L[i]))
        beta  = vec_sub(matvec(pp["B1"], sig["z_c"][i]), scalar_vec(e, c1))
        gamma = vec_sub(vec_add(matvec(pp["B2"], sig["z_c"][i]), sig["z"][i]), scalar_vec(e, c2))
        e = H2_challenge(_vecbytes(*L), _tagbytes(I), m,
                         _vecbytes(alpha), _vecbytes(beta), _vecbytes(gamma))
    return 1 if all(np.array_equal(a, b) for a, b in zip(e, sig["d1"])) else 0

def _link_branch(pp, carrier, other, m_carrier, L_carrier, bound):
    """Test whether `carrier` is the difference-carrying (2nd) signature.

    For the 2nd signature: z = y + d*(r1 - r2), c = Com(sk; r2), and the other
    commitment is Com(sk; r1).  Then  c_other - c_carrier = Com(0; r1 - r2),
    so  B*z - d*(c_other - c_carrier) = B*y, and  tag_challenge(B*y,...) == d.
    """
    c1, c2 = carrier["c1"], carrier["c2"]
    co1, co2 = other["c1"], other["c2"]
    z, d = carrier["z"], carrier["d"]
    if _norm2(z) > bound:
        return False
    d1 = vec_sub(co1, c1)          # delta = c_other - c_carrier
    d2 = vec_sub(co2, c2)
    t1 = vec_sub(matvec(pp["B1"], z), scalar_vec(d, d1))
    t2 = vec_sub(matvec(pp["B2"], z), scalar_vec(d, d2))
    chk = tag_challenge(t1, t2, c1, c2, m_carrier, L_carrier)
    return np.array_equal(chk, d)

def link(pp, m, mp, L, Lp, sig, sigp):
    """Algorithm 5.  Returns 1 if both signatures come from the same signer.

    The signing order is unknown, so we test both assignments of which tag is
    the difference-carrying (second) signature.
    """
    bound = 2 * SIGMA * np.sqrt(K_DIM * N)
    I, Ip = sig["I"], sigp["I"]
    if _link_branch(pp, Ip, I, mp, Lp, bound):   # sigp is the 2nd signature
        return 1
    if _link_branch(pp, I, Ip, m, L, bound):     # sig  is the 2nd signature
        return 1
    return 0

# ----------------------------------------------------------------------------
# Size accounting (bits) — matches thesis Table 3 formula
# ----------------------------------------------------------------------------
def sizes_bits(n):
    logq      = int(np.ceil(np.log2(Q)))           # ~32
    log4sigma = int(np.ceil(np.log2(4 * SIGMA)))   # 17
    pk = H_DIM * N * logq
    sk = 2 * L_DIM * N                              # 2 bits per ternary coeff
    sig = (n * (K_DIM + L_DIM) + K_DIM) * N * log4sigma + (V_DIM + L_DIM) * N * logq
    return pk, sk, sig
