# Pre-cache
网站预缓存脚本，全量拉取sitemap里面的网址来实现预缓存，支持使用CDN或本地有静态缓存的网站。

# 使用说明：
## 基于Docker运行(推荐)
```
# 不依赖本地环境
docker run --rm --net=host -ti jagerzhang/pre-cache:latest \
    --sitemap=https://zhang.ge/sitemap.xml \
    --cacheheader=cf-cache-status
```

## 直接运行脚本
### 环境初始化：
```
git clone https://github.com/jagerzhang/Pre-cache.git
cd Pre-cache
yum install -y python-pip
pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```
### 打印帮助信息：
```
python pre_cache.py --help

usage: pre_cache.py [-h] -s SITEMAP [-S SIZE] [-t TIMEOUT] [-H HOST]
                    [-c CACHEHEADER] [-U USERAGENT] [-v VERIFY]

网站预缓存脚本，支持使用CDN或本地有静态缓存的网站.

optional arguments:
  -h, --help            show this help message and exit
  -s SITEMAP, --sitemap SITEMAP
                        网站地图sitemap地址
  -S SIZE, --size SIZE  并发请求数量,默认20
  -t TIMEOUT, --timeout TIMEOUT
                        单个请求的超时时间,默认10s
  -H HOST, --host HOST  指定真实主机，比如 127.0.0.1:8080
  -c CACHEHEADER, --cacheheader CACHEHEADER
                        缓存标识，比如: x-cache
  -U USERAGENT, --useragent USERAGENT
                        指定UA标识，默认 Pre-cache/python-
                        requests/__version__
  -v VERIFY, --verify VERIFY
                        是否校验SSL，默认不校验                                           
```

### 快速使用：
```
python pre_cache.py \
   --sitemap=https://zhang.ge/sitemap.xml \
   --cacheheader=cf-cache-status
```

### 指定真实主机：
```
# 可以指定IP+Host域名可以绕过CDN，直接请求源站，实现源站本地缓存
python pre_cache.py \
   --sitemap=https://zhang.ge/sitemap.xml \
   --host=127.0.0.1:8443 \
   --cacheheader=x-cache-redis
```
### 指定UA标识：
```
# 可以指定UA标识，伪装浏览器或其他客户端请求，避免被CDN拦截
python pre_cache.py \
   --sitemap=https://zhang.ge/sitemap.xml \
   --cacheheader=cf-cache-status \
   --useragent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
```
### 对象引用：
```
from pre_cache import preCache
pre = preCache(sitemap="https://zhang.ge/sitemap.xml",
                   host=None,
                   size=10,
                   timeout=10,
                   cache_header="cf-cache-status",
                   user_agent="Pre-cache/python-requests/2.22.0",
                   verify=False)
pre.start()                 
```
