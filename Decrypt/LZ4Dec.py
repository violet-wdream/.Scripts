import sys
import os
import lz4.frame

if len(sys.argv) < 2:
    print("用法: python lz4dec.py 输入文件")
    sys.exit(1)

inp = sys.argv[1]
name = os.path.basename(inp)
outp = name + ".txt"

with open(inp, "rb") as f:
    data = f.read()

dec = lz4.frame.decompress(data)

with open(outp, "wb") as f:
    f.write(dec)

print("输出:", outp)
