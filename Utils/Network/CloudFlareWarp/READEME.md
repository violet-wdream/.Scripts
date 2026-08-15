# execute
chmod +x setup-warp.sh
./setup-warp.sh

# open
sudo wg-quick up wgcf
# close
sudo wg-quick down wgcf


# check status_code 200
curl -L --interface wgcf -o /dev/null -s -w "%{http_code}" https://my.telegram.org
# check html
curl -L --interface wgcf https://my.telegram.org

# git
git add .; git commit -m "add new warp"; git push;