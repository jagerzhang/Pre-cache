# Pre-cache
网站预缓存脚本，全量拉去sitemap里面的网址来实现预缓存，支持使用CDN或本地有静态缓存的网站。

# 使用说明：
```
git clone https://github.com/jagerzhang/Pre-cache.git
cd Pre-cache
```
### 打印帮助信息：
```
python pre_cache.py --help

usage: pre_cache.py [-h] -u URL [-s SIZE] [-t TIMEOUT] [-H HOST] [-S SITEMAP]
                    [-c CACHEHEADER] [-U USERAGENT] [-v VERIFY]

网站预缓存脚本，全量拉去sitemap里面的网址来实现预缓存，支持使用CDN或本地有静态缓存的网站。

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     网站入口地址，一般为首页地址
  -s SIZE, --size SIZE  并发请求数量,默认50
  -t TIMEOUT, --timeout TIMEOUT
                        单个请求的超时时间,默认10s
  -H HOST, --host HOST  指定Host头部
  -S SITEMAP, --sitemap SITEMAP
                        sitemap的url路径，默认sitemap.xml
  -c CACHEHEADER, --cacheheader CACHEHEADER
                        缓存标识，比如: x-cache
  -U USERAGENT, --useragent USERAGENT
                        指定UA标识，默认Pre Cache Tools
  -v VERIFY, --verify VERIFY
                        是否校验SSL，默认不校验
                                              
```

### 快速使用：
```
python pre_cache.py --url=https://zhang.ge --cacheheader=cf-cache-status
```

### 指定IP缓存：
```
# 可以指定IP+Host域名可以绕过CDN，直接请求源站，实现源站本地缓存
python pre_cache.py --url=https://127.0.0.1 --host=zhang.ge --cacheheader=cf-cache-status
```

### 脚本引用
```
from pre_cache import preCache()
pre = preCache(baseurl="https://zhang.ge",
                   host=None,
                   size=10,
                   timeout=10,
                   cache_header="cf-cache-status",
                   user_agent="Pre-Cache-Tools",
                   verify=False)
pre.start()                 
```
