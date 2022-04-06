#!/usr/bin/env python
# coding=utf-8
import json
import re
import urllib

from PyQt5.QtCore import QThread, pyqtSignal
from bs4 import BeautifulSoup

import myUtils


class UrlScrapyThreading(QThread):
    signal_end = pyqtSignal(str)

    def __init__(self, scrawlUrl, sensiveKeyList=[], startUrl="", parent=None, extraUrlArr=[], nowCookie="",
                 proxies=None):
        super(UrlScrapyThreading, self).__init__(parent)
        self.scrawlUrl = scrawlUrl
        self.sensiveKeyList = sensiveKeyList
        self.startUrl = startUrl
        self.extraUrlArr = extraUrlArr
        self.nowCookie = nowCookie
        self.proxies = proxies

    def run(self):
        reDicStr = self.scrapyProcess(self.scrawlUrl)
        self.signal_end.emit(reDicStr)

    def getScrawlUrl(self):
        return self.scrawlUrl

    # 访问并分析URL，生成多个能正常访问的结果字典并写入结果队列
    # 字典结构为：
    # {
    # "url":"访问地址",
    # "status":"响应码",
    # "title":"标题",
    # "contentLength":"包长",
    # "linkList":"当前页面的URL列表（已去重）",
    # "sensiveInfoList":"当前页面存在的敏感字典列表信息，字典格式为：{"url":当前URL,"key":匹配关键词,"seneiveStr":敏感信息}"
    # }
    def scrapyProcess(self, url):
        reDicStr = ""

        # 获得后缀
        urlSuffix = myUtils.getUrlFileSuffix(url)

        # 请求这个URL
        try:
            tempDic = myUtils.requestsUrl(url, cookie={} if self.nowCookie == "" else self.nowCookie,
                                          proxies=self.proxies)
        except Exception as ex:
            raise

        if tempDic["checkFlag"]:
            # 访问成功
            status = tempDic["status"]
            title = tempDic["title"]
            content = tempDic["pageContent"]
            reLinkList = []
            if urlSuffix == "js":
                # 是js文件，使用js文件分析方法分析
                tempLinkList = self.analysisJSPage(self.scrawlUrl, url, content, extraUrlArr=self.extraUrlArr)
                for tempLink in tempLinkList:
                    reLinkList.append((tempLink, self.startUrl))
            else:  # if urlSuffix == "js":
                # 不是js文件，按HTML文件分析方法分析
                reHtmlDic = self.analysisHtmlPage(pageUrl=tempDic["url"], pageContent=content)
                reAList = reHtmlDic["a"]
                reJsList = reHtmlDic["js"]
                tempLinkList = reAList + reJsList
                for tempLink in tempLinkList:
                    reLinkList.append((tempLink, self.startUrl))

            # 分析敏感信息
            sensiveInfoList = self.analysisSensiveInfo(url, content)

            # 构建返回结果
            reDic = {}
            reDic["url"] = url
            reDic["status"] = status
            reDic["title"] = title
            reDic["contentLength"] = len(content)
            reDic["linkList"] = reLinkList
            reDic["sensiveInfoList"] = sensiveInfoList
            reDic["urlType"] = urlSuffix if urlSuffix != "" else "html"
            reDicStr = json.dumps(reDic)
        else:  # if reDic["checkFlag"]
            pass
        return reDicStr

    # 分析一个Html页面，返回其中的链接以及引用的js链接，
    # 返回一个字典，字典结构为：{"a":[a标签的链接数组],"js":[js链接数组]}
    def analysisHtmlPage(self, pageUrl="", pageContent=""):
        reDic = {}
        aLinkList = []
        jsLinkList = []

        # 获得当前URL的域名值
        nowDomain = myUtils.getUrlDomain(pageUrl)

        # 解析当前页面
        soup = BeautifulSoup(pageContent, "lxml")
        # 获取所有a标签
        aList = soup.find_all("a")
        for aItem in aList:
            if "href" in aItem.attrs.keys():
                # 获取链接
                nowHref = aItem.attrs["href"]
                nowHref = urllib.parse.urljoin(pageUrl, nowHref)
                # 判断是否属于爬取域名的子域名
                if myUtils.ifSameMainDomain(nowDomain, myUtils.getUrlDomain(nowHref)):
                    aLinkList.append(nowHref)
        # 获取所有js链接
        scriptList = soup.find_all("script")
        for scriptItem in scriptList:
            if "src" in scriptItem.attrs.keys():
                # 获取链接
                nowSrc = scriptItem.attrs["src"]
                nowSrc = urllib.parse.urljoin(pageUrl, nowSrc)
                # 判断是否是js链接且属于爬取域名的子域名
                if urllib.parse.urlparse(nowSrc)[2].split(".")[-1] == "js" and myUtils.ifSameMainDomain(nowDomain,
                                                                                                        myUtils.getUrlDomain(
                                                                                                            nowSrc)):
                    jsLinkList.append(nowSrc)
        # 结果去重
        aLinkList = list(set(aLinkList))
        jsLinkList = list(set(jsLinkList))

        # 构造返回字典
        reDic["a"] = aLinkList
        reDic["js"] = jsLinkList
        return reDic

    # 分析js文件，传入一个网站域名，当前js文件地址，以及js文件的源码，需要额外拼接的URL列表，返回一个链接列表
    def analysisJSPage(self, nowScrawlUrl="", nowUrl="", pageContent="", extraUrlArr=[]):
        reList = []
        # pattern = re.compile(r'(?:(?:http|https)://|["|\[|\']/).*?["|\]|\']', flags=re.I)
        pattern = re.compile(r'(?:(?:http|https)://|["|\[|\'][a-zA-Z0-9\.]*/).*?["|\]|\']', flags=re.I)
        startPattern = re.compile(r'^["|\'|[]', flags=re.I)
        endPattern = re.compile(r'["|\'|}]$', flags=re.I)
        httpPattern = re.compile(r'(?:http|https)://', flags=re.I)

        nowScrawlDomain = myUtils.getUrlDomain(nowScrawlUrl)
        nowUrlDomain = myUtils.getUrlDomain(nowUrl)
        nowStartDomain = myUtils.getUrlDomain(self.startUrl)
        # 提取所有符合URL格式的字符串
        reResults = pattern.findall(pageContent)
        for link in reResults:
            # 替换开始的引号
            link = startPattern.sub("", link)
            # 替换结束的引号
            link = endPattern.sub("", link)
            # 替换换行符
            link = link.replace("\r\n", "\n").replace("\n", "")
            if httpPattern.match(link):
                # 链接自带协议，是完整的地址
                # 判断是否属于爬取域名的子域名
                if myUtils.ifSameMainDomain(nowScrawlDomain, myUtils.getUrlDomain(link)):
                    reList.append(link)
            else:
                link = urllib.parse.unquote(link, encoding="utf-8", errors=None)
                link = urllib.parse.quote(link, safe='/', encoding="utf-8", errors=None)
                # 与当前输入网站域名结合
                reList.append(urllib.parse.urljoin(nowScrawlDomain, link))
                # 与当前输入网站URL结合
                reList.append(myUtils.joinUrl(myUtils.getUrlWithoutFile(nowScrawlUrl), link))
                # 与开始输入网站域名相结合
                reList.append(urllib.parse.urljoin(nowStartDomain, link))
                # 与当前输入网站URL结合
                reList.append(myUtils.joinUrl(myUtils.getUrlWithoutFile(self.startUrl), link))
                # 与js文件域名结合
                reList.append(urllib.parse.urljoin(nowUrlDomain, link))
                # 与js文件地址结合
                reList.append(myUtils.joinUrl(myUtils.getUrlWithoutFile(nowUrl), link))
                # 与额外传入的URL地址结合
                for nowExtraUrl in extraUrlArr:
                    reList.append(urllib.parse.urljoin(nowExtraUrl, link))
                    reList.append(myUtils.joinUrl(nowExtraUrl, link))

        # 去重
        reList = list(set(reList))
        return reList

    # 分析页面中的敏感信息，返回敏感信息字典的列表，
    # 字典格式为：{"url":当前URL,"key":匹配关键词,"seneiveStr":敏感信息}
    def analysisSensiveInfo(self, pageUrl="", pageContent=""):
        reList = []

        # 定义敏感信息键值列表
        sensiveKeyList = self.sensiveKeyList

        # 替换页面源码的换行符
        pageContent = pageContent.replace("\r\n", "\n")
        # 按行分割源码
        pageContentArr = pageContent.split("\n")
        # 按行分析源码
        for pageLine in pageContentArr:
            for sensiveKey in sensiveKeyList:
                splitArr = pageLine.split(sensiveKey)
                if len(splitArr) >= 2:
                    # 表示存在该关键词，从关键词开始截取当行
                    tempLineStr = sensiveKey + sensiveKey.join(splitArr[1:])
                    if len(tempLineStr) > 50:
                        # 若当前行过长，判断为压缩后的js文件等特殊情况，只截取前50个字符
                        tempLineStr = tempLineStr[:50]
                    else:
                        pass
                    reList.append({"url": pageUrl, "key": sensiveKey, "seneiveStr": tempLineStr})
                else:
                    pass

        return reList
