# -*- coding: utf8 -*-
import sys
import json
import time
import re
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

    def debug(self, msg, debug):
        if debug:
            print(msg)

    def green(self, msg):
        print("%s%s%s" % (self.GREEN, msg, self.ENDC))

    def yellow(self, msg):
        print("%s%s%s" % (self.YELLOW, msg, self.ENDC))

    def red(self, msg):
        print("%s%s%s" % (self.RED, msg, self.ENDC))

    def blue(self, msg):
        print("%s%s%s" % (self.BLUE, msg, self.ENDC))


class PreCache():
    """网站预缓存工具
    """
    def __init__(self,
                 sitemap="http://loalhost/sitemap.xml",
                 host=None,
                 cache_header=None,
                 user_agent=None,
                 size=20,
                 timeout=10,
                 verify=False,
                 debug=False):
        """class 初始化

        Args:
            sitemap (str, optional): 网站地图sitemap文件的url路径，比如 https://yourdomain.com/sitemmap.xml. Defaults to "http://loalhost/sitemap.xml".
            host ([type], optional): 指定真实主机，比如 127.0.0.1 或 127.0.0.1:8080. Defaults to None.
            cache_header ([type], optional): 指定缓存命中的头部信息，比如 x-cache (大小写均可). Defaults to None.
            user_agent ([type], optional): 指定请求时发送到服务器的User Agent标识. Defaults to None.
            size (int, optional): 并发请求大小，注意并非越大越好. Defaults to 20.
            timeout (int, optional): 单个请求的超时时间. Defaults to 10.
            verify (bool, optional): 是否验证SSL证书，选择IP请求方式时必须关闭. Defaults to False.
        """

        self.report = Colors()
        self.scheme = urlparse(sitemap).scheme
        self.domain = urlparse(sitemap).netloc
        if not self.scheme or not self.domain:
            self.report.red("网站地图Url解析失败：%s，请检查！" % self.sitemap_url)
            exit(1)

        self.host = host
        self.size = size
        self.verify = verify
        self.timeout = timeout
        self.start_time = time.time()
        self.session = requests.Session()
        self.cache_header = cache_header
        self.sitemap_url = sitemap
        self.debug = debug
        if not self.verify:
            urllib3.disable_warnings()

        self.user_agent = user_agent
        if not user_agent:
            self.user_agent = "Pre-cache/python-requests/%s" % requests.__version__

        headers = {}
        headers["user-agent"] = self.user_agent
        headers["Host"] = self.domain
        self.session.headers.update(headers)

    def _exception_handler(self, request, exception):
        """grequests异常处理
        """
        print("请求异常：%s,%s" % (str(request.url), exception))

    def _get_urls(self):
        """通过解析XML来提取网址
        """
        sitemap = self.session.get(self.sitemap_url,
                                   timeout=self.timeout,
                                   verify=self.verify).text

        urls = []
        for u in xmltodict.parse(sitemap)["urlset"]["url"]:
            url = u["loc"]
            # 若指定了域名则替换
            if self.host:
                scheme = urlparse(url).scheme
                domain = urlparse(url).netloc
                src_base = "{0}://{1}".format(scheme, domain)
                new_base = "{0}://{1}".format(self.scheme, self.host)
                url = url.replace(src_base, new_base)

            self.report.debug("[DEBUG]成功提取网址：{0}".format(url), self.debug)

            urls.append(url)

        return urls

    def _get_urls_re(self):
        """正则解析提取网址
        """
        self.report.normal("拉取站点地图文件：{0}".format(self.sitemap_url))
        sitemap = self.session.get(self.sitemap_url,
                                   timeout=self.timeout,
                                   verify=self.verify).text

        pattern = r"<loc>https?://[^<]+</loc>"
        src_urls = re.findall(pattern, sitemap)

        urls = []
        for url in src_urls:
            url_re = re.search(r"https?://[^<]+", url)
            if not url_re:
                self.report.debug("[DEBUG]提取网址失败：{0}".format(url), self.debug)

                continue

            url = url_re.group()

            # 若指定了域名则替换
            if self.host:
                scheme = urlparse(url).scheme
                domain = urlparse(url).netloc
                src_base = "{0}://{1}".format(scheme, domain)
                new_base = "{0}://{1}".format(self.scheme, self.host)
                url = url.replace(src_base, new_base)

            self.report.debug("[DEBUG]成功提取网址：{0}".format(url), self.debug)

            urls.append(url)

        return urls

    def _stats_result(self, result):
        """缓存结果解析
        """
        self.hit_count = 0
        self.miss_count = 0
        self.none_count = 0
        self.noheader_count = 0
        self.exception_count = 0

        if not self.cache_header:
            return

        for r in result:
            flag = 0
            try:
                headers = json.loads(json.dumps(dict(r.headers)))

            except:
                self.exception_count += 1
                continue

            url = str(r.url)
            if self.host:
                url = url.replace(self.host, self.domain)

            for header, status in headers.items():
                if header.upper() == self.cache_header.upper():
                    flag += 1
                    if "HIT" in status.upper():
                        self.hit_count += 1

                    elif "MISS" in status.upper() or "EXPIRED" in status.upper(
                    ):
                        self.miss_count += 1
                        self.report.green("可预缓存页面：{0} 缓存标识头：{1}: {2}".format(
                            url, header, status))

                    else:
                        self.none_count += 1
                        self.report.red("不可缓存页面：{0} 缓存标识头：{1}: {2}".format(
                            url, header, status))

            if flag == 0:
                self.report.yellow("缓存标识头缺失页面：%s " % url)
                self.noheader_count += 1

    def start(self):
        """启动预缓存
        """
        self.report.normal("站点地图：{0}".format(self.sitemap_url))

        if self.host:
            self.report.normal("指定主机：{0}".format(self.host))

        self.report.normal("并发数量：{0}".format(self.size))
        self.report.normal("超时时间：{0}秒".format(self.timeout))
        self.report.normal("缓存标识：{0}".format(self.cache_header))
        self.report.normal("UA  标识：{0}".format(self.user_agent))
        self.report.blue("预缓存开始:")
        self.report.normal(
            "---------------------------------------------------------")

        urls = []

        try:
            urls = self._get_urls()

        except Exception as error:
            self.report.yellow("通过XML解析器提取网址失败: {0}，尝试改为正则提取...".format(error))
            urls = self._get_urls_re()

        finally:
            if len(urls) == 0:
                self.report.red("提取网址失败，请检查sitemap文件是否符合规范")
                exit(1)

            self.report.green("提取网址成功，共 {0} 条记录".format(len(urls)))

        req = (grequests.get(url,
                             timeout=self.timeout,
                             session=self.session,
                             verify=self.verify) for url in urls)

        result = grequests.map(req,
                               size=self.size,
                               exception_handler=self._exception_handler)

        count = len(result)
        self._stats_result(result)

        self.report.normal(
            "---------------------------------------------------------")
        self.report.blue("预缓存完成，页面总数：% s，耗时% s秒" %
                         (count, int(time.time() - self.start_time)))

        if self.hit_count > 0:
            self.report.green("已被缓存页面数：{0}".format(self.hit_count))

        if self.miss_count > 0:
            self.report.blue("可预缓存页面数：{0}".format(self.miss_count))

        if self.none_count > 0:
            self.report.red("不可缓存页面数：{0}".format(self.none_count))

        if self.exception_count > 0:
            self.report.red("请求异常页面数：{0}".format(self.exception_count))

        if self.noheader_count > 0:
            self.report.yellow("缓存标识头缺失页面数：{0}".format(self.noheader_count))

        if self.hit_count + self.miss_count == 0:
            if self.cache_header:
                self.report.yellow("指定的缓存标识头 {0} 可能不对，未能找到这个头信息.".format(
                    self.cache_header))

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
                        action="store_true",
                        help="是否校验SSL，默认不校验")
    parser.add_argument("-d",
                        "--debug",
                        action="store_true",
                        help="显示Debug信息, 默认关闭")
    args = parser.parse_args()
    pre = PreCache(sitemap=args.sitemap,
                   host=args.host,
                   size=args.size,
                   timeout=args.timeout,
                   cache_header=args.cacheheader,
                   user_agent=args.useragent,
                   verify=args.verify,
                   debug=args.debug)
    pre.start()
