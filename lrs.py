"""
Post-Quantum Linkable Ring Signatures Based on Lattice 論文 PoC 實作
Author: Guolong Wang
"""

import numpy as np
import hashlib

# 參數集詳見論文
ALPHA = 11.0 # alpha = sigma / (kappa * sqrt(l*N))  => M = 5.67, M_z = 14.83
Q_DEFAULT = 1099511627581 # q = 2^40 - 195

def _make_set(N, l = 4, k = 6, h = 1, v = 1, kappa = 45, beta = 1, q = Q_DEFAULT, alpha = ALPHA):
    sigma = round(alpha * kappa * np.sqrt(l * N))
    return {"N": N, "Q": q, "H_DIM": h, "L_DIM": l, "V_DIM": v, "K_DIM": k, "KAPPA": kappa, "BETA": beta, "SIGMA": float(sigma)}

PARAM_SETS = {"lrs-1024": _make_set(N = 1024), "lrs-2048": _make_set(N = 2048)}

N = Q = QH = H_DIM = L_DIM = V_DIM = K_DIM = KAPPA = BETA = SIGMA = None
T2 = None             # kappa * sqrt(k * N)：環簽章回應 z_c 中 d*r2 的上界
TC = AC = M = None    # 環簽章的拒絕採樣常數 M
TZ = AZ = MZ = None   # 連結標記的拒絕採樣常數
PARAM_NAME = None

def set_params(name):
    global N, Q, QH, H_DIM, L_DIM, V_DIM, K_DIM, KAPPA, BETA, SIGMA
    global T2, TC, AC, M, TZ, AZ, MZ, PARAM_NAME
    ps = PARAM_SETS[name] if isinstance(name, str) else name
    PARAM_NAME = name if isinstance(name, str) else "custom"
    N = ps["N"]; Q = ps["Q"]
    H_DIM = ps["H_DIM"]; L_DIM = ps["L_DIM"]; V_DIM = ps["V_DIM"]; K_DIM = ps["K_DIM"]
    KAPPA = ps["KAPPA"]; BETA = ps["BETA"]; SIGMA = ps["SIGMA"]
    assert Q % 8 == 5, "q == 5 (mod 8) for Lemma 1"
    QH = Q // 2

    # 拒絕採樣常數
    T2 = KAPPA * np.sqrt(K_DIM * N)
    TC = KAPPA * np.sqrt((L_DIM + K_DIM) * N)
    AC = SIGMA / TC
    M = np.exp(12.0 / AC + 1.0 / (2 * AC * AC))
    TZ = 2.0 * T2
    AZ = SIGMA / TZ
    MZ = np.exp(12.0 / AZ + 1.0 / (2 * AZ * AZ))
    _check_int64_headroom()

def _check_int64_headroom():
    est = 2.0 * (Q / 2.0) * SIGMA * np.sqrt(N)
    if est >= 2.0 ** 62:
        print("卷積溢位警告")

set_params("lrs-1024")

# ----------------------------------------------------------------------------
# R_q = Z_q[X]/(X^N + 1) 環多項式運算
# ----------------------------------------------------------------------------
def center(a):
    # (-q/2, q/2]
    a = a % Q
    a = np.where(a > QH, a - Q, a)
    return a.astype(np.int64)

def poly_mul(a, b):
    conv = np.convolve(a.astype(np.int64), b.astype(np.int64))
    res = np.zeros(N, dtype=np.int64)
    res[:N] = conv[:N]
    # X^N = -1
    res[:N - 1] -= conv[N:2 * N - 1]
    return center(res)

def poly_add(a, b):
    return center(a + b)

def poly_sub(a, b):
    return center(a - b)

def matvec(mat, vec):
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
    return [poly_mul(c, v) for v in vec]

# ----------------------------------------------------------------------------
# 取樣
# ----------------------------------------------------------------------------
_rng = np.random.default_rng()

def sample_uniform_poly(rng):
    return center(rng.integers(0, Q, size=N, dtype=np.int64))

def sample_uniform_vec(rng, dim):
    return [sample_uniform_poly(rng) for _ in range(dim)]

def sample_uniform_mat(rng, rows, cols):
    return [[sample_uniform_poly(rng) for _ in range(cols)] for _ in range(rows)]

def sample_ternary_vec(rng, dim):
    # 係數 {-1,0,1}
    return [rng.integers(-BETA, BETA + 1, size=N, dtype=np.int64) for _ in range(dim)]

def sample_gaussian_vec(rng, dim, sigma=SIGMA):
    return [np.rint(rng.normal(0.0, sigma, size=N)).astype(np.int64) for _ in range(dim)]

def sample_challenge(seed_bytes):
    # C = { c in R : l_inf=1, l1 = kappa }
    rng = np.random.default_rng(int.from_bytes(hashlib.sha256(seed_bytes).digest()[:8], "little"))
    c = np.zeros(N, dtype=np.int64)
    positions = rng.choice(N, size=KAPPA, replace=False)
    signs = rng.integers(0, 2, size=KAPPA) * 2 - 1
    c[positions] = signs
    return c

# ----------------------------------------------------------------------------
# 雜湊
# ----------------------------------------------------------------------------
def _digest(*parts):
    # H : {0,1}* -> S_beta^k；H2 : {0,1}* -> C
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
    raw = _digest(b"H", *parts).digest(K_DIM * N)
    arr = np.frombuffer(raw, dtype=np.uint8).astype(np.int64)
    arr = (arr % 3) - 1  # {0,1,2} -> {-1,0,1}
    return [arr[i * N:(i + 1) * N].copy() for i in range(K_DIM)]

def H2_challenge(*parts):
    seed = _digest(b"H2", *parts).digest(32)
    return sample_challenge(seed)

def tag_challenge(t1, t2, c1, c2, m, L):
    return H2_challenge(b"TAG", _vecbytes(t1), _vecbytes(t2),
                        _vecbytes(c1, c2), m, _vecbytes(*L))

def _vecbytes(*vecs):
    out = bytearray()
    for v in vecs:
        for p in v:
            out += center(np.asarray(p)).tobytes()
    return bytes(out)

# ----------------------------------------------------------------------------
# 演算法
# ----------------------------------------------------------------------------
def setup(rng=None):
    rng = rng or _rng
    A  = sample_uniform_mat(rng, H_DIM, L_DIM) # h x l
    B1 = [] # B1 = [ I_v | B1' ] (v x k)
    for i in range(V_DIM):
        row = []
        for j in range(K_DIM):
            if j < V_DIM:
                p = np.zeros(N, dtype=np.int64); p[0] = 1 if j == i else 0
                row.append(p)
            else:
                row.append(sample_uniform_poly(rng))
        B1.append(row)

    B2 = [] # B2 = [ 0^{l x v} | I_l | B2' ] (l x k)
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
    sk = sample_ternary_vec(rng, L_DIM)
    pk = matvec(pp["A"], sk)
    return pk, sk, None  # 狀態 s = None

def commit(pp, x_vec, r_vec):
    c1 = matvec(pp["B1"], r_vec)
    c2 = vec_add(matvec(pp["B2"], r_vec), x_vec)
    return c1, c2

def _rej_accept(z_polys, v_polys, sigma, M):
    # 拒絕採樣
    z = np.concatenate([np.asarray(p, dtype=np.float64) for p in z_polys])
    vv = np.concatenate([np.asarray(p, dtype=np.float64) for p in v_polys])
    inner = float(np.dot(z, vv))
    nv2 = float(np.dot(vv, vv))
    val = np.exp((-2.0 * inner + nv2) / (2.0 * sigma * sigma)) / M
    return _rng.random() < min(1.0, val)

def sign(pp, m, L, sk, state, signer_index, rng=None, _max_retry=2000):
    rng = rng or _rng
    n = len(L)
    j = signer_index

    # 建構連結標記
    if state is None:
        r1 = H_ternary(_vecbytes(sk), m, _vecbytes(*L))
        r2 = r1
        new_state = (m, L)
    else:
        m1, L1 = state
        r1 = H_ternary(_vecbytes(sk), m1, _vecbytes(*L1))
        r2 = H_ternary(_vecbytes(sk), m, _vecbytes(*L))
        new_state = state
    c1, c2 = commit(pp, sk, r2)
    r_diff = vec_sub(r1, r2)

    # 連結標記中的 z 需要進行拒絕採樣
    for _ in range(_max_retry):
        y = sample_gaussian_vec(rng, K_DIM)
        B1y = matvec(pp["B1"], y)
        B2y = matvec(pp["B2"], y)
        d_tag = tag_challenge(B1y, B2y, c1, c2, m, L)
        z_tag = vec_add(y, scalar_vec(d_tag, r_diff))
        v_tag = scalar_vec(d_tag, r_diff)
        if _rej_accept(z_tag, v_tag, SIGMA, MZ):
            break
    else:
        raise RuntimeError("連結標記生成超過重試上限")
    I = {"z": z_tag, "d": d_tag, "c1": c1, "c2": c2}

    # 計算環簽章
    for _ in range(_max_retry):
        u   = sample_gaussian_vec(rng, L_DIM)
        u_c = sample_gaussian_vec(rng, K_DIM)
        d = [None] * n
        z   = [None] * n
        z_c = [None] * n
        a_j = matvec(pp["A"],  u)
        b_j = matvec(pp["B1"], u_c)
        g_j = vec_add(matvec(pp["B2"], u_c), u)
        d[(j + 1) % n] = H2_challenge(_vecbytes(*L), _tagbytes(I), m, _vecbytes(a_j), _vecbytes(b_j), _vecbytes(g_j))
        i = (j + 1) % n
        while i != j:
            z[i]   = sample_gaussian_vec(rng, L_DIM)
            z_c[i] = sample_gaussian_vec(rng, K_DIM)
            alpha = vec_sub(matvec(pp["A"], z[i]),  scalar_vec(d[i], L[i]))
            beta  = vec_sub(matvec(pp["B1"], z_c[i]), scalar_vec(d[i], c1))
            gamma = vec_sub(vec_add(matvec(pp["B2"], z_c[i]), z[i]), scalar_vec(d[i], c2))
            d[(i + 1) % n] = H2_challenge(_vecbytes(*L), _tagbytes(I), m, _vecbytes(alpha), _vecbytes(beta), _vecbytes(gamma))
            i = (i + 1) % n

        z[j]   = vec_add(u,   scalar_vec(d[j], sk))
        z_c[j] = vec_add(u_c, scalar_vec(d[j], r2))

        # 環簽章的拒絕採樣
        v1 = scalar_vec(d[j], sk)
        v2 = scalar_vec(d[j], r2)
        if not _rej_accept(z[j] + z_c[j], v1 + v2, SIGMA, M):
            continue

        sig = {"d1": d[0], "z": z, "z_c": z_c, "I": I}
        return sig, new_state
    raise RuntimeError("環簽章超過重試上限")

def _tagbytes(I):
    return _vecbytes(I["z"]) + _vecbytes([I["d"]]) + _vecbytes(I["c1"], I["c2"])

def _norm2(polys):
    z = np.concatenate([np.asarray(p, dtype=np.float64) for p in polys])
    return float(np.sqrt(np.dot(z, z)))

def verify(pp, m, L, sig):
    n = len(L)
    I = sig["I"]
    # 連結標記 z 的回應向量合法範圍
    bound_tag = 2 * SIGMA * np.sqrt(N)
    for zi in I["z"]:
        if _norm2([zi]) > bound_tag: return 0
    # 環簽章的回應向量合法範圍
    bound_z   = 2 * SIGMA * np.sqrt(L_DIM * N)
    bound_zc  = 2 * SIGMA * np.sqrt(K_DIM * N)
    for i in range(n):
        if _norm2(sig["z"][i]) > bound_z:   return 0
        if _norm2(sig["z_c"][i]) > bound_zc: return 0

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
    c1, c2 = carrier["c1"], carrier["c2"]
    co1, co2 = other["c1"], other["c2"]
    z, d = carrier["z"], carrier["d"]
    if any(_norm2([zi]) > bound for zi in z):
        return False

    # delta c
    d1 = vec_sub(co1, c1)
    d2 = vec_sub(co2, c2)

    t1 = vec_sub(matvec(pp["B1"], z), scalar_vec(d, d1))
    t2 = vec_sub(matvec(pp["B2"], z), scalar_vec(d, d2))
    chk = tag_challenge(t1, t2, c1, c2, m_carrier, L_carrier)
    return np.array_equal(chk, d)

def link(pp, m, mp, L, Lp, sig, sigp):
    bound = 2 * SIGMA * np.sqrt(N)
    I, Ip = sig["I"], sigp["I"]
    if _link_branch(pp, Ip, I, mp, Lp, bound):
        return 1
    if _link_branch(pp, I, Ip, m, L, bound):
        return 1
    return 0

def sizes_bits(n):
    logq = int(np.ceil(np.log2(Q))) # 40
    log4sigma = int(np.ceil(np.log2(4 * SIGMA)))
    pk = H_DIM * N * logq
    sk = 2 * L_DIM * N # 三個係數，用 2 bits
    sig = (n * (K_DIM + L_DIM) + K_DIM) * N * log4sigma + (V_DIM + L_DIM) * N * logq
    return pk, sk, sig
