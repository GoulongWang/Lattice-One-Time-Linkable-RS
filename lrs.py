# Copyright (C) 2026 Guolong Wang
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Post-Quantum Linkable Ring Signatures Based on Lattice 論文 PoC 實作
Author: Guolong Wang
"""

import numpy as np
import hashlib
from dataclasses import dataclass

# 參數集詳見論文
ALPHA = 11.0 # alpha = sigma / (kappa * sqrt(l*N))  => M = 5.67, M_z = 14.83
Q_DEFAULT = 1099511627581 # q = 2^40 - 195

@dataclass(frozen=True)
class Params:
    name: str
    N: int
    Q: int
    H_DIM: int
    L_DIM: int
    V_DIM: int
    K_DIM: int
    KAPPA: int
    BETA: int
    SIGMA: float

    def __post_init__(self):
        assert self.Q % 8 == 5, "q == 5 (mod 8) for Lemma 1"
        if 2.0 * (self.Q / 2.0) * self.SIGMA * np.sqrt(self.N) >= 2.0 ** 62:
            print("卷積溢位警告")

    @property
    def QH(self): return self.Q // 2

    # kappa * sqrt(k * N)：環簽章回應 z_c 中 d*r2 的上界
    @property
    def T2(self): return self.KAPPA * np.sqrt(self.K_DIM * self.N)

    # 環簽章的拒絕採樣常數 M
    @property
    def M(self):
        ac = self.SIGMA / (self.KAPPA * np.sqrt((self.L_DIM + self.K_DIM) * self.N))
        return np.exp(12.0 / ac + 1.0 / (2 * ac * ac))

    # 連結標記的拒絕採樣常數
    @property
    def MZ(self):
        az = self.SIGMA / (2.0 * self.T2)
        return np.exp(12.0 / az + 1.0 / (2 * az * az))

def make_params(name, N, l = 4, k = 6, h = 1, v = 1, kappa = 45, beta = 1, q = Q_DEFAULT, alpha = ALPHA):
    sigma = round(alpha * kappa * np.sqrt(l * N))
    return Params(name, N = N, Q = q, H_DIM = h, L_DIM = l, V_DIM = v, K_DIM = k, KAPPA = kappa, BETA = beta, SIGMA = float(sigma))

PARAM_SETS = {name: make_params(name, N) for name, N in (("lrs-1024", 1024), ("lrs-2048", 2048))}

def _new_rng(rng):
    return np.random.default_rng() if rng is None else rng

# ----------------------------------------------------------------------------
# R_q = Z_q[X]/(X^N + 1) 環多項式運算
# ----------------------------------------------------------------------------
def center(P, a):
    # (-q/2, q/2]
    a = a % P.Q
    a = np.where(a > P.QH, a - P.Q, a)
    return a.astype(np.int64)

def poly_mul(P, a, b):
    N = P.N
    conv = np.convolve(a.astype(np.int64), b.astype(np.int64))
    res = np.zeros(N, dtype=np.int64)
    res[:N] = conv[:N]
    # X^N = -1
    res[:N - 1] -= conv[N:2 * N - 1]
    return center(P, res)

def poly_add(P, a, b):
    return center(P, a + b)

def poly_sub(P, a, b):
    return center(P, a - b)

def matvec(P, mat, vec):
    out = []
    for row in mat:
        acc = np.zeros(P.N, dtype=np.int64)
        for aij, vj in zip(row, vec):
            acc = acc + poly_mul(P, aij, vj)
        out.append(center(P, acc))
    return out

def vec_add(P, u, w):
    return [poly_add(P, a, b) for a, b in zip(u, w)]

def vec_sub(P, u, w):
    return [poly_sub(P, a, b) for a, b in zip(u, w)]

def scalar_vec(P, c, vec):
    return [poly_mul(P, c, v) for v in vec]

# ----------------------------------------------------------------------------
# 取樣
# ----------------------------------------------------------------------------
def sample_uniform_poly(P, rng):
    return center(P, rng.integers(0, P.Q, size=P.N, dtype=np.int64))

def sample_uniform_vec(P, rng, dim):
    return [sample_uniform_poly(P, rng) for _ in range(dim)]

def sample_uniform_mat(P, rng, rows, cols):
    return [[sample_uniform_poly(P, rng) for _ in range(cols)] for _ in range(rows)]

def sample_ternary_vec(P, rng, dim):
    # 係數 {-1,0,1}
    return [rng.integers(-P.BETA, P.BETA + 1, size=P.N, dtype=np.int64) for _ in range(dim)]

def sample_gaussian_vec(P, rng, dim):
    return [np.rint(rng.normal(0.0, P.SIGMA, size=P.N)).astype(np.int64) for _ in range(dim)]

def sample_challenge(P, seed_bytes):
    # C = { c in R : l_inf=1, l1 = kappa }
    rng = np.random.default_rng(int.from_bytes(hashlib.sha256(seed_bytes).digest()[:8], "little"))
    c = np.zeros(P.N, dtype=np.int64)
    positions = rng.choice(P.N, size=P.KAPPA, replace=False)
    signs = rng.integers(0, 2, size=P.KAPPA) * 2 - 1
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

def H_ternary(P, *parts):
    N = P.N
    raw = _digest(b"H", *parts).digest(P.K_DIM * N)
    arr = np.frombuffer(raw, dtype=np.uint8).astype(np.int64)
    arr = (arr % 3) - 1  # {0,1,2} -> {-1,0,1}
    return [arr[i * N:(i + 1) * N].copy() for i in range(P.K_DIM)]

def H2_challenge(P, *parts):
    seed = _digest(b"H2", *parts).digest(32)
    return sample_challenge(P, seed)

def tag_challenge(P, t1, t2, c1, c2, m, L):
    return H2_challenge(P, b"TAG", _vecbytes(P, t1), _vecbytes(P, t2),
                        _vecbytes(P, c1, c2), m, _vecbytes(P, *L))

def _vecbytes(P, *vecs):
    out = bytearray()
    for v in vecs:
        for p in v:
            out += center(P, np.asarray(p)).tobytes()
    return bytes(out)

# ----------------------------------------------------------------------------
# 演算法
# ----------------------------------------------------------------------------
def setup(P, rng=None):
    rng = _new_rng(rng)
    N, V_DIM, L_DIM, K_DIM = P.N, P.V_DIM, P.L_DIM, P.K_DIM
    A  = sample_uniform_mat(P, rng, P.H_DIM, L_DIM) # h x l
    B1 = [] # B1 = [ I_v | B1' ] (v x k)
    for i in range(V_DIM):
        row = []
        for j in range(K_DIM):
            if j < V_DIM:
                p = np.zeros(N, dtype=np.int64); p[0] = 1 if j == i else 0
                row.append(p)
            else:
                row.append(sample_uniform_poly(P, rng))
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
                row.append(sample_uniform_poly(P, rng))
        B2.append(row)
    return {"params": P, "A": A, "B1": B1, "B2": B2}

def keygen(pp, rng=None):
    P, rng = pp["params"], _new_rng(rng)
    sk = sample_ternary_vec(P, rng, P.L_DIM)
    pk = matvec(P, pp["A"], sk)
    return pk, sk, None  # 狀態 s = None

def commit(pp, x_vec, r_vec):
    P = pp["params"]
    c1 = matvec(P, pp["B1"], r_vec)
    c2 = vec_add(P, matvec(P, pp["B2"], r_vec), x_vec)
    return c1, c2

def _rej_accept(rng, z_polys, v_polys, sigma, M):
    # 拒絕採樣
    z = np.concatenate([np.asarray(p, dtype=np.float64) for p in z_polys])
    vv = np.concatenate([np.asarray(p, dtype=np.float64) for p in v_polys])
    inner = float(np.dot(z, vv))
    nv2 = float(np.dot(vv, vv))
    val = np.exp((-2.0 * inner + nv2) / (2.0 * sigma * sigma)) / M
    return rng.random() < min(1.0, val)

def _ring_hash(pp, L, I, m, a, b, g):
    # H2 的輸入順序：sign 與 verify 都經過這裡
    P = pp["params"]
    return H2_challenge(P, _vecbytes(P, *L), _tagbytes(P, I), m, _vecbytes(P, a), _vecbytes(P, b), _vecbytes(P, g))

def _ring_next(pp, L, I, m, pk_i, z_i, zc_i, d_i):
    # 由第 i 位成員的 (z_i, z_c_i, d_i) 算出 d_{i+1}
    P = pp["params"]
    alpha = vec_sub(P, matvec(P, pp["A"], z_i),  scalar_vec(P, d_i, pk_i))
    beta  = vec_sub(P, matvec(P, pp["B1"], zc_i), scalar_vec(P, d_i, I["c1"]))
    gamma = vec_sub(P, vec_add(P, matvec(P, pp["B2"], zc_i), z_i), scalar_vec(P, d_i, I["c2"]))
    return _ring_hash(pp, L, I, m, alpha, beta, gamma)

def sign(pp, m, L, sk, state, signer_index, rng=None, _max_retry=2000):
    P, rng = pp["params"], _new_rng(rng)
    n = len(L)
    j = signer_index

    # 建構連結標記
    if state is None:
        r1 = H_ternary(P, _vecbytes(P, sk), m, _vecbytes(P, *L))
        r2 = r1
        new_state = (m, L)
    else:
        m1, L1 = state
        r1 = H_ternary(P, _vecbytes(P, sk), m1, _vecbytes(P, *L1))
        r2 = H_ternary(P, _vecbytes(P, sk), m, _vecbytes(P, *L))
        new_state = state
    c1, c2 = commit(pp, sk, r2)
    r_diff = vec_sub(P, r1, r2)

    # 連結標記中的 z 需要進行拒絕採樣
    for _ in range(_max_retry):
        y = sample_gaussian_vec(P, rng, P.K_DIM)
        B1y = matvec(P, pp["B1"], y)
        B2y = matvec(P, pp["B2"], y)
        d_tag = tag_challenge(P, B1y, B2y, c1, c2, m, L)
        z_tag = vec_add(P, y, scalar_vec(P, d_tag, r_diff))
        v_tag = scalar_vec(P, d_tag, r_diff)
        if _rej_accept(rng, z_tag, v_tag, P.SIGMA, P.MZ):
            break
    else:
        raise RuntimeError("連結標記生成超過重試上限")
    I = {"z": z_tag, "d": d_tag, "c1": c1, "c2": c2}

    # 計算環簽章
    for _ in range(_max_retry):
        u   = sample_gaussian_vec(P, rng, P.L_DIM)
        u_c = sample_gaussian_vec(P, rng, P.K_DIM)
        d = [None] * n
        z   = [None] * n
        z_c = [None] * n
        a_j = matvec(P, pp["A"],  u)
        b_j = matvec(P, pp["B1"], u_c)
        g_j = vec_add(P, matvec(P, pp["B2"], u_c), u)
        d[(j + 1) % n] = _ring_hash(pp, L, I, m, a_j, b_j, g_j)
        i = (j + 1) % n
        while i != j:
            z[i]   = sample_gaussian_vec(P, rng, P.L_DIM)
            z_c[i] = sample_gaussian_vec(P, rng, P.K_DIM)
            d[(i + 1) % n] = _ring_next(pp, L, I, m, L[i], z[i], z_c[i], d[i])
            i = (i + 1) % n

        z[j]   = vec_add(P, u,   scalar_vec(P, d[j], sk))
        z_c[j] = vec_add(P, u_c, scalar_vec(P, d[j], r2))

        # 環簽章的拒絕採樣
        v1 = scalar_vec(P, d[j], sk)
        v2 = scalar_vec(P, d[j], r2)
        if not _rej_accept(rng, z[j] + z_c[j], v1 + v2, P.SIGMA, P.M):
            continue

        sig = {"d1": d[0], "z": z, "z_c": z_c, "I": I}
        return sig, new_state
    raise RuntimeError("環簽章超過重試上限")

def _tagbytes(P, I):
    return _vecbytes(P, I["z"]) + _vecbytes(P, [I["d"]]) + _vecbytes(P, I["c1"], I["c2"])

def _norm2(polys):
    z = np.concatenate([np.asarray(p, dtype=np.float64) for p in polys])
    return float(np.sqrt(np.dot(z, z)))

def verify(pp, m, L, sig):
    P = pp["params"]
    n = len(L)
    I = sig["I"]
    # 連結標記 z 的回應向量合法範圍
    bound_tag = 2 * P.SIGMA * np.sqrt(P.N)
    for zi in I["z"]:
        if _norm2([zi]) > bound_tag: return 0
    # 環簽章的回應向量合法範圍
    bound_z   = 2 * P.SIGMA * np.sqrt(P.L_DIM * P.N)
    bound_zc  = 2 * P.SIGMA * np.sqrt(P.K_DIM * P.N)
    for i in range(n):
        if _norm2(sig["z"][i]) > bound_z:   return 0
        if _norm2(sig["z_c"][i]) > bound_zc: return 0

    e = sig["d1"]
    for i in range(n):
        e = _ring_next(pp, L, I, m, L[i], sig["z"][i], sig["z_c"][i], e)
    return 1 if all(np.array_equal(a, b) for a, b in zip(e, sig["d1"])) else 0

def _link_branch(pp, carrier, other, m_carrier, L_carrier, bound):
    P = pp["params"]
    c1, c2 = carrier["c1"], carrier["c2"]
    co1, co2 = other["c1"], other["c2"]
    z, d = carrier["z"], carrier["d"]
    if any(_norm2([zi]) > bound for zi in z):
        return False

    # delta c
    d1 = vec_sub(P, co1, c1)
    d2 = vec_sub(P, co2, c2)

    t1 = vec_sub(P, matvec(P, pp["B1"], z), scalar_vec(P, d, d1))
    t2 = vec_sub(P, matvec(P, pp["B2"], z), scalar_vec(P, d, d2))
    chk = tag_challenge(P, t1, t2, c1, c2, m_carrier, L_carrier)
    return np.array_equal(chk, d)

def link(pp, m, mp, L, Lp, sig, sigp):
    P = pp["params"]
    bound = 2 * P.SIGMA * np.sqrt(P.N)
    I, Ip = sig["I"], sigp["I"]
    if _link_branch(pp, Ip, I, mp, Lp, bound):
        return 1
    if _link_branch(pp, I, Ip, m, L, bound):
        return 1
    return 0

def sizes_bits(P, n):
    logq = int(np.ceil(np.log2(P.Q))) # 40
    log4sigma = int(np.ceil(np.log2(4 * P.SIGMA)))
    pk = P.H_DIM * P.N * logq
    sk = 2 * P.L_DIM * P.N # 三個係數，用 2 bits
    sig = (n * (P.K_DIM + P.L_DIM) + P.K_DIM) * P.N * log4sigma + (P.V_DIM + P.L_DIM) * P.N * logq
    return pk, sk, sig
