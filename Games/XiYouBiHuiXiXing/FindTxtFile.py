import os
import shutil
import re

source_path = r"C:/Users/86182/Downloads/bundles"
output_path = os.path.join(source_path, "identified_txt")

def is_pure_text(data):
    """
    通过分析数据块来判断是否为纯文本
    """
    if not data:
        return False
        
    # 1. 检查是否存在大量的 NULL 字节 (\x00)，这是二进制文件最明显的特征
    if b'\x00' in data:
        # 允许极少数出现（有些编辑器保存时可能带少量空字节），但如果超过 1% 肯定是二进制
        if data.count(b'\x00') > (len(data) * 0.01):
            return False

    # 2. 检查 Spine 特征：如果包含版本号（数字.数字.数字）且周围有不可读字符
    if re.search(rb'\d+\.\d+\.\d+', data):
        # 进一步确认：如果是文本，剩下的字符应该是可打印的
        non_printable = len([b for b in data if b < 32 and b not in (9, 10, 13)]) # 排除 tab, lf, cr
        if non_printable > 5:
            return False

    # 3. 尝试解码
    try:
        data.decode('utf-8')
        return True
    except UnicodeDecodeError:
        try:
            data.decode('gbk') # 兼容中文
            return True
        except UnicodeDecodeError:
            return False

def extract_txt():
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    print(f"正在扫描: {source_path}")
    txt_count = 0
    
    for filename in os.listdir(source_path):
        if not filename.lower().endswith('.u2d'):
            continue
            
        file_path = os.path.join(source_path, filename)
        
        try:
            with open(file_path, 'rb') as f:
                # 读取前 1024 字节进行深度采样
                chunk = f.read(1024)
                
                # 排除 Unity 明确特征
                if any(tag in chunk for tag in [b'UnityFS', b'UnityWeb', b'UnityRaw']):
                    continue
                
                # 执行文本特征综合判断
                if is_pure_text(chunk):
                    target_file = os.path.join(output_path, filename.replace('.u2d', '.txt'))
                    shutil.copy2(file_path, target_file)
                    txt_count += 1
                    print(f"[找到文本] {filename}")
                    
        except Exception as e:
            print(f"读取 {filename} 出错: {e}")

    print(f"\n--- 处理完成 ---")
    print(f"共提取 TXT 文件: {txt_count} 个")
    print(f"结果保存在: {output_path}")

if __name__ == "__main__":
    extract_txt()