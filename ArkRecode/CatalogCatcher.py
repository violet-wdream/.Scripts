import re
import json
import requests
import os
from typing import Tuple, Optional
from urllib3.exceptions import InsecureRequestWarning
import urllib3

urllib3.disable_warnings(InsecureRequestWarning)

from datetime import datetime

def append_timestamp(catalog_name: str) -> str:
    # catalog_name 例如 "catalog_107966.json"
    base = catalog_name.rsplit(".", 1)[0]         # 去掉 .json -> catalog_107966
    date_str = datetime.now().strftime("%Y.%m.%d")  # 2025.12.04
    return f"{base}-{date_str}.json"

# 下载文件
def download_file(url: str, save_path: str) -> bool:
    headers = {
        'User-Agent': "UnityPlayer/2022.3.28f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "X-Unity-Version": "2022.3.28f1"
    }
    try:
        resp = requests.get(url, headers=headers, stream=True, timeout=30, verify=False)
        resp.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print("下载完成:", save_path)
        return True
    except Exception as e:
        print("下载失败:", e)
        return False


class XingYunJiHua:
    @staticmethod
    def get_path_domain_sync(url: str) -> Optional[Tuple[str, str]]:
        host_match = re.search(r".*://([^/]*).*", url)
        host = host_match.group(1) if host_match else ""

        headers = {
            'Host': host,
            'User-Agent': "UnityPlayer/2022.3.28f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
            "X-Unity-Version": "2022.3.28f1",
            "Content-Type": "application/json"
        }

        data = {
            "data": {},
            "route": "GameServerDBSettingHandler.QueryBulletinInfoResult"
        }

        try:
            resp = requests.put(url, json=data, headers=headers, timeout=15, verify=False)
            resp.raise_for_status()
            obj = resp.json()
            info = obj.get("Info", {})

            path_domain = info.get("PathDomain")
            new_catalog_name = info.get("NewCatalogName")

            if path_domain and new_catalog_name:
                return path_domain, new_catalog_name
            print("返回数据不完整:", info)
            return None
        except Exception as e:
            print("请求失败:", e)
            return None


if __name__ == "__main__":
    API_URL = "https://game-arkre-nu.ecchi.xxx//Router/RouterHandler.ashx"

    result = XingYunJiHua.get_path_domain_sync(API_URL)
    if not result:
        print("获取 Catalog 失败")
        exit()

    path_domain, new_catalog_name = result
    catalog_url = f"{path_domain}/Android/{new_catalog_name}.json"
    filename = f"{new_catalog_name}.json"
    save_path = os.path.join(os.getcwd(), filename)

    print("Catalog URL:", catalog_url)
    download_file(catalog_url, save_path)

    new_filename = append_timestamp(filename)
    new_path = os.path.join(os.getcwd(), new_filename)
    os.rename(save_path, new_path)

