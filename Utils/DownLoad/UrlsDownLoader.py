import json

import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import zipfile
THREADS = 16
TIMEOUT = 15
session = requests.Session()

def download_one(url: str, output_dir: Path) -> str:
    url = url.strip()
    if not url:
        raise ValueError("URL is empty")

    name = url.rstrip("/").split("/")[-1]
    out_file = output_dir / name
    if out_file.exists():
        return ""  # 已存在，静默跳过
    try:
        print(f"Downloading: {name}")
        r = session.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        out_file.write_bytes(r.content)

        if zipfile.is_zipfile(out_file):
            try:
                with zipfile.ZipFile(out_file, 'r') as zf:
                    zf.extractall(output_dir)
                out_file.unlink()  # 解压成功，删除 ZIP
            except Exception as e:
                return f"UNZIP FAIL: {name}  {e}"

        return ""  # 成功，无输出
    except Exception as e:
        return f"FAIL: {name}  {e}"

def main():
    input_file = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\res_base_classify_download.json")
    output_path = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\PTN")
    # if not input_file.exists():
    #     raise FileNotFoundError(f"文件 {input_file} 不存在")
    #
    # urls = [line.strip() for line in input_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    
    base = "https://xonecn-hotupdatecdn.shziyi.com/release-cn/android/tags/major/2.5/classify/0/classify"
    urls = [base + i["Name"] for i in json.load(open(input_file, encoding="utf-8"))["Infos"]]
    
    print(f"总计 {len(urls)} 条，开始下载…")

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(download_one, url, output_path) for url in urls]
        for future in as_completed(futures):
            err = future.result()
            if err:  # 仅错误信息打印
                print(err)

if __name__ == "__main__":
    main()