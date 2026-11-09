# illusion connect re 文件解密
# 非lua部分参考 https://github.com/nobbyfix/IllusionConnectTools/blob/main/lib/xxtea/xxtea_decrypt.py
import os
import cxxtea
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from Utils.Png.Texture2Png import decode_pvr, decompress_ccz

# AppDelegate::applicationDidFinishLaunching
SIGN_LUA_CONF = b"@D#P$S%"
SIGN_OTHER = b"@S#T$O%"
PVR3_MAGIC = b"PVR\x03"
PVR2_MAGIC = b"4\x00\x00\x00"
# 输出已存在时跳过（断点续跑）；需要强制重刷置 True
FORCE = False
# 无签名的明文文件(.skel/.plist/.mclib/.json/.ccz/明文png等)原样拷贝到输出目录
COPY_PLAIN = True
# PNG 无损压缩等级：1-3 编码快(体积略大)，6 体积小但慢 ~10x；图集类建议 3
PNG_COMPRESS_LEVEL = 3

# ---------- Lookup Table ----------
v91_signed = [
    -10, -103, -23, -112, -30, -117, -20, -124, -16, -40, -101, -78, -98, -84, -100, -83,
    -102, -74, -14, 0x80, -31, -122, -23, -121, -41, -94, -52, -81, -57, -108, -32, -113,
    -3, -112, -80, -28, -127, -30, -118, -92, -25, -120, -90, -118, -58, -78, -42, -8, -8
]

xor_val = 0xB5
lookup_table = bytearray(49)
for i, b in enumerate(v91_signed):
    val = b & 0xFF
    lookup_table[i] = xor_val ^ val
    xor_val = val
lookup_table = bytes(lookup_table[:-1])  # 去掉末尾字节，保留实际使用的 48 字节

print(f"{lookup_table}") # Copyright(C),2017,DragonPunchStorm Tech.Co.,Ltd.

def generate_key(v13: int, v15: int) -> bytes:
    """
    根据头部两字节生成动态密钥，并直接补齐到 16 字节以供 cxxtea 使用。
    """
    v16 = v15 + v13
    v17 = v15 + v15 + v13
    v18 = v15 + v13 + v17
    v19 = v18 + v17 + v18
    v20 = v17 + v18 + v19
    
    n8 = max(8, v16 % 13)
    tl = len(lookup_table)
    
    # 预计算所有可能用到的索引
    indices = [v13, v15, v16, v17, v18, v17 + v18, v19, v20]
    if n8 > 8:
        v22 = v19 + v20
        indices.append(v22)
        if n8 > 9:
            v23 = v20 + v22
            indices.append(v23)
            if n8 > 10:
                v24 = v22 + v23
                indices.append(v24)
                if n8 == 12:
                    indices.append(v23 + v24)
    
    # 提取实际长度的密钥字节
    key = bytes(lookup_table[idx % tl] for idx in indices[:n8])
    
    # XXTEA 标准密钥需要 16 字节，不足部分用 \x00 补齐
    return key.ljust(16, b'\0')

def _target_path(output_path: Path, source: Path, ext: str) -> Path:
    name = source.name
    low = name.lower()
    image_like = low.endswith((".png", ".jpg", ".jpeg", ".webp")) or "@alpha" in low
    if ext == ".png" and image_like:
        return output_path
    if ext == ".lua" and low.endswith((".lua", ".luac")):
        return output_path
    if ext == ".json" and low.endswith(".json"):
        return output_path
    if ext in (".ccz", ".bin"):
        return output_path
    if output_path.suffix:
        return output_path.with_suffix(ext)
    return output_path.with_name(output_path.name + ext)


def decrypt_file(filepath: Path, output_path: Path = None, quiet: bool = False):
    log = (lambda *a: None) if quiet else print
    if output_path is not None and not FORCE and output_path.exists():
        return "skip"
    try:
        with open(filepath, 'rb') as f:
            head = f.read(7)
            if head == SIGN_LUA_CONF:
                is_lua = True
                sign_len = len(SIGN_LUA_CONF)
            elif head == SIGN_OTHER:
                is_lua = False
                sign_len = len(SIGN_OTHER)
            else:
                if not COPY_PLAIN or output_path is None:
                    return "skip"
                body = head + f.read()
                if output_path.resolve() == filepath.resolve():
                    return "skip"
                # 明文 .ccz 实为裸 PVR 纹理 -> 解码为 PNG（有同名 .png 双胞胎则跳过冗余件）
                if body[:4] in (PVR3_MAGIC, PVR2_MAGIC) and filepath.suffix.lower() == ".ccz":
                    if filepath.with_suffix(".png").exists():
                        return "skip"
                    try:
                        img = decode_pvr(body)
                    except Exception as e:
                        log(f"明文 PVR 解码失败 [{filepath.name}]: {e}")
                        img = None
                    if img is not None:
                        _out = output_path.with_suffix(".png")
                        _out.parent.mkdir(parents=True, exist_ok=True)
                        img.save(_out, format="PNG", compress_level=PNG_COMPRESS_LEVEL)
                        return "ccz-png"
                _out = output_path
                _out.parent.mkdir(parents=True, exist_ok=True)
                _out.write_bytes(body)
                return "copy"
            data = head + f.read()
    except OSError as e:
        log(f"读取失败 [{filepath}]: {e}")
        return "fail"
    
    datasrc = data[sign_len:]
    v13, v15 = datasrc[0], datasrc[1]
    key = generate_key(v13, v15)
    
    if is_lua:
        decrypt_len = len(datasrc) - 2
        datasrc_clean = datasrc[2:]
    else:
        decrypt_len = datasrc[5] | ((datasrc[4] | ((datasrc[3] | (datasrc[2] << 8)) << 8)) << 8)
        datasrc_clean = datasrc[6:]
    
    ciphertext = datasrc_clean[:decrypt_len]
    try:
        decrypted_bytes = cxxtea.decrypt(ciphertext, b"", key)
    except Exception as e:
        log(f"cxxtea 解密失败 [{filepath}]: {e}")
        return "fail"
    
    # 尾部填充
    final_data = b''.join((decrypted_bytes, datasrc_clean[decrypt_len:]))
    
    ext = ".bin"
    image = None
    pvr_fail = False
    if final_data.startswith(b'\x89PNG'):
        ext = ".png"
    elif final_data.startswith(b'\x1B\x4C\x75\x61') or is_lua:
        ext = ".lua"
    elif final_data.startswith((b'{', b'[')):
        ext = ".json"
    elif final_data.startswith(b"CCZ!"):
        try:
            final_data = decompress_ccz(final_data)
            image = decode_pvr(final_data)
            ext = ".png"
        except Exception as e:
            log(f"[FAIL] CCZ/PVR: {e}")
            ext = ".ccz"
            image = None
            pvr_fail = True
    else:
        pass
    
    if output_path is not None:
        _out = _target_path(output_path, filepath, ext)
    else:
        _out = filepath.with_suffix(ext)
    if pvr_fail and _out.suffix.lower() != ".ccz":
        _out = Path(str(_out) + ".ccz")
    _out.parent.mkdir(parents=True, exist_ok=True)

    if image:
        image.save(_out, format="PNG", compress_level=PNG_COMPRESS_LEVEL)
    else:
        _out.write_bytes(final_data)

    return "pvr-fail" if pvr_fail else "ok"




if __name__ == "__main__":
    SOURCE_DIR = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\illusionConnectRe\extract")
    OUTPUT_DIR = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\illusionConnectRe\output")
    WORKERS = min(32, (os.cpu_count() or 8))

    def work(p: Path):
        out = OUTPUT_DIR / p.relative_to(SOURCE_DIR)
        return decrypt_file(p, out, quiet=True)

    files = [p for p in SOURCE_DIR.rglob("*") if p.is_file()]
    stats = {"ok": 0, "skip": 0, "copy": 0, "ccz-png": 0, "fail": 0, "pvr-fail": 0}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(work, p): p for p in files}
        for fut in as_completed(futures):
            p = futures[fut]
            try:
                st = fut.result()
                stats[st if st in stats else "fail"] += 1
            except Exception as e:
                stats["fail"] += 1
                print(f"[FAIL] {p}: {e}")
    print(f"done: {stats}")