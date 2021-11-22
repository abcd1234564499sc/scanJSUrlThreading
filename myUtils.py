#!/usr/bin/env python
# coding=utf-8
import datetime
import re
import urllib.parse

import requests
# 访问URL,type表示请求类型，0为GET，1为POST
# 返回值类型如下：
# {
# "url":传入URL,
# "resultStr":访问结果字符串,
# "checkFlag":标志是否访问成功的布尔类型变量,
# "title":访问成功时的页面标题,
# "pageContent":访问成功时的页面源码，
# "status":访问的响应码
# }
from bs4 import BeautifulSoup


def requestsUrl(url, cookie={}, data={}, type=0, reqTimeout=5, readTimeout=5):
    resDic = {}
    url = url.strip()
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
    }

    resultStr = ""
    checkedFlag = False
    status = ""
    title = ""
    reContent = ""
    timeout = (reqTimeout, readTimeout)

    try:
        if type == 0:
            response = requests.get(url, headers=header, verify=False, cookies=cookie, timeout=timeout)
        else:
            response = requests.post(url, headers=header, verify=False, cookies=cookie, data=data,
                                     timeout=timeout)
        status = response.status_code
        if status == requests.codes.ok:
            # 获得页面编码
            pageEncoding = response.apparent_encoding
            # 设置页面编码
            response.encoding = pageEncoding
            # 获得页面内容
            reContent = response.text
            soup = BeautifulSoup(reContent, "lxml")
            title = "成功访问，但无法获得标题" if not soup.title else soup.title.string
            resultStr = "验证成功，标题为：{0}".format(title)
            checkedFlag = True
        else:
            resultStr = "验证失败，状态码为{0}".format(status)
            checkedFlag = False
    except Exception as e:
        resultStr = str(e)
        checkedFlag = False

    # 构建返回结果
    resDic["url"] = url
    resDic["resultStr"] = resultStr
    resDic["checkFlag"] = checkedFlag
    resDic["title"] = title
    resDic["status"] = status
    resDic["pageContent"] = reContent
    return resDic


# 判断该字符串是否是IP，返回一个布尔值
def ifIp(matchStr):
    reFlag = True
    ipReg = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    if re.match(ipReg, matchStr):
        reFlag = True
    else:
        reFlag = False
    return reFlag


# 从URL中提取协议+域名部分
def getUrlDomain(url):
    urlObj = urllib.parse.urlsplit(url)
    domain = urllib.parse.urlunsplit(tuple(list(urlObj[:2]) + [""] * 3))
    return domain


# 判断两个域名是否属于同一主域名，如果两者都是IP则比较是否完全相同，
# 返回一个布尔值,属于返回True,否则返回False
def ifSameMainDomain(domain1, domain2):
    reFlag = True
    domainArr = [domain1,domain2]
    if ifIp(domain1) != ifIp(domain2):
        # 判断是否是IP和域名比较
        reFlag = False
    elif ifIp(domain1) and ifIp(domain2):
        # 两个参数都是IP
        reFlag = (domain1 == domain2)
    else:
        # 两个参数都是域名
        # 去除端口号
        for index,nowDomain in enumerate(domainArr):
            tempPort = nowDomain.split(":")[-1]
            if tempPort.isdigit():
                # 去除端口号
                nowDomain = ":".join(nowDomain.split(":")[:-1])
                domainArr[index] = nowDomain
            else:
                pass

        # 判断主域名是否相同
        tempMainDomain = ".".join(domainArr[0].split(".")[-2:])
        for nowDomain in domainArr:
            if ".".join(nowDomain.split(".")[-2:]) != tempMainDomain:
                reFlag = False
    return reFlag


# 从URL中提取文件后缀名
def getUrlFileSuffix(url):
    reSuffix = ""
    urlObj = urllib.parse.urlparse(url)
    reSuffix = urlObj[2].split("/")[-1].split(".")[-1]
    return reSuffix

# 获得精确到秒的当前时间
def getNowSeconed():
    formatStr = "%Y-%m-%d %H:%M:%S"
    nowDate = datetime.datetime.now()
    nowDateStr = nowDate.strftime(formatStr)
    return nowDateStr