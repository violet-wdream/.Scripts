from Crypto.Cipher import AES
import struct
import binascii
import os
import sys

key = b'wiki is transfer'

def decrypt_aes(encrypted_file, output_file):
    with open(encrypted_file, 'rb') as f:
        file_content = f.read()

    # 未加密的 UnityFS 文件直接复制
    if file_content[:7] == b'UnityFS':
        with open(output_file, 'wb') as f:
            f.write(file_content)
        return

    iv_length = struct.unpack('<I', file_content[-4:])[0]
    assert iv_length == 16

    l = len(file_content)
    data_end = l - 4 - iv_length
    iv = file_content[data_end:l-4]
    encrypted_data = file_content[:data_end]

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = cipher.decrypt(encrypted_data)

    pad = decrypted_data[-1]
    decrypted_data = decrypted_data[:-pad]

    with open(output_file, 'wb') as f:
        f.write(decrypted_data)


if __name__ == '__main__':
    # 当前脚本所在目录
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 输出目录
    output_dir = os.path.join(base_dir, 'decrypted')
    os.makedirs(output_dir, exist_ok=True)

    print(f"开始自动搜索当前目录及其子目录...\n源目录: {base_dir}\n输出目录: {output_dir}")

    # 遍历并解密
    for root, dirs, files in os.walk(base_dir):
        # 跳过输出目录，避免递归解密已输出文件
        if root.startswith(output_dir):
            continue

        for file in files:
            encrypted_file = os.path.join(root, file)
            rel_path = os.path.relpath(root, base_dir)
            output_subdir = os.path.join(output_dir, rel_path)

            os.makedirs(output_subdir, exist_ok=True)
            output_file = os.path.join(output_subdir, file)

            print(f"处理: {encrypted_file} -> {output_file}")
            try:
                decrypt_aes(encrypted_file, output_file)
            except Exception as e:
                print(f"  解密失败: {str(e)}")

    print("\n解密完成！文件已保存到: " + output_dir)

    if sys.platform == 'win32':
        os.startfile(output_dir)
