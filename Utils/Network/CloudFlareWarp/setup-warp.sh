#!/bin/bash
set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# 安装依赖
sudo apt update -qq
sudo apt install -y wireguard-tools curl dnsutils

# 安装 wgcf
if ! command -v wgcf &> /dev/null; then
    curl -fsSL https://github.com/ViRb3/wgcf/releases/download/v2.2.32/wgcf_2.2.32_linux_amd64 -o wgcf
    chmod +x wgcf && sudo mv wgcf /usr/local/bin/
fi

# 注册并生成配置
[ ! -f wgcf-account.toml ] && wgcf register
wgcf generate
sudo mkdir -p /etc/wireguard
sudo cp wgcf-profile.conf /etc/wireguard/wgcf.conf

# 获取 Telegram 的 IP
TG_IPS=$(dig +short my.telegram.org | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | tr '\n' ',' | sed 's/,$//')
[ -z "$TG_IPS" ] && TG_IPS="149.154.167.99"
TG_IPS=$(echo "$TG_IPS" | sed 's/,/\/32,/g' | sed 's/$/\/32/')

# 修改配置：只路由 Telegram IP，删除 DNS
sudo sed -i "s|^AllowedIPs = .*|AllowedIPs = $TG_IPS|" /etc/wireguard/wgcf.conf
sudo sed -i '/^DNS =/d' /etc/wireguard/wgcf.conf

# 启动
sudo wg-quick down wgcf 2>/dev/null || true
sudo wg-quick up wgcf

# 验证
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --interface wgcf https://my.telegram.org 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ 成功！状态码: $HTTP_CODE${NC}"
else
    echo -e "${YELLOW}⚠️ 状态码: $HTTP_CODE，检查网络或 IP 列表${NC}"
fi
