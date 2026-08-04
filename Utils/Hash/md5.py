import hashlib


def md5_hash(s):
    return hashlib.md5(s.encode()).hexdigest()

p  = "common_sken_res/xiandaosqnv.png"
at = "common_sken_res/xiandaosqnv.atlas"
sk = "common_sken_res/xiandaosqnv.json"
# e7385d0fc6fca0d1f114729279443cba -> longnv.png
# 9f72b1d466345467350efa24ebd42894 -> longnv.atlas
# 90b1d5342140360813d3024c9520f1bf -> longnv.skel
print(md5_hash(p))
print(md5_hash(at))
print(md5_hash(sk))