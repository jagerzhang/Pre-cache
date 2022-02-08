FROM python:3.9
LABEL maintainer="Jager<im@zhang.ge>"
LABEL description="网站预缓存脚本，全量拉取sitemap里面的网址来实现预缓存，支持使用CDN或本地有静态缓存的网站。"
WORKDIR /opt/
COPY . .
RUN python -m pip install --upgrade pip \
    && pip install -r /opt/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ \
    && rm -rf ~/.cache/pip/* 
ENTRYPOINT ["python","/opt/pre_cache.py"]
