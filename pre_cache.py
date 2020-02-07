# -*- coding: utf8 -*-
import sys
import json
import time
import urllib3
import requests
import argparse
import xmltodict
import grequests
reload(sys)
sys.setdefaultencoding("utf-8")
try:
    from urllib.parse import urlparse
except:
    from urlparse import urlparse


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
    baseurl: 入口网址，一般为首页,不带最后的斜杠,比如 http://yourdomain.com
    host: 指定Host访问，支持指定IP请求,比如 yourdomain.com
    sitemap: 指定sitemap文件的path路径，不加开头的斜杠，比如 sitemmap.xml 或 blog/sitemap.xml
    cache_header: 指定缓存命中的头部信息，比如 x-cache (大小写均可)
    user_agent: 指定请求时发送到服务器的User Agent标识
    size: 并发请求大小，注意并非越大越好
    timeout: 单个请求的超时时间
    verify: 是否验证SSL证书，选择IP请求方式时必须关闭
    """
    def __init__(self,
                 baseurl="http://loalhost",
                 host=None,
                 sitemap="sitemap.xml",
                 cache_header=None,
                 user_agent="Pre Cache Tools",
                 size=20,
                 timeout=5,
                 verify=False):
        self.size = size
        self.verify = verify
        self.timeout = timeout
        self.baseurl = baseurl
        self.start_time = time.time()
        self.session = requests.Session()
        self.cache_header = cache_header
        self.server = urlparse(baseurl).netloc
        self.user_agent = user_agent
        self.headers = {"user-agent": user_agent}
        self.sitemap_url = "%s/%s" % (self.baseurl, sitemap)
        if not self.verify:
            urllib3.disable_warnings()
        if host:
            self.host = host
        else:
            self.host = self.server

        self.headers["Host"] = self.host
        self.report = Colors()

    def exception_handler(self, request, exception):
        print("请求异常：%s,%s" % (str(request.url), exception))

    def get_urls(self):
        sitemap = self.session.get(self.sitemap_url,
                                   headers=self.headers,
                                   timeout=self.timeout,
                                   verify=self.verify).text
        urls = []
        for url in xmltodict.parse(sitemap)["urlset"]["url"]:
            if self.host:
                urls.append(url["loc"].replace(
                    "%s://%s" %
                    (urlparse(url["loc"]).scheme, urlparse(url["loc"]).netloc),
                    self.baseurl))
            else:
                urls.append(url["loc"])
        return urls

    def start(self):
        self.report.normal("网站首页：%s" % self.baseurl)
        self.report.normal("站点地图：%s" % self.sitemap_url)
        self.report.normal("Host头部：%s" % self.host)
        self.report.normal("超时时间：%s秒" % self.timeout)
        self.report.normal("缓存标识：%s" % self.cache_header)
        self.report.normal("并发数量：%s" % self.size)
        self.report.normal("UA 标识：%s" % self.user_agent)
        self.report.normal("预缓存开始:\n---------------------------------------")
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
        if self.cache_header:
            hit_count = 0
            miss_count = 0
            none_count = 0
            noheader_count = 0
            exception_count = 0
            for r in result:
                flag = 0
                try:
                    headers = json.loads(json.dumps(dict(r.headers)))
                except Exception as e:
                    exception_count += 1
                    continue

                for header, status in headers.items():
                    if header.upper() == self.cache_header.upper():
                        flag += 1
                        if status.upper() == "HIT":
                            hit_count += 1
                        elif status.upper() == "MISS" or status.upper(
                        ) == "EXPIRED":
                            self.report.green(
                                "可预缓存页面：%s " %
                                str(r.url).replace(self.server, self.host))
                            miss_count += 1
                        else:
                            none_count += 1
                            self.report.red(
                                "不可缓存页面：%s，缓存状态：%s " % (str(r.url).replace(
                                    self.server, self.host), str(status)))
                if flag == 0:
                    self.report.yellow(
                        "未找到缓存标识头部：%s " %
                        str(r.url).replace(self.server, self.host))
                    noheader_count += 1

        self.report.normal(
            "---------------------------------------\n预缓存完成，页面总数：% s，耗时% s秒" %
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
            self.report.yellow("缓存头部标识缺失页面数：%s" % noheader_count)
        if hit_count + miss_count == 0:
            if self.cache_header:
                self.report.yellow("指定的缓存命中头部 %s 可能不对，未能找到这个头部信息." %
                                   self.cache_header)
            else:
                self.report.normal(
                    "Ps：如果指定了缓存命中的头部信息，将会显示更多统计信息，比如加上：--cacheheader=x-cache")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="网站预缓存脚本，支持使用CDN或本地有静态缓存的网站.")
    parser.add_argument("-u",
                        "--url",
                        type=str,
                        required=True,
                        help="网站入口地址，一般为首页地址")
    parser.add_argument("-s",
                        "--size",
                        type=int,
                        default=50,
                        help="并发请求数量,默认50")
    parser.add_argument("-t",
                        "--timeout",
                        type=int,
                        default=10,
                        help="单个请求的超时时间,默认10s")
    parser.add_argument("-H",
                        "--host",
                        type=str,
                        default=None,
                        help="指定Host头部")
    parser.add_argument("-S",
                        "--sitemap",
                        type=str,
                        default="sitemap.xml",
                        help="sitemap的url路径，默认sitemap.xml")
    parser.add_argument("-c",
                        "--cacheheader",
                        type=str,
                        default=None,
                        help="缓存标识，比如: x-cache")
    parser.add_argument("-U",
                        "--useragent",
                        type=str,
                        default="Pre Cache Tools",
                        help="指定UA标识，默认Pre Cache Tools ")
    parser.add_argument("-v",
                        "--verify",
                        type=bool,
                        default=False,
                        help="是否校验SSL，默认不校验")
    args = parser.parse_args()
    pre = preCache(baseurl=args.url,
                   host=args.host,
                   size=args.size,
                   timeout=args.timeout,
                   sitemap=args.sitemap,
                   cache_header=args.cacheheader,
                   user_agent=args.useragent,
                   verify=args.verify)
    pre.start()
