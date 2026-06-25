import numpy as np
import lrs

rng = np.random.default_rng(12345)
lrs._rng = np.random.default_rng(999)

# print(f"q = {lrs.Q}  (q mod 8 = {lrs.Q % 8}),  N = {lrs.N}")
# print(f"M1 = {lrs.M1:.3f}  M2 = {lrs.M2:.3f}  (期望 Retry 次數約 M1 * M2 = {lrs.M1*lrs.M2:.1f})\n")

pp = lrs.setup(rng)
n = 5
keys = [lrs.keygen(pp, rng) for _ in range(n)]
L = [pk for (pk, sk, s) in keys] # Ring L: n 組公私鑰對
signer = int(rng.integers(n))  # 全程使用的簽章者
pk, sk, st = keys[signer]

# 1. 簽章正確性檢查
def unit_test_sign_verify():
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
def unit_test_wrong_message():
    sig, _ = lrs.sign(pp, b"msg", L, sk, st, signer)
    v_bad = lrs.verify(pp, b"wrong_msg", L, sig)
    ret = True if v_bad == 0 else False
    print(f"[2] 篡改訊息驗證失敗: {'PASS' if ret else 'FAIL'}")
    return ret

# 3. Link 正確性
def unit_test_link():
    sig1, state = lrs.sign(pp, b"m1", L, sk, None, signer)
    sig2, _ = lrs.sign(pp, b"m2", L, sk, state, signer)
    v = lrs.verify(pp, b"m2", L, sig2)
    lk = lrs.link(pp, b"m1", b"m2", L, L, sig1, sig2)
    ret = True if v == 1 and lk == 1 else False
    print(f"[3] Link 正確性: {'PASS' if ret else 'FAIL'}")
    return ret

# 4. 不同簽章者不可連結
def unit_test_link_different_signers():
    other = int(rng.choice([i for i in range(n) if i != signer]))
    pkB, skB, stB = keys[other]
    sigA, _ = lrs.sign(pp, b"vote-A", L, sk, st, signer)
    sigB, _ = lrs.sign(pp, b"vote-A", L, skB, stB, other)
    lk = lrs.link(pp, b"vote-A", b"vote-A", L, L, sigA, sigB)
    ret = True if lk == 0 else False
    print(f"[4] 不同簽章者不可連結: {'PASS' if ret else 'FAIL'}")
    return ret

allGood = 1
allGood &= unit_test_sign_verify()
allGood &= unit_test_wrong_message()
allGood &= unit_test_link()
allGood &= unit_test_link_different_signers()

if allGood == 1:
    print("ALL GOOD!")
else:
    print("TESTS FAIL!")

print("\n公私鑰及簽章大小:")
for n in [1, 8, 32]:
    pkb, skb, sgb = lrs.sizes_bits(n)
    print(f"n = {n:<3} PK = {pkb / 8 / 1024:.2f} KB  SK = {skb / 8 / 1024:.2f} KB  "
          f"Sig = {sgb / 8 / 1024:.2f} KB")
