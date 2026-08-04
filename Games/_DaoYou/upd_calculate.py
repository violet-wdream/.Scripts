from pathlib import Path
from remotezip import RemoteZip
from concurrent.futures import ThreadPoolExecutor, as_completed

from Utils.DownLoad.UrlsDownLoader import download_one # my download function

mlist_file = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\DaoYou\mlist.txt")
download_path = Path(r"D:\Tools\UsefulTools\MuMu\Shared\Download\DaoYou\download")
base_url = "https://resdy.jzyx.com/v8/pak/"


def remote_zip_parser(url: str) -> int:
    try:
        with RemoteZip(url) as z:
            return len(z.namelist())
    except Exception as e:
        print(e)
        return 0

# 按行解析 mlist_file
# 匹配 upd_1.pak	8146	234022 类似行目
# upd_{n}.pak    {crc32}	 {size}
# print the sum of the sizes of all upd_{n}.pak files in mlist_file
def calculate_size():
    urls = []
    total_size = 0

    with open(mlist_file, encoding="utf8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) != 3:
                continue

            filename, _crc32, size = parts

            if filename.startswith("upd_") and filename.endswith(".pak"):
                urls.append(base_url + filename)
                total_size += int(size)

    print(f"总大小: {total_size / 1024 / 1024:.2f} MB")

    # with ThreadPoolExecutor(max_workers=16) as pool:
    #     futures = [pool.submit(remote_zip_parser, url) for url in urls]
    #
    #     for future in as_completed(futures):
    #         total_files += future.result()

    # download all urls
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(download_one, url, download_path) for url in urls]

        for future in as_completed(futures):
            print(future.result())





if __name__ == "__main__":
    calculate_size()

    # 先用一个基础序列号1050来测探最大序列号
    # ...
    # 这里的得到是1054
    # 对于任意一个pak, 其中的文件名是32位的MD5
    # url = "https://resdy.jzyx.com/v8/pak/upd_2.pak"
    # with RemoteZip(url) as z:
    #     print(len(z.namelist()))
    #     print(z.namelist())
    # 对于所有pak, 收集所有文件名, 构成一个MD5表

