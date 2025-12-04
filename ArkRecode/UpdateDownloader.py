import os
import json
import requests
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time

lock = Lock()  # 线程安全写日志

def download_file(url: str, save_dir: str, log_file: str, max_retries: int = 4):
    """下载单个文件，如果失败重试 max_retries 次，仍失败写入 log_file"""
    os.makedirs(save_dir, exist_ok=True)
    filename = os.path.basename(url)
    save_path = os.path.join(save_dir, filename)

    headers = {
        "User-Agent": "PythonCatalogDownloader/1.0"
    }

    attempt = 0
    while attempt <= max_retries:
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            print(f"✅ 下载完成: {filename}")
            return
        except Exception as e:
            attempt += 1
            if attempt <= max_retries:
                print(f"⚠️ 下载失败: {filename}，重试 {attempt}/{max_retries} ...")
                time.sleep(2)  # 简单延时后重试
            else:
                print(f"❌ 下载失败: {filename}，已超过最大重试次数")
                with lock:
                    with open(log_file, "a", encoding="utf-8") as logf:
                        logf.write(url + "\n")
                return

def main(json_file: str, output_dir: str, threads: int = 8, retries: int = 4):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    urls = data.get("added", [])
    if not urls:
        print("⚠️ JSON 中没有找到 'added' 数组")
        return

    log_file = "404.log"
    # 清空旧日志
    if os.path.exists(log_file):
        os.remove(log_file)

    print(f"开始下载 {len(urls)} 个文件，线程数: {threads}，最大重试次数: {retries}")

    # 多线程下载
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(download_file, url, output_dir, log_file, retries) for url in urls]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"❌ 下载任务异常: {e}")

    print(f"\n下载完成。失败的 URL 已记录在 {log_file}（如果有）")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="多线程下载 catalog-update JSON 中的文件，失败重试 4 次并记录 404.log")
    parser.add_argument("json_file", help="包含 'added' 数组的 JSON 文件")
    parser.add_argument("--output", default="output", help="下载保存目录")
    parser.add_argument("--threads", type=int, default=8, help="同时下载线程数")
    parser.add_argument("--retries", type=int, default=4, help="失败自动重试次数")
    args = parser.parse_args()

    main(args.json_file, args.output, args.threads, args.retries)
