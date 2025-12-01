import os
import sys
import re
import requests
from urllib.parse import urlparse

# 配置参数
LOG_FILE_PATH = "404.log"  # 默认的日志文件名
ERROR_OUTPUT_DIR = "errorAsset"  # 错误文件输出目录

def read_and_parse_log(log_path):
    """
    读取日志文件，并解析出 URL 和本地路径对。
    假设日志格式是 URL 和 本地路径 成对出现，中间可能被空行或错误信息打断。
    
    Args:
        log_path (str): 日志文件的路径。

    Returns:
        list: 包含 (url, local_path) 元组的列表。
    """
    pairs = []
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]  # 读取非空行

        # 使用正则表达式匹配 URL (以 http/https 开头)
        url_pattern = re.compile(r'^https?://.*')
        
        # 迭代处理行，寻找 URL 和其后的本地路径
        i = 0
        while i < len(lines):
            url = lines[i]
            
            # 检查当前行是否是 URL
            if url_pattern.match(url):
                # 假设下一个非空行是对应的本地路径
                if i + 1 < len(lines):
                    local_path = lines[i + 1]
                    pairs.append((url, local_path))
                    i += 2  # 跳过下一行（本地路径）
                else:
                    print(f"警告: 发现 URL 但没有对应的本地路径: {url}")
                    i += 1
            else:
                # 忽略非 URL/本地路径的行（例如错误信息、分隔符）
                i += 1

    except FileNotFoundError:
        print(f"错误: 日志文件未找到: {log_path}")
        sys.exit(1)
    except Exception as e:
        print(f"读取或解析日志文件时发生错误: {e}")
        sys.exit(1)
        
    return pairs

def download_file(url, local_path):
    """
    尝试从 URL 下载文件到指定的本地路径。
    
    Args:
        url (str): 待下载文件的 URL。
        local_path (str): 待保存的本地路径 (包含文件名)。

    Returns:
        bool: 下载成功返回 True，失败返回 False。
    """
    print(f"尝试下载: {url}")
    
    try:
        # 使用流模式下载，以便处理大文件
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()  # 检查 HTTP 响应状态，如果失败会抛出异常
        
        # 确定最终输出路径
        # 1. 获取 URL 中的文件名作为真正的文件名 (例如：mirror_effect_m6.6089c2f6bc4c5ff8e18ba2b23f83cb4c)
        # 2. 避免使用 local_path 中可能包含的路径信息，只使用文件名
        
        # 从 URL 中提取文件名 (通常是 URL 路径的最后一部分)
        # 确保文件名是原始 URL 中的那一部分，不包含路径分隔符
        parsed_url = urlparse(url)
        url_file_name = os.path.basename(parsed_url.path)
        
        # 组合最终的保存路径： errorAsset 目录 + URL 中的文件名
        final_save_path = os.path.join(ERROR_OUTPUT_DIR, url_file_name)

        # 写入文件
        with open(final_save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        print(f"  -> **成功**。文件保存至: {final_save_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"  -> **失败** (网络/HTTP 错误): {e}")
        return False
    except IOError as e:
        print(f"  -> **失败** (文件写入错误): {e}")
        return False
    except Exception as e:
        print(f"  -> **失败** (未知错误): {e}")
        return False

def main():
    # 1. 检查命令行参数，允许用户指定日志文件
    if len(sys.argv) > 1:
        log_file_to_use = sys.argv[1]
    else:
        log_file_to_use = LOG_FILE_PATH
        
    print(f"*** 开始分析日志文件: {log_file_to_use} ***")

    # 2. 创建输出目录
    if not os.path.exists(ERROR_OUTPUT_DIR):
        os.makedirs(ERROR_OUTPUT_DIR)
        print(f"已创建输出目录: {ERROR_OUTPUT_DIR}")
    else:
        print(f"输出目录已存在: {ERROR_OUTPUT_DIR}")

    # 3. 解析日志
    download_targets = read_and_parse_log(log_file_to_use)
    
    if not download_targets:
        print("日志文件中未找到有效的 URL-本地路径 对，程序退出。")
        return

    print(f"\n共找到 {len(download_targets)} 个待重新下载的目标。")
    print("-" * 30)

    # 4. 尝试重新下载
    success_count = 0
    fail_count = 0
    
    for url, local_path in download_targets:
        if download_file(url, local_path):
            success_count += 1
        else:
            fail_count += 1

    # 5. 总结
    print("\n" + "=" * 40)
    print(f"重新下载尝试完成。")
    print(f"总计目标: {len(download_targets)}")
    print(f"成功下载: {success_count} 个")
    print(f"失败下载: {fail_count} 个")
    print(f"文件已保存至目录: {os.path.abspath(ERROR_OUTPUT_DIR)}")
    print("=" * 40)

if __name__ == "__main__":
    main()