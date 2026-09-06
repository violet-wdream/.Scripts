import struct
import zlib
import cxxtea
import os

SIGN_LUA_CONF = b"@D#P$S%"
SIGN_OTHER = b"@S#T$O%"

# ---------- 1. 预计算 Lookup Table ----------
v91_signed = [
    -10, -103, -23, -112, -30, -117, -20, -124, -16, -40, -101, -78, -98, -84, -100, -83,
    -102, -74, -14, 0x80, -31, -122, -23, -121, -41, -94, -52, -81, -57, -108, -32, -113,
    -3, -112, -80, -28, -127, -30, -118, -92, -25, -120, -90, -118, -58, -78, -42, -8, -8
]

lookup_table = bytearray(49)
xor_val = 0xB5
for i, b in enumerate(v91_signed):
    val = b & 0xFF
    lookup_table[i] = xor_val ^ val
    xor_val = val
lookup_table = bytes(lookup_table[:-1])  # 去掉末尾字节，保留实际使用的 48 字节
print(f"{lookup_table}")
# Copyright(C),2017,DragonPunchStorm Tech.Co.,Ltd.

# ---------- 2. 生成动态密钥 ----------
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


# ---------- 3. 主解密逻辑 ----------
def decrypt_encrypted_file(filepath: str, output_path: str = None):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # 自动识别类型
    if data.startswith(SIGN_LUA_CONF):
        is_lua = True
        sign_len = len(SIGN_LUA_CONF)
    elif data.startswith(SIGN_OTHER):
        is_lua = False
        sign_len = len(SIGN_OTHER)
    else:
        print(f"跳过：未识别的签名 -> {os.path.basename(filepath)}")
        return
    
    datasrc = data[sign_len:]
    # 动态获取特征字节并生成密钥
    v13, v15 = datasrc[0], datasrc[1]
    key = generate_key(v13, v15)
    
    if is_lua:
        decrypt_len = len(datasrc) - 2
        datasrc_clean = datasrc[2:]
    else:
        # 非 Lua 资源（如图片），解析 4 字节真实长度
        decrypt_len = datasrc[5] | ((datasrc[4] | ((datasrc[3] | (datasrc[2] << 8)) << 8)) << 8)
        datasrc_clean = datasrc[6:]
    
    # 截取精确需要解密的密文段
    ciphertext = datasrc_clean[:decrypt_len]
    try:
        decrypted_bytes = cxxtea.decrypt(ciphertext, b"", key)
    except Exception as e:
        print(f"cxxtea 解密失败 [{filepath}]: {e}")
        return
    
    # 拼回未加密的尾部填充（如果有的话）
    final_data = b''.join((decrypted_bytes, datasrc_clean[decrypt_len:]))
    
    # 自动推断后缀
    ext = ".bin"
    if final_data.startswith(b'\x89PNG'):
        ext = ".png"
    elif final_data.startswith(b'\x1B\x4C\x75\x61') or is_lua:
        ext = ".lua"
    elif final_data.startswith((b'{', b'[')):
        ext = ".json"
    elif final_data.startswith(b'CCZ!'):
        print("检测到 CCZ 压缩容器，正在解压...")
        try:
            # CCZ 通常使用 zlib 压缩，真实数据从偏移 16 字节开始
            # 前 16 字节包含了压缩类型和解压后大小等元数据
            compression_type = struct.unpack('>H', final_data[4:6])[0]
            uncompressed_size = struct.unpack('>I', final_data[12:16])[0]
            
            zlib_data = final_data[16:]
            # 配合 zlib 解压
            raw_image_data = zlib.decompress(zlib_data)
            print(f"CCZ 解压成功, 原始大小: {len(raw_image_data)} 字节")
            final_data = raw_image_data
            ext = ".pvr"
        except Exception as e:
            print(f"CCZ 解压失败，保存为普通二进制: {e}")
            ext = ".ccz"
    
    out = output_path or (filepath + ext)
    with open(out, 'wb') as f:
        f.write(final_data)
    print(f"成功解密并保存: {out}")


# ---------- 使用示例 ----------
if __name__ == "__main__":
    test_dir = r"D:\Tools\UsefulTools\MuMu\Shared\Download\illusionConnectRe\test\bak"
    if os.path.exists(test_dir):
        for root, _, files in os.walk(test_dir):
            for file in files:
                decrypt_encrypted_file(os.path.join(root, file))
    else:
        print(f"找不到目录: {test_dir}")