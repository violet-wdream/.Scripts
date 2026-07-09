# 来自黑洞的旅人 MobileGoddess
# 用于解密 skel atlas png(webp)
import math
import struct
from pathlib import Path
# p.decrypt = function (buf) {
#   var bytes = new Uint8Array(buf);
#   var key = "AF&LM@nF23fK*vWp";     // 硬编码密钥，逐字节循环异或
#   for (var i = 0; i < bytes.length; i++) {
#     bytes[i] ^= key.charCodeAt(i % key.length);
#   }
#   return utf8Decode(bytes);          // 解密后是 JSON 格式的版本清单
# };
# ---------- MaskUtil const ----------
# MASK_SEQ = [0, 9, 2, 1, 8, 3, 7, 5, 6, 4]
# UNMASK_SEQ = [0, 3, 2, 5, 9, 7, 8, 6, 4, 1]
# KEY_STR = "%rt*p211-@"
# MASK_BYTES = list(KEY_STR.encode("utf-8"))  # 原始10字节
# MASK_CODE = [MASK_BYTES[i] for i in MASK_SEQ]  # 最终掩码字节
# MASK_INT = struct.unpack("<I", bytes(MASK_CODE[:4]))[0]  # 整数掩码


MAX_INT = 0x7fffffff
def get_mask_code(filename: str, data_len: int) -> int:

    # 取最后一个 '/' 之后的部分
    # filename = url.rsplit('/', 1)[-1] if '/' in url else url

    # 去掉扩展名
    filename = filename.rsplit('.', 1)[0] if '.' in filename else filename

    parts = filename.split('-') # e.g. baihua_m-86254f39cf

    if len(parts) > 1:
        try:
            ver = int(parts[1], 16)
        except ValueError:
            ver = MAX_INT
    else:
        ver = MAX_INT

    ver %= data_len

    while ver * 3 < MAX_INT:
        ver *= 3
    return ver

def codec(data: bytes, mask: int) -> bytes:
    length = len(data)
    s = math.floor(math.sqrt(length / 4))
    # 保证数据长度是 4 的倍数，并补齐到 s*s*4
    need = s * s * 4
    padded = data + b'\x00' * (need - length) if length < need else data
    # 对齐 4B
    if len(padded) % 4 != 0:
        padded += b'\x00' * (4 - (len(padded) % 4))

    # 以小端 u32 读取
    unpacked = list(struct.unpack('<' + 'I' * (len(padded) // 4), padded))
    ints = [x for x in unpacked]

    a = s
    o = s
    h = 48

    if s < 2 * h:
        h = math.floor(s / 2)

    for y in range(o):
        if (y // h) % 2 != 0:
            continue

        for x in range(a):
            new_x = x
            new_y = y
            skip = False

            if y + h < o:
                new_y = y + h
            else:
                skip = True

            if (x // h) % 2 == 0:
                if x + h < a:
                    new_x = x + h
            else:
                if skip:
                    continue  # y 越界且 x 在后半块，跳过
                new_x = x - h


            idx1 = y * a + x
            idx2 = new_y * a + new_x
            tmp = ints[idx1]
            ints[idx1] = ints[idx2] ^ mask
            ints[idx2] = tmp ^ mask

    result = struct.pack('<' + 'I' * len(ints), *ints)
    return result[:length]  # 截断到原始长度


def decrypt_asset(url: str, encrypted_data: bytes) -> bytes:
    mask = get_mask_code(url, len(encrypted_data))
    return codec(encrypted_data, mask)

if __name__ == "__main__":
    # 测试
    test_path = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\HeiDong_crypto\avatar\sp")
    out_path = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\HeiDong_crypto\out")
    for file in test_path.rglob("*"):
        if not file.is_file():
            continue
        test_name = file.name
        test_data = file.read_bytes()
        decrypted_data = decrypt_asset(test_name, test_data)

        ext = test_name.rsplit('.')[-1]
        out_name = test_name.split('-')[0] + '.' + ext
        out_file = out_path / out_name
        out_file.write_bytes(decrypted_data)
