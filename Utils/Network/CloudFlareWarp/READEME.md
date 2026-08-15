# execute in github-codespace
chmod +x setup-warp.sh
./setup-warp.sh

# check status_code 200
curl -L --interface wgcf -o /dev/null -s -w "%{http_code}" https://my.telegram.org
# check html
curl -L --interface wgcf https://my.telegram.org

# git
git add .; git commit -m "add new warp"; git push;

# open
sudo wg-quick up wgcf
# close
sudo wg-quick down wgcf



# download usque in github-codespace
# 1. 下载适合 Linux 系统的 usque 二进制文件
wget https://github.com/Diniboy1123/usque/releases/download/v4.2.1/usque_4.2.1_linux_amd64.zip

# 2. 解压文件
sudo apt update && sudo apt install unzip -y
unzip usque_4.2.1_linux_amd64.zip

# 3. 将 usque 移动到系统路径，方便后续使用
sudo mv usque /usr/local/bin/


