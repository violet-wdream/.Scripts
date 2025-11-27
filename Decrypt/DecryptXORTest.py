import os
import struct


class BundleDecryptor:
    def __init__(self):
        self.total_bundles = 0
        self.success_count = 0
        self.error_count = 0

    def analyze_encryption(self, data):
        """分析加密模式"""
        print("分析文件加密模式...")

        # 检查文件头
        header = data[:100]
        print(f"文件头 (hex): {header[:50].hex()}")
        print(f"文件头 (ascii): {''.join(chr(b) if 32 <= b < 127 else '.' for b in header[:50])}")

        # 查找可能的模式
        patterns = {}
        for i in range(len(data) - 4):
            pattern = data[i:i + 4]
            patterns[pattern] = patterns.get(pattern, 0) + 1

        # 打印最常见的模式
        common_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:10]
        print("常见字节模式:")
        for pattern, count in common_patterns:
            print(f"  {pattern.hex():8} - 出现 {count} 次")

        return common_patterns

    def try_xor_decryption(self, data, key=None):
        """尝试XOR解密"""
        if key is None:
            # 尝试自动检测key
            possible_keys = []
            for test_key in range(256):
                # 检查解密后是否包含Unity常见签名
                test_decrypt = bytes(b ^ test_key for b in data[:100])
                if b'Unity' in test_decrypt or b'UnityFS' in test_decrypt:
                    possible_keys.append(test_key)

            if possible_keys:
                key = possible_keys[0]
                print(f"检测到可能的XOR密钥: {key} (0x{key:02x})")
            else:
                # 使用统计方法找key
                key = self.find_xor_key_statistical(data)
                print(f"使用统计方法找到XOR密钥: {key} (0x{key:02x})")

        return bytes(b ^ key for b in data), key

    def find_xor_key_statistical(self, data):
        """使用统计方法查找XOR密钥"""
        # 假设空格(0x20)是最常见的字节
        byte_counts = [0] * 256
        for byte in data[:1000]:  # 只分析前1000字节提高速度
            byte_counts[byte] += 1

        # 找到最常见的字节，假设它是空格(0x20)加密后的结果
        most_common_byte = byte_counts.index(max(byte_counts))
        key = most_common_byte ^ 0x20

        return key

    def try_rolling_xor(self, data, key_sequence):
        """尝试滚动XOR解密"""
        result = bytearray()
        key_len = len(key_sequence)
        for i, byte in enumerate(data):
            result.append(byte ^ key_sequence[i % key_len])
        return bytes(result)

    def check_unity_signature(self, data):
        """检查Unity文件签名"""
        signatures = [
            b'UnityFS',
            b'UnityWeb',
            b'UnityRaw',
            b'UnityArchive'
        ]

        for sig in signatures:
            if sig in data[:100]:
                return True, sig
        return False, None

    def decrypt_and_save(self, file_path):
        """解密并保存文件"""
        self.total_bundles += 1
        print(f"\n处理文件: {os.path.basename(file_path)}")

        try:
            with open(file_path, "rb") as f:
                data = f.read()

            if len(data) < 100:
                print("文件太小，可能不是有效的bundle文件")
                self.error_count += 1
                return False

            # 分析加密模式
            self.analyze_encryption(data)

            # 尝试多种解密方法
            decrypted_data = None
            method_used = ""

            # 方法1: 简单XOR解密
            print("尝试XOR解密...")
            decrypted_data, xor_key = self.try_xor_decryption(data)
            is_unity, signature = self.check_unity_signature(decrypted_data)

            if is_unity:
                method_used = f"XOR (key: 0x{xor_key:02x})"
                print(f"✓ XOR解密成功! 检测到Unity签名: {signature}")
            else:
                # 方法2: 尝试带偏移的XOR
                print("尝试带偏移的XOR解密...")
                for offset in [50, 100, 200]:
                    if offset < len(data):
                        test_data = data[offset:]
                        test_decrypted, test_key = self.try_xor_decryption(test_data)
                        is_unity, signature = self.check_unity_signature(b' ' * offset + test_decrypted)
                        if is_unity:
                            decrypted_data = data[:offset] + test_decrypted
                            method_used = f"XOR with offset {offset} (key: 0x{test_key:02x})"
                            print(f"✓ 带偏移解密成功! 偏移: {offset}, 签名: {signature}")
                            break

            if decrypted_data and self.check_unity_signature(decrypted_data)[0]:
                # 保存解密后的文件
                decrypted_file_path = file_path + ".decrypted"
                with open(decrypted_file_path, "wb") as f:
                    f.write(decrypted_data)

                self.success_count += 1
                print(f"✓ 解密成功! 方法: {method_used}")
                print(f"  保存为: {os.path.basename(decrypted_file_path)}")
                return True
            else:
                print("✗ 所有解密方法都失败了")
                self.error_count += 1
                return False

        except Exception as e:
            print(f"✗ 处理文件时出错: {str(e)}")
            self.error_count += 1
            return False

    def process_directory(self, directory=None):
        """处理目录中的所有bundle文件"""
        if directory is None:
            directory = os.getcwd()

        bundle_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".bundle") and not file.endswith(".decrypted"):
                    bundle_files.append(os.path.join(root, file))

        print(f"找到 {len(bundle_files)} 个bundle文件")

        for file_path in bundle_files:
            self.decrypt_and_save(file_path)

    def print_summary(self):
        """打印总结"""
        print(f"\n" + "=" * 50)
        print("解密完成总结:")
        print(f"总文件数: {self.total_bundles}")
        print(f"成功: {self.success_count}")
        print(f"失败: {self.error_count}")
        print("=" * 50)


def main():
    # 设置工作目录到脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("Unity Bundle 文件解密工具")
    print("正在分析加密模式...")

    decryptor = BundleDecryptor()
    decryptor.process_directory()
    decryptor.print_summary()

    input("按回车键退出...")


if __name__ == "__main__":
    main()