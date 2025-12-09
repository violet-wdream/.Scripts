import os
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

OUTPUT_DIR = "output"


def download_one(url):
    url = url.strip()
    if not url:
        return "SKIP"

    name = url.rstrip("/").split("/")[-1]
    path = os.path.join(OUTPUT_DIR, name)

    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()

        with open(path, "wb") as f:
            f.write(r.content)

        return f"OK: {name}"
    except Exception as e:
        return f"FAIL: {name}  {e}"


def main():
    if len(sys.argv) < 2:
        print("用法: python download_urls.py list.txt")
        return

    txt = sys.argv[1]

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open(txt, "r", encoding="utf-8") as f:
        urls = [x.strip() for x in f if x.strip()]

    print(f"总计 {len(urls)} 条，开始多线程下载…")

    # 线程数自行调节，8～32 都可
    with ThreadPoolExecutor(max_workers=16) as exe:
        futures = [exe.submit(download_one, u) for u in urls]

        for fut in as_completed(futures):
            print(fut.result())


if __name__ == "__main__":
    main()
