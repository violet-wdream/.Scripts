import json
import sys
import datetime
import os

def find_key_differences_with_values(dict1, dict2):
    """
    比较两个字典的顶级键，并返回仅存在于其中一个字典的键及其对应的值。
    """
    keys1 = set(dict1.keys())
    keys2 = set(dict2.keys())

    # 找出独有的键
    only_keys_in_file1 = keys1 - keys2
    only_keys_in_file2 = keys2 - keys1

    # 提取独有的键值对
    diff_values = {}
    
    # 添加 file1 中独有的键值对
    for key in only_keys_in_file1:
        diff_values[key] = dict1[key]

    # 添加 file2 中独有的键值对
    for key in only_keys_in_file2:
        diff_values[key] = dict2[key]
        
    return diff_values

def main():
    # 检查命令行参数数量
    if len(sys.argv) != 3:
        print("用法: python update.py <file1.json> <file2.json>")
        sys.exit(1)

    file1_path = sys.argv[1]
    file2_path = sys.argv[2]

    # 1. 读取 JSON 文件
    try:
        with open(file1_path, 'r', encoding='utf-8') as f:
            data1 = json.load(f)
        with open(file2_path, 'r', encoding='utf-8') as f:
            data2 = json.load(f)
    except FileNotFoundError as e:
        print(f"错误: 文件未找到: {e.filename}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("错误: 文件内容不是有效的 JSON 格式。")
        sys.exit(1)
    except Exception as e:
        print(f"读取文件时发生未知错误: {e}")
        sys.exit(1)

    # 确保加载的数据是字典 (假设 JSON 文件的顶级结构是对象)
    if not isinstance(data1, dict) or not isinstance(data2, dict):
        print("警告: 至少有一个 JSON 文件的顶级结构不是对象 (字典)。脚本将退出。")
        sys.exit(1)

    # 2. 比较键差异并获取值
    diff_values = find_key_differences_with_values(data1, data2)

    # 3. 准备输出内容
    # 获取当前时间，格式化为 YYYYMMDD_HHMMSS
    current_time_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 构造输出文件名: index.update-YYYYMMDD_HHMMSS.txt
    output_filename = f"index.update-{current_time_str}.txt"

    # 构造最终的 JSON 格式输出内容
    # 核心内容就是 diff_values 字典本身
    
    # 4. 写入输出文件
    try:
        # 使用 json.dumps 格式化为 JSON 字符串，确保内容是 JSON 形式
        # indent=4 使输出结果保持您示例中那种缩进格式
        json_output_content = json.dumps(diff_values, indent=4, ensure_ascii=False)
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(json_output_content)
        
        print(f"键差异比较完成，并提取了差异值。")
        print(f"输出文件已保存到: **{output_filename}**")
        print(f"文件内容 (JSON 格式) 如下:")
        print("---")
        print(json_output_content)
        print("---")
        
    except Exception as e:
        print(f"写入输出文件时发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()