# -*- coding: utf8 -*-
import sys
import json
import time
import urllib3
import requests
import argparse
import xmltodict
import grequests
try:
    from urllib.parse import urlparse
except:
    # For PYTHON2
    from urlparse import urlparse
    reload(sys)
    sys.setdefaultencoding("utf-8")


class Colors():
    def __init__(self):
        self.RED = "\033[31m"
        self.GREEN = "\033[32m"
        self.YELLOW = "\033[33m"
        self.BLUE = "\033[34m"
        self.ENDC = "\033[0m"

    def normal(self, msg):
        print(msg)

    def green(self, msg):
        print("%s%s%s" % (self.GREEN, msg, self.ENDC))

    def yellow(self, msg):
        print("%s%s%s" % (self.YELLOW, msg, self.ENDC))

    def red(self, msg):
        print("%s%s%s" % (self.RED, msg, self.ENDC))

    def blue(self, msg):
        print("%s%s%s" % (self.BLUE, msg, self.ENDC))


class preCache():
    """
    sitemap: 网站地图sitemap文件的url路径，比如 https://yourdomain.com/sitemmap.xml
    host: 指定真实主机，比如 127.0.0.1 或 127.0.0.1:8080
    cache_header: 指定缓存命中的头部信息，比如 x-cache (大小写均可)
    user_agent: 指定请求时发送到服务器的User Agent标识
    size: 并发请求大小，注意并非越大越好
    timeout: 单个请求的超时时间
    verify: 是否验证SSL证书，选择IP请求方式时必须关闭
    """
    def __init__(self,
                 sitemap="http://loalhost/sitemap.xml",
                 host=None,
                 cache_header=None,
                 user_agent=None,
                 size=20,
                 timeout=10,
                 verify=False):
        self.report = Colors()
        self.scheme = urlparse(sitemap).scheme
        self.domain = urlparse(sitemap).netloc
        if not self.scheme or not self.domain:
            self.check_fault = True
        self.host = host
        self.size = size
        self.verify = verify
        self.timeout = timeout
        self.start_time = time.time()
        self.session = requests.Session()
        self.cache_header = cache_header
        self.headers = {}
        self.baseurl = "%s://%s" % (self.scheme, self.host)
        self.user_agent = user_agent
        if not user_agent:
            self.user_agent = "Pre-cache/python-requests/%s" % requests.__version__
        self.headers["user-agent"] = self.user_agent
        self.sitemap_url = sitemap
        if not self.verify:
            urllib3.disable_warnings()
        self.headers["Host"] = self.domain

    def exception_handler(self, request, exception):
        print("请求异常：%s,%s" % (str(request.url), exception))

    def get_urls(self):
        sitemap = self.session.get(self.sitemap_url,
                                   headers=self.headers,
                                   timeout=self.timeout,
                                   verify=self.verify).text
        urls = []
        for u in xmltodict.parse(sitemap)["urlset"]["url"]:
            url = u["loc"]
            scheme = urlparse(url).scheme
            domain = urlparse(url).netloc
            if self.host:
                url = url.replace("%s://%s" % (scheme, domain),
                                  "%s://%s" % (self.scheme, self.host))
            else:
                url = url.replace("%s://%s" % (scheme, domain),
                                  "%s://%s" % (self.scheme, self.domain))
            urls.append(url)
        return urls

    def start(self):
        try:
            self.check_fault
            self.report.red("网站地图Url解析失败：%s，请检查！" % self.sitemap_url)
            return False
        except:
            pass
        self.report.normal("站点地图：%s" % self.sitemap_url)
        if self.host:
            self.report.normal("指定主机：%s" % self.host)
        self.report.normal("并发数量：%s" % self.size)
        self.report.normal("超时时间：%s秒" % self.timeout)
        self.report.normal("缓存标识：%s" % self.cache_header)
        self.report.normal("UA  标识：%s" % self.user_agent)
        self.report.blue("预缓存开始:")
        self.report.normal(
            "---------------------------------------------------------")
        urls = self.get_urls()
        req = (grequests.get(url,
                             headers=self.headers,
                             timeout=self.timeout,
                             session=self.session,
                             verify=self.verify) for url in urls)
        result = grequests.map(req,
                               size=self.size,
                               exception_handler=self.exception_handler)
        count = len(result)
        hit_count = 0
        miss_count = 0
        none_count = 0
        noheader_count = 0
        exception_count = 0
        if self.cache_header:
            for r in result:
                flag = 0
                try:
                    headers = json.loads(json.dumps(dict(r.headers)))
                except Exception as e:
                    exception_count += 1
                    continue

                url = str(r.url)
                if self.host:
                    url = url.replace(self.host, self.domain)

                for header, status in headers.items():
                    if header.upper() == self.cache_header.upper():
                        flag += 1
                        if "HIT" in status.upper():
                            hit_count += 1
                        elif "MISS" in status.upper(
                        ) or "EXPIRED" in status.upper():
                            self.report.green("可预缓存页面：%s 缓存标识头：%s: %s" %
                                              (url, str(header), str(status)))
                            miss_count += 1
                        else:
                            none_count += 1
                            self.report.red("不可缓存页面：%s 缓存标识头：%s: %s" %
                                            (url, str(header), str(status)))
                if flag == 0:
                    self.report.yellow("缓存标识头缺失页面：%s " % url)
                    noheader_count += 1

        self.report.normal(
            "---------------------------------------------------------")
        self.report.blue("预缓存完成，页面总数：% s，耗时% s秒" %
                         (count, int(time.time() - self.start_time)))
        if hit_count > 0:
            self.report.green("已被缓存页面数：%s" % hit_count)
        if miss_count > 0:
            self.report.blue("可预缓存页面数：%s" % miss_count)
        if none_count > 0:
            self.report.red("不可缓存页面数：%s" % none_count)
        if exception_count > 0:
            self.report.red("请求异常页面数：%s" % exception_count)
        if noheader_count > 0:
            self.report.yellow("缓存标识头缺失页面数：%s" % noheader_count)
        if hit_count + miss_count == 0:
            if self.cache_header:
                self.report.yellow("指定的缓存标识头 %s 可能不对，未能找到这个头信息." %
                                   self.cache_header)
            else:
                self.report.normal(
                    "Ps：如果指定了缓存命中的头信息，将会显示更多统计信息，比如加上：--cacheheader=x-cache")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="网站预缓存脚本，支持使用CDN或本地有静态缓存的网站.")
    parser.add_argument("-s",
                        "--sitemap",
                        type=str,
                        required=True,
                        help="网站地图sitemap地址")
    parser.add_argument("-S",
                        "--size",
                        type=int,
                        default=20,
                        help="并发请求数量,默认20")
    parser.add_argument("-t",
                        "--timeout",
                        type=int,
                        default=10,
                        help="单个请求的超时时间,默认10s")
    parser.add_argument("-H",
                        "--host",
                        type=str,
                        default=None,
                        help="指定真实主机，比如 127.0.0.1:8080")
    parser.add_argument("-c",
                        "--cacheheader",
                        type=str,
                        default=None,
                        help="缓存标识，比如: x-cache")
    parser.add_argument("-u",
                        "--useragent",
                        type=str,
                        default=None,
                        help="指定UA标识，默认 Pre-cache/python-requests/__version__")
    parser.add_argument("-v",
                        "--verify",
                        type=bool,
                        default=False,
                        help="是否校验SSL，默认不校验")
    args = parser.parse_args()
    pre = preCache(sitemap=args.sitemap,
                   host=args.host,
                   size=args.size,
                   timeout=args.timeout,
                   cache_header=args.cacheheader,
                   user_agent=args.useragent,
                   verify=args.verify)
    pre.start()
