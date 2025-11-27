import os
import sys

# --- 1. 定义核心解密函数 ---
def dec(e: str, d: str) -> bool:
    """
    对文件e的前64个字节进行异或 0xFF 操作，并将结果写入文件d。
    e: 待处理文件名/路径
    d: 输出文件名/路径
    返回: 成功则返回 True，失败返回 False。
    """
    try:
        # 以二进制模式读取文件内容
        with open(e, 'rb') as f:
            enc = f.read()
        
        # 转换为可变字节数组
        data = bytearray(enc)
        
        # 确定操作范围：文件长度或 64 字节，取最小值
        byte_limit = min(len(data), 64)
        
        # 执行异或 0xFF (按位取反) 操作
        for i in range(byte_limit):
            # 核心操作：异或 0xFF
            data[i] ^= 0xFF
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(d), exist_ok=True)
        
        # 写入处理后的数据
        with open(d, 'wb') as f:
            f.write(data)
        
        # 打印信息时，原文件和输出文件都是相同的 basename
        print(f"✅ 处理成功：'{os.path.basename(e)}' -> '{d}'")
        return True
    except Exception as error:
        print(f"❌ 处理文件 '{e}' 时发生错误: {error}")
        return False

# --- 2. 搜索和处理文件 ---

def main():
    # 获取脚本运行的当前目录 (作为搜索的根目录)
    current_dir = os.getcwd()
    
    # 定义输出目录
    OUTPUT_DIR = os.path.join(current_dir, "output")
    
    # 创建 output 文件夹
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("=" * 60)
    print(f"📂 所有处理后的文件将保存到目录: '{OUTPUT_DIR}'")
    print(f"🔍 开始在目录 '{current_dir}' 及其子目录中搜索所有文件...")
    print("=" * 60)

    # 遍历当前目录下的所有文件和子目录
    for root, dirs, files in os.walk(current_dir):
        # 忽略 output 目录本身
        if root.startswith(OUTPUT_DIR):
            continue
            
        for filename in files:
            file_path = os.path.join(root, filename)
            
            # 排除自身脚本文件
            if file_path == os.path.abspath(__file__):
                continue
            
            # --- 注意：由于输出文件名与原文件一致，我们无法再通过后缀排除已处理文件。 ---
            
            try:
                # 1. 计算文件相对于搜索根目录的路径
                relative_dir = os.path.relpath(root, current_dir)
                
                # 2. 构造输出文件在 OUTPUT_DIR 下的目录
                output_sub_dir = os.path.join(OUTPUT_DIR, relative_dir)
                os.makedirs(output_sub_dir, exist_ok=True) # 创建必要的子目录
                
                # 3. 构造最终的输出文件路径 (文件名与原文件一致)
                # ****** 关键改动在这里：移除了 "_dec" 后缀 ******
                dec_file_path = os.path.join(output_sub_dir, filename) 
                
                # 执行处理操作
                dec(file_path, dec_file_path)
                    
            except IOError as e:
                # 忽略无法访问或权限不足的文件
                print(f"⚠️ 无法读取文件 '{file_path}': {e}")
            except Exception as e:
                # 捕获其他未知错误
                print(f"🚨 处理文件 '{file_path}' 时发生未知错误: {e}")

    print("=" * 60)
    print("✅ 所有文件处理操作已完成。")

if __name__ == "__main__":
    main()