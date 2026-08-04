from pathlib import Path
from hashlib import md5
import cxxtea
import zlib
import re
# MD5
PATHLIST = "5fb3ffbe6a0ecfa290f72b0347f7cda7"
MLIST = md5("mlist".encode()).hexdigest()
INITLIST = md5("initlist".encode()).hexdigest()

# RE
skel_pattern = re.compile(rb'\x07\d\.\d\.\d{1,2}')

# XOR
HEX_TABLE = [0xFF] * 256
for i, ch in enumerate(range(ord('0'), ord('9') + 1)):
    HEX_TABLE[ch] = i
for i, ch in enumerate(range(ord('A'), ord('F') + 1)):
    HEX_TABLE[ch] = 0xA + i
for i, ch in enumerate(range(ord('a'), ord('f') + 1)):
    HEX_TABLE[ch] = 0xA + i

# XXTEA
XXTEA_KEY = "SDFKAR%$#JEIQWOFJ(@!=dsa"
SIGN_XXTEA_ZLIB = b"\x03\x15\x20\x00"
SIGN_XXTEA = b"\x04\x15\x20\x00"


def hex_string_to_key(hex_str: str) -> bytearray:
    if len(hex_str) != 32:
        raise ValueError("Key must be 32 hex characters")
    key = bytearray()
    for i in range(0, 32, 2):
        hi = HEX_TABLE[ord(hex_str[i])]
        lo = HEX_TABLE[ord(hex_str[i+1])]
        if hi == 0xFF or lo == 0xFF:
            raise ValueError(f"Invalid hex char at {i}")
        key.append((hi << 4) | (lo & 0xF))
    return key

def xor_decrypt_data(data: bytes, filename: str, max_len: int = 16) -> bytes:
    if '.' in filename or len(filename) != 32:
        raise ValueError("Filename must be 32 hex characters without extension")

    key = hex_string_to_key(filename)

    n = min(len(data), max_len)

    data = bytearray(data)
    for index in range(n):
        data[index] ^= key[index]
    return bytes(data)

def xxtea_decrypt_data(data: bytes, sign, key) -> bytes:
    if data.startswith(sign):
        out = cxxtea.decrypt(data, sign, key.encode('utf-8'))
        if out is None:
            print("xxtea 解密失败")
            return data
        else:
            pass
            # print("xxtea 解密成功")
        return out
    else:
        print("不是 xxtea 数据")
        return data

def try_zlib(data: bytes) -> bytes:
    if not data.startswith(b'\x78\x9C'):
        print("Not zlib data")
        return data
    try:
        return zlib.decompress(data)
    except OSError as e:
        return data

def zlib_decompress_data(data: bytes, pos: int = 4) -> bytes:
    data = try_zlib(data[pos:])
    return data

def ext_name(sig: bytes, data: bytes) -> str:

    if sig == b"\x89PNG":
        return ".png"
    elif sig[:3] == b"\xFF\xD8\xFF":
        return ".jpg"
    elif sig == b"ibcc":
        return ".ccbi"

    elif b'<!DOCTYPE plist' in data:
        return ".plist"
    elif b'<?xml' in data:
        return ".xml"
    elif b'gasp' in data:
        return ".ttf"
    elif b'PK\x03\x04' in data:
        return ".zip"
    elif b'ID3' in data:
        return ".mp3"
    elif b'GL_ES' in data:
        return ".shader"
    elif b'"skeleton":' in data:
        return ".json"
    elif skel_pattern.search(data):
        return ".skel"
    elif b'size:' in data:
        return ".atlas"
    else:
        return ""

if __name__ == "__main__":
    input_dir = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\DaoYou\download")
    output_dir = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\DaoYou\out")
    output_dir.mkdir(parents=True, exist_ok=True)

    unknown_files = 0
    unknown_sign_dict: dict[str, int] = {} # signature hex -> count

    for file in input_dir.rglob("*"):
        if not file.is_file():
            continue

        name = file.name

        # 跳过 mp3 ogg
        if name.endswith(".mp3") or name.endswith(".ogg"):
            continue

        # 只处理 32 位 hex 文件名
        if len(name) != 32:
            continue
        try:
            encrypted_data: bytes = file.read_bytes()
            decrypted_data: bytes = xor_decrypt_data(encrypted_data, name)
            signature: bytes = decrypted_data[:4]

            if name == MLIST:
                decrypted_data = zlib_decompress_data(decrypted_data, 4)
                name = "mlist"

            elif name == INITLIST:
                decrypted_data = zlib_decompress_data(decrypted_data, 4)
                name = "initlist"

            elif name == PATHLIST:
                name = "pathlist"

            ext = ext_name(signature, decrypted_data)

            if signature in (SIGN_XXTEA_ZLIB, SIGN_XXTEA): # xxtea
                use_zlib = signature == SIGN_XXTEA_ZLIB
                # print(f"[INFO] {file}: XXTEA{' + ZLIB' if use_zlib else ''}")
                decrypted_data = xxtea_decrypt_data(decrypted_data, signature, XXTEA_KEY)
                if use_zlib:
                    decrypted_data = zlib_decompress_data(decrypted_data, 4)

                if b"()" in decrypted_data: # jsc
                    ext = ".jsc"
                else: # other
                    ext = ".bin"

            elif ext == "":
                unknown_files += 1
                unknown_sign_dict[signature.hex()] = unknown_sign_dict.get(signature.hex(), 0) + 1

            name += ext
            out_path = output_dir / name
            out_path.write_bytes(decrypted_data)

        except Exception as e:
            print(f"[ERROR] {file}: {e}")

    print(f"[INFO] Finished. Unknown {unknown_files} files.")
    # 输出前三个数量最多的未知签名
    sorted_unknown_signs = sorted(unknown_sign_dict.items(), key=lambda x: x[1], reverse=True)[:3]
    print(f"[INFO] Top 3 unknown signatures: {sorted_unknown_signs}")
