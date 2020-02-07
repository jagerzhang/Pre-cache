FROM centos:7
WORKDIR /opt/
RUN rm -rf /etc/yum.repos.d/* \
        && curl -o /etc/yum.repos.d/CentOS-Base.repo http://mirrors.163.com/.help/CentOS7-Base-163.repo \
        && curl -o /etc/yum.repos.d/CentOS-epel.repo http://mirrors.aliyun.com/repo/epel-7.repo \
        && rpm --import http://mirrors.163.com/centos/RPM-GPG-KEY-CentOS-7 \
        && yum clean all  \
        && yum makecache \
        && yum install -y python-pip
RUN pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
COPY . .
RUN pip install -r /opt/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ 
CMD ["/usr/bin/python","/opt/pre_cache.py"]
