# Copyright (C) 2026 Guolong Wang
# SPDX-License-Identifier: GPL-3.0-or-later
import numpy as np
import lrs

n = 5                                # 環大小（測試用的人數，與參數集無關）
PARAMS = ["lrs-1024", "lrs-2048"]    # 兩組參數集都要驗；lrs-2048 離 int64 上限最近

def build(param):
    lrs.set_params(param)
    rng = np.random.default_rng(12345)
    lrs._rng = np.random.default_rng(999)
    pp = lrs.setup(rng)
    keys = [lrs.keygen(pp, rng) for _ in range(n)]
    L = [pk for (pk, sk, s) in keys] # Ring L
    signer = int(rng.integers(n))    # 全程使用的簽章者
    return pp, keys, L, signer, rng

# 1. 簽章正確性檢查
def unit_test_sign_verify(ctx):
    pp, keys, L, signer, rng = ctx
    all_ok = True
    for i in range(n):
        pk_i, sk_i, st_i = keys[i]
        sig_i, _ = lrs.sign(pp, b"msg", L, sk_i, st_i, i)
        v_i = lrs.verify(pp, b"msg", L, sig_i)
        all_ok &= (v_i == 1)
    ret = True if all_ok else False
    print(f"[1] 驗證簽章正確性 ({n} 人): {'PASS' if ret else 'FAIL'}")
    return ret

# 2. 錯誤訊息驗證不會通過
def unit_test_wrong_message(ctx):
    pp, keys, L, signer, rng = ctx
    pk, sk, st = keys[signer]
    sig, _ = lrs.sign(pp, b"msg", L, sk, st, signer)
    v_bad = lrs.verify(pp, b"wrong_msg", L, sig)
    ret = True if v_bad == 0 else False
    print(f"[2] 篡改訊息驗證失敗: {'PASS' if ret else 'FAIL'}")
    return ret

# 3. Link 正確性
def unit_test_link(ctx):
    pp, keys, L, signer, rng = ctx
    pk, sk, st = keys[signer]
    sig1, state = lrs.sign(pp, b"m1", L, sk, None, signer)   # 第一次簽章
    sig2, state = lrs.sign(pp, b"m2", L, sk, state, signer)
    sig3, _ = lrs.sign(pp, b"m3", L, sk, state, signer)
    ok = lrs.verify(pp, b"m3", L, sig3) == 1
    ok &= lrs.link(pp, b"m1", b"m2", L, L, sig1, sig2) == 1
    ok &= lrs.link(pp, b"m1", b"m3", L, L, sig1, sig3) == 1
    ok &= lrs.link(pp, b"m2", b"m3", L, L, sig2, sig3) == 0
    ret = bool(ok)
    print(f"[3] Link 正確性: {'PASS' if ret else 'FAIL'}")
    return ret

# 4. 不同簽章者不可連結
def unit_test_link_different_signers(ctx):
    pp, keys, L, signer, rng = ctx
    pk, sk, st = keys[signer]
    other = int(rng.choice([i for i in range(n) if i != signer]))
    pkB, skB, stB = keys[other]
    _, stA = lrs.sign(pp, b"vote-first", L, sk, None, signer)
    sigA, _ = lrs.sign(pp, b"vote-A", L, sk, stA, signer)
    sigB, _ = lrs.sign(pp, b"vote-A", L, skB, stB, other)
    lk = lrs.link(pp, b"vote-A", b"vote-A", L, L, sigA, sigB)
    ret = True if lk == 0 else False
    print(f"[4] 不同簽章者不可連結: {'PASS' if ret else 'FAIL'}")
    return ret

def print_sizes(param):
    print(f"\n公私鑰及簽章大小（{param}）:")
    for ring_n in [1, 8, 32]:
        pkb, skb, sgb = lrs.sizes_bits(ring_n)
        print(f"n = {ring_n:<3} PK = {pkb / 8 / 1024:.2f} KB  SK = {skb / 8 / 1024:.2f} KB  "
              f"Sig = {sgb / 8 / 1024:.2f} KB")

def run(param):
    print(f"\n=== {param} ===")
    ctx = build(param)
    ok = unit_test_sign_verify(ctx)
    ok &= unit_test_wrong_message(ctx)
    ok &= unit_test_link(ctx)
    ok &= unit_test_link_different_signers(ctx)
    print_sizes(param)
    return bool(ok)

allGood = 1
for param in PARAMS:
    allGood &= run(param)

if allGood == 1:
    print("\nALL GOOD!")
else:
    print("\nTESTS FAIL!")
