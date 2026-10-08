"""
論文方案的參考實作（概念驗證）：基於晶格、以承諾當標籤的可連結環簽章
    "Post-Quantum Linkable Ring Signatures Based on Lattice"（Guolong Wang，政大）

在 R_q = Z_q[X]/(X^N + 1) 上實作 Setup / KeyGen / Sign / Verify / Link（演算法 1-5），
參數集照論文參數表：

    q = 2^40 - 195（質數，q = 5 mod 8，引理 1 在 d=2 時成立）
    N = 1024,  h = 1,  l = 4,  v = 1,  k = 6
    kappa = 45（挑戰值的 l1 權重）,  beta = 1（sk、r 為三元）,  sigma = 31680

只用來驗正確性和測效能，不是常數時間、也沒做最佳化。
多項式乘法用 NumPy int64 負循環卷積；矩陣元素約 2^39 乘上短的高斯／三元向量，
部分和都小於 2^63，所以 int64 算出來是精確的。
"""

import numpy as np
import hashlib
import time

# ----------------------------------------------------------------------------
# 參數集
# ----------------------------------------------------------------------------
# 安全性主要看多項式次數 N（晶格維度 ~ N * 模組秩）和模組秩 (l, k)，所以這裡用不同 N
# 開了幾組參數集。sigma = alpha * kappa * sqrt(l*N)，alpha 固定，這樣拒絕取樣常數
# M、M_z 在每組都一樣（重試次數不會亂跳）。alpha = 11 在 N = 1024 剛好得到論文的
# sigma = 31680。
#
# q = 2^40 - 195 是質數且 == 5 (mod 8)；這裡的 N 都是 2 的冪次，所以引理 1
# （X^N+1 部分分裂，d=2）每組都成立，大家共用同一個 q。
# 具體安全性估計（lattice-estimator / Core-SVP）留到未來工作，所以參數集不標安全位元數。
ALPHA = 11.0                 # sigma / (kappa * sqrt(l*N))；alpha=11 -> M~5.67, M_z~14.83
Q_DEFAULT = 1099511627581    # = 2^40 - 195，質數，== 5 (mod 8)

def _make_set(N, l=4, k=6, h=1, v=1, kappa=45, beta=1, q=Q_DEFAULT, alpha=ALPHA):
    sigma = round(alpha * kappa * np.sqrt(l * N))
    return {"N": N, "Q": q, "H_DIM": h, "L_DIM": l, "V_DIM": v, "K_DIM": k,
            "KAPPA": kappa, "BETA": beta, "SIGMA": float(sigma)}

PARAM_SETS = {
    # 論文參數表的基準組（sigma 四捨五入就是 31680）
    "lrs-1024":   _make_set(N=1024),
    # 安全性較高的一組
    "lrs-2048":   _make_set(N=2048),
}

# 這些全域變數由 set_params() 設定；import 時下面會先設好預設值，
# 舊腳本直接 `import lrs` 不用改。
N = Q = QH = H_DIM = L_DIM = V_DIM = K_DIM = KAPPA = BETA = SIGMA = None
T2 = None             # kappa*sqrt(k*N)：z_c 中心 d*r2 的最壞上界
TC = AC = M = None    # 環回應的拒絕常數 M（論文參數表的 M）和它的兩個中間值。
                      # C 是「合併」的意思：TC/AC 算的是疊起來的 (l+k) 維回應
                      # (z_j || z_c,j)，不是只有 z_j。
TZ = AZ = MZ = None   # 標籤回應的拒絕常數（演算法 3 第 13 行）：中心 v = d*(r1-r2)
PARAM_NAME = None

def set_params(name):
    """切換到 PARAM_SETS 裡指定的參數集，重設上面的全域變數。"""
    global N, Q, QH, H_DIM, L_DIM, V_DIM, K_DIM, KAPPA, BETA, SIGMA
    global T2, TC, AC, M, TZ, AZ, MZ, PARAM_NAME
    ps = PARAM_SETS[name] if isinstance(name, str) else name
    PARAM_NAME = name if isinstance(name, str) else "custom"
    N = ps["N"]; Q = ps["Q"]
    H_DIM = ps["H_DIM"]; L_DIM = ps["L_DIM"]; V_DIM = ps["V_DIM"]; K_DIM = ps["K_DIM"]
    KAPPA = ps["KAPPA"]; BETA = ps["BETA"]; SIGMA = ps["SIGMA"]
    assert Q % 8 == 5, "q must be == 5 (mod 8) for Lemma 1 (partial splitting, d=2)"
    QH = Q // 2  # 置中化約用
    # 拒絕取樣的重複常數（定理 1），由 sigma = alpha*T 算出
    T2 = KAPPA * np.sqrt(K_DIM * N)     # z_c 中心 d*r2 的最壞上界
    # 對疊起來的回應 (z_j || z_c,j) 只做「一次」合併拒絕，中心 v = (d*sk || d*r2)，
    # T = kappa*sqrt((l+k)*N)。z_j、z_c,j 分開檢查的話期望要 2.99 * 3.83 = 11.44 次；
    # 因為 sqrt(l+k) < sqrt(l)+sqrt(k)，合併檢查只要 M = 5.67 次，少一半。
    TC = KAPPA * np.sqrt((L_DIM + K_DIM) * N)
    AC = SIGMA / TC
    M = np.exp(12.0 / AC + 1.0 / (2 * AC * AC))
    # 標籤回應的拒絕常數 M_z（論文演算法 3 第 13 行）：標籤回應 z = y + d*(r1 - r2)
    # 要做「自己的」Lyubashevsky 拒絕檢查，跟上面環的 M 是分開的。
    # 中心 v = d*(r1 - r2)，r1、r2 都在 S_beta^k（三元）；沿用 T2 的最壞上界
    # （中心 d*r，單一 r 在 S_beta^k）加三角不等式，
    # ||d*(r1-r2)|| <= ||d*r1|| + ||d*r2|| <= 2*T2。
    TZ = 2.0 * T2
    AZ = SIGMA / TZ
    MZ = np.exp(12.0 / AZ + 1.0 / (2 * AZ * AZ))
    _check_int64_headroom()

def _check_int64_headroom():
    """poly_mul 的 int64 卷積快要溢位時印警告。

    poly_mul 是一個 mod q 均勻的運算元（|coeff| <= q/2）跟一個短向量（高斯寬度 sigma）
    做卷積。N 個正負號隨機的乘積加起來，大小約 2 * (q/2) * sigma * sqrt(N)；
    前面的 2 是用 object dtype 實測校正的（lrs-2048、q = 2^40 - 195 實測峰值 2^60.8，
    這個估計給 2^61.0）。int64 上限 2^63，目前的參數集大約用掉四分之一 —— 還是精確的，
    但餘裕不多，q 或 N 再加大就要換更寬的累加器。
    """
    est = 2.0 * (Q / 2.0) * SIGMA * np.sqrt(N)
    if est >= 2.0 ** 62:
        print("WARNING: poly_mul int64 headroom is thin for %s: estimated peak "
              "convolution magnitude 2^%.1f against the int64 ceiling 2^63. "
              "Exact integer arithmetic may silently overflow -- widen the "
              "accumulator or lower q/N." % (PARAM_NAME, np.log2(est)))

set_params("lrs-1024")  # 預設：論文參數表的基準組（向下相容）

# ----------------------------------------------------------------------------
# R_q = Z_q[X]/(X^N + 1) 上的運算。多項式用 int64[N] 表示
# ----------------------------------------------------------------------------
def center(a):
    """取置中代表元，範圍 (-q/2, q/2]。"""
    a = a % Q
    a = np.where(a > QH, a - Q, a)
    return a.astype(np.int64)

def poly_mul(a, b):
    """負循環乘法 a*b mod (X^N+1) mod q，用 int64 精確計算。"""
    # 完整卷積，長度 2N-1
    conv = np.convolve(a.astype(np.int64), b.astype(np.int64))
    res = np.zeros(N, dtype=np.int64)
    res[:N] = conv[:N]
    # 折回來：X^N = -1
    res[:N - 1] -= conv[N:2 * N - 1]
    return center(res)

def poly_add(a, b):
    return center(a + b)

def poly_sub(a, b):
    return center(a - b)

# 向量 = 多項式的 list；矩陣 = 列的 list，每列是多項式的 list
def matvec(mat, vec):
    """R_q 上的 mat（rows x cols）乘 vec（cols），結果長度 rows。"""
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
    """多項式 c 乘上 vec 的每一項。"""
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
    """S_beta^dim，beta=1：係數從 {-1,0,1} 均勻取。"""
    return [rng.integers(-BETA, BETA + 1, size=N, dtype=np.int64) for _ in range(dim)]

def sample_gaussian_vec(rng, dim, sigma=SIGMA):
    """寬度 sigma 的離散高斯（連續高斯再取整），共 dim 個多項式。"""
    return [np.rint(rng.normal(0.0, sigma, size=N)).astype(np.int64) for _ in range(dim)]

def sample_challenge(seed_bytes):
    """C = { c in R : l_inf=1, l1 = kappa }，由 seed 決定。"""
    rng = np.random.default_rng(int.from_bytes(hashlib.sha256(seed_bytes).digest()[:8], "little"))
    c = np.zeros(N, dtype=np.int64)
    positions = rng.choice(N, size=KAPPA, replace=False)
    signs = rng.integers(0, 2, size=KAPPA) * 2 - 1
    c[positions] = signs
    return c

# ----------------------------------------------------------------------------
# 雜湊。H : {0,1}* -> S_beta^k（三元）；H2 : {0,1}* -> C（挑戰值）
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
    """雜湊到 S_beta^k：k 個三元多項式。"""
    raw = _digest(b"H", *parts).digest(K_DIM * N)
    arr = np.frombuffer(raw, dtype=np.uint8).astype(np.int64)
    arr = (arr % 3) - 1  # {0,1,2} -> {-1,0,1}
    return [arr[i * N:(i + 1) * N].copy() for i in range(K_DIM)]

def H2_challenge(*parts):
    seed = _digest(b"H2", *parts).digest(32)
    return sample_challenge(seed)

def tag_challenge(t1, t2, c1, c2, m, L):
    """標籤用的挑戰值 d（Sign 第 11 行和 Link 共用）。"""
    return H2_challenge(b"TAG", _vecbytes(t1), _vecbytes(t2),
                        _vecbytes(c1, c2), m, _vecbytes(*L))

def _vecbytes(*vecs):
    """把多項式向量固定編碼成 bytes，給雜湊用。"""
    out = bytearray()
    for v in vecs:
        for p in v:
            out += center(np.asarray(p)).tobytes()
    return bytes(out)

# ----------------------------------------------------------------------------
# 方案：演算法 1-5
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
    return pk, sk, None  # 狀態 s = None（bottom，還沒簽過）

def commit(pp, x_vec, r_vec):
    """Com(x; r)：c1 = B1 r（v 維），c2 = B2 r + x（l 維）。"""
    c1 = matvec(pp["B1"], r_vec)
    c2 = vec_add(matvec(pp["B2"], r_vec), x_vec)
    return c1, c2

def _rej_accept(z_polys, v_polys, sigma, M):
    """Lyubashevsky 拒絕取樣：回傳這次是否接受。"""
    z = np.concatenate([np.asarray(p, dtype=np.float64) for p in z_polys])
    vv = np.concatenate([np.asarray(p, dtype=np.float64) for p in v_polys])
    inner = float(np.dot(z, vv))
    nv2 = float(np.dot(vv, vv))
    val = np.exp((-2.0 * inner + nv2) / (2.0 * sigma * sigma)) / M
    return _rng.random() < min(1.0, val)

def sign(pp, m, L, sk, state, signer_index, rng=None, _max_retry=2000):
    """演算法 3。L 是公鑰的 list（每把公鑰是 h 個多項式的向量）。

    照論文虛擬碼，有兩個「獨立」的 Lyubashevsky 拒絕取樣迴圈：
      (1) 標籤迴圈（第 9-13 行）：重抽 y，直到標籤回應 z = y + d*(r1-r2) 被接受
          （用自己的常數 M_z，就是第 13 行的「以機率 ... 重新開始」）；
          標籤 I = (z, d, c) 在這裡一次定下來。
      (2) 環迴圈（第 15-21 行）：用已經定好的 I（I 會被雜湊進 AOS 鏈，所以建鏈前就要固定），
          重抽 (u, u_c) 重建環鏈，直到合併回應 (z_j || z_c,j) 被接受（常數 M）。
    (2) 失敗只重做環，不重做標籤 —— 標籤接受後就不用再動。
    期望總嘗試次數 E[Sign] = M_z + M。
    """
    rng = rng or _rng
    n = len(L)
    j = signer_index

    # ---- 標籤（第一次簽章：s = bottom）-------------------------------------
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
    r_diff = vec_sub(r1, r2)

    # ---- (1) 標籤拒絕取樣（演算法 3 第 9-13 行）-----------------------------
    for _ in range(_max_retry):
        y = sample_gaussian_vec(rng, K_DIM)
        B1y = matvec(pp["B1"], y)
        B2y = matvec(pp["B2"], y)
        d_tag = tag_challenge(B1y, B2y, c1, c2, m, L)
        z_tag = vec_add(y, scalar_vec(d_tag, r_diff))   # r1=r2 時就是 y
        v_tag = scalar_vec(d_tag, r_diff)
        if _rej_accept(z_tag, v_tag, SIGMA, MZ):
            break
    else:
        raise RuntimeError("tag signing exceeded retry budget")
    I = {"z": z_tag, "d": d_tag, "c1": c1, "c2": c2}

    # ---- (2) 環（AOS 鏈）拒絕取樣（第 15-21 行）-----------------------------
    for _ in range(_max_retry):
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

        # 簽章者的回應
        z[j]   = vec_add(u,   scalar_vec(d[j], sk))
        z_c[j] = vec_add(u_c, scalar_vec(d[j], r2))

        # 拒絕取樣（定理 1）：對疊起來的回應 (z_j || z_c,j) 做一次合併檢查，
        # 中心 v = (d*sk || d*r2)。等於對整個向量做一次 Lyubashevsky 拒絕，
        # 期望成本比分開檢查兩次低（5.67 vs 11.44）。
        v1 = scalar_vec(d[j], sk)
        v2 = scalar_vec(d[j], r2)
        if not _rej_accept(z[j] + z_c[j], v1 + v2, SIGMA, M):
            continue

        sig = {"d1": d[0], "z": z, "z_c": z_c, "I": I}
        return sig, new_state
    raise RuntimeError("signing exceeded retry budget")

def _tagbytes(I):
    return _vecbytes(I["z"]) + _vecbytes([I["d"]]) + _vecbytes(I["c1"], I["c2"])

def _norm2(polys):
    z = np.concatenate([np.asarray(p, dtype=np.float64) for p in polys])
    return float(np.sqrt(np.dot(z, z)))

def verify(pp, m, L, sig):
    """演算法 4（Verify）。"""
    n = len(L)
    I = sig["I"]
    # 第 2 行：標籤回應 z = (z^(1),...,z^(k))；每個 ||z^(i)||_2 <= 2*sigma*sqrt(N)
    bound_tag = 2 * SIGMA * np.sqrt(N)
    for zi in I["z"]:
        if _norm2([zi]) > bound_tag: return 0
    # 第 3 行：環回應
    bound_z   = 2 * SIGMA * np.sqrt(L_DIM * N)
    bound_zc  = 2 * SIGMA * np.sqrt(K_DIM * N)
    for i in range(n):
        if _norm2(sig["z"][i]) > bound_z:   return 0
        if _norm2(sig["z_c"][i]) > bound_zc: return 0
    # 第 4 行：重算環鏈
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
    """檢查 `carrier` 是不是帶著差值的那張（第二次簽章）。

    第二次簽章：z = y + d*(r1 - r2)，c = Com(sk; r2)，另一張的承諾是 Com(sk; r1)。
    所以 c_other - c_carrier = Com(0; r1 - r2)，
    B*z - d*(c_other - c_carrier) = B*y，且 tag_challenge(B*y,...) == d。
    """
    c1, c2 = carrier["c1"], carrier["c2"]
    co1, co2 = other["c1"], other["c2"]
    z, d = carrier["z"], carrier["d"]
    # 演算法 5 第 8/9 行：每個分量 ||z^(i)||_2 <= 2*sigma*sqrt(N)，i in [k]
    if any(_norm2([zi]) > bound for zi in z):
        return False
    d1 = vec_sub(co1, c1)          # delta = c_other - c_carrier
    d2 = vec_sub(co2, c2)
    t1 = vec_sub(matvec(pp["B1"], z), scalar_vec(d, d1))
    t2 = vec_sub(matvec(pp["B2"], z), scalar_vec(d, d2))
    chk = tag_challenge(t1, t2, c1, c2, m_carrier, L_carrier)
    return np.array_equal(chk, d)

def link(pp, m, mp, L, Lp, sig, sigp):
    """演算法 5。兩張簽章是同一個簽章者簽的就回傳 1。

    不知道哪張先簽，所以兩種順序都要試：看哪一張的標籤帶著差值（第二次簽章）。
    """
    bound = 2 * SIGMA * np.sqrt(N)          # 每個分量（演算法 5 第 8 行）
    I, Ip = sig["I"], sigp["I"]
    if _link_branch(pp, Ip, I, mp, Lp, bound):   # sigp 是第二次簽章
        return 1
    if _link_branch(pp, I, Ip, m, L, bound):     # sig 是第二次簽章
        return 1
    return 0

# ----------------------------------------------------------------------------
# 公私鑰及簽章大小（bits），跟論文的簽章大小公式一致
# ----------------------------------------------------------------------------
def sizes_bits(n):
    logq      = int(np.ceil(np.log2(Q)))           # 40
    log4sigma = int(np.ceil(np.log2(4 * SIGMA)))   # lrs-1024 是 17，lrs-2048 是 18
    pk = H_DIM * N * logq
    sk = 2 * L_DIM * N                              # 三元係數每個 2 bits
    sig = (n * (K_DIM + L_DIM) + K_DIM) * N * log4sigma + (V_DIM + L_DIM) * N * logq
    return pk, sk, sig
