
BASE64_KEYS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
BASE64_MAP = {c: i for i, c in enumerate(BASE64_KEYS)}

def decompress(base64_str):
    """
    解压: 将 22位 Cocos 压缩 ID 转换为标准 36位 UUID
    """
    if len(base64_str) != 22:
        return base64_str

    # 前两个字符保持不变
    uuid_chars = [base64_str[:2]]
    
    # 后续每 2 个 Base64 字符解析为 3 个 Hex 字符 (12 bits -> 12 bits)
    for i in range(2, 22, 2):
        lhs = BASE64_MAP[base64_str[i]]
        rhs = BASE64_MAP[base64_str[i+1]]
        
        # 重组位运算
        # Hex1: lhs 高4位
        # Hex2: lhs 低2位 + rhs 高2位
        # Hex3: rhs 低4位
        val = (lhs << 6) | rhs
        uuid_chars.append(f"{val:03x}")

    hex_str = "".join(uuid_chars)
    
    # 按照 8-4-4-4-12 格式插入连字符
    return f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:]}"

def compress(full_uuid):
    """
    压缩: 将标准 36位 UUID 转换为 22位 Cocos压缩 ID
    """
    # 处理可能有后缀的情况 (如: uuid@import)
    parts = full_uuid.split('@')
    uuid = parts[0]
    
    if len(uuid) != 36:
        return full_uuid

    # 去掉原有的连字符
    clean_uuid = uuid.replace('-', '')
    
    # 前两个字符直接保留
    res = [clean_uuid[:2]]
    
    # 后续每 3 个 Hex 字符压缩为 2 个 Base64 字符
    for i in range(2, 32, 3):
        # 解析 3 个 Hex 字符为整数
        val = int(clean_uuid[i:i+3], 16)
        
        # 拆分为 2 个 Base64 索引
        res.append(BASE64_KEYS[(val >> 6) & 0x3F])
        res.append(BASE64_KEYS[val & 0x3F])

    compressed = "".join(res)
    
    return compressed if len(parts) == 1 else f"{compressed}@{parts[1]}"

if __name__ == '__main__':
    # 压缩
    uuid36 = "d038ec75-346e-40c7-8ee8-433114ce5ece"
    print(f"压缩结果: {compress(uuid36)}")

    # 解压
    uuid22 = "a9gRG/jpVA7rf6TAOLTWaO"
    print(f"解压结果: {decompress(uuid22)}")


