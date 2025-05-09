#!/usr/bin/env python
# coding=utf-8
import json
import re
import urllib.parse

from PyQt5.QtCore import QThread, pyqtSignal

import myUtils


class UrlScrapyThreading(QThread):
    signal_end = pyqtSignal(str)

    def __init__(self, scrawlUrl, sensiveKeyList=[], startUrl="", parent=None, extraUrlArr=[], nowCookie={},
                 proxies=None, unvisitInterfaceUri=[],userAgent="",nowHeaders={}):
        super(UrlScrapyThreading, self).__init__(parent)
        self.scrawlUrl = scrawlUrl
        self.sensiveKeyList = sensiveKeyList
        self.startUrl = startUrl
        self.extraUrlArr = extraUrlArr
        self.nowCookie = nowCookie
        self.proxies = proxies
        self.unvisitInterfaceUri = unvisitInterfaceUri
        self.userAgent=userAgent
        self.nowHeaders=nowHeaders

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

        # 不处理资源文件
        if urlSuffix in myUtils.getHtmlCrawlerNotSolveResourceFileSuffixList():
            return reDicStr

        # 构建header
        tmpHeader = {
            "User-Agent": self.userAgent
        }

        for tmpKey,tmpVal in self.nowHeaders.items():
            tmpHeader[tmpKey] = tmpVal

        # 请求这个URL
        try:
            tempDic = myUtils.requestsUrl(url, cookie=self.nowCookie,
                                          proxies=self.proxies,header=tmpHeader)
        except Exception as ex:
            raise

        if tempDic["checkFlag"]:
            # 访问成功
            status = tempDic["status"]

            if str(status)[0] == "4":
                return reDicStr

            title = tempDic["title"]
            content = tempDic["pageContent"]
            reLinkList = []
            reOtherDomainList = []
            sensiveInfoList = []
            finalOtherDomainList = []
            if urlSuffix in myUtils.getHtmlCrawlerNotCrawlerFileSuffixList():
                # 二进制文件后缀，不进行爬虫操作，仅记录请求结果
                pass
            else:
                if urlSuffix in myUtils.getHtmlCrawlerScriptFileSuffixList():
                    # 是js文件，使用js文件分析方法分析
                    tempLinkList,tmpOtherDomainList = self.analysisJSPage(self.scrawlUrl, url, content, extraUrlArr=self.extraUrlArr,
                                                       unvisitInterfaceUri=self.unvisitInterfaceUri)
                    for tempLink in tempLinkList:
                        reLinkList.append((tempLink, self.startUrl))

                    reOtherDomainList+=tmpOtherDomainList
                elif urlSuffix in myUtils.getHtmlCrawlerCssFileSuffixList():
                    # 是css文件，使用css文件分析方法分析
                    tempLinkList, tmpOtherDomainList = self.analysisCssPage(self.scrawlUrl, url, content,
                                                                           extraUrlArr=self.extraUrlArr,
                                                                           unvisitInterfaceUri=self.unvisitInterfaceUri)
                    for tempLink in tempLinkList:
                        reLinkList.append((tempLink, self.startUrl))

                    reOtherDomainList += tmpOtherDomainList
                else:
                    # 不是js和css文件，按HTML文件分析方法分析
                    reHtmlDic = self.analysisHtmlPage(pageUrl=tempDic["url"], pageContent=content,
                                                      unvisitInterfaceUri=self.unvisitInterfaceUri)
                    tempLinkList = reHtmlDic["url"]
                    for tempLink in tempLinkList:
                        reLinkList.append((tempLink, self.startUrl))

                    tmpOtherDomainList = reHtmlDic["otherDomains"]

                    reOtherDomainList+=tmpOtherDomainList

                # 分析敏感信息
                sensiveInfoList = self.analysisSensiveInfo(url, content)

                # 返回前去重
                reOtherDomainList = list(set(reOtherDomainList))

                # 将其他域名进行处理
                finalOtherDomainList = []
                for tmpOtherDomain in reOtherDomainList:
                    # 获取该URL的domain部分
                    tmpOnlyDomain = myUtils.getUrlOnlyDomain(tmpOtherDomain)
                    finalOtherDomainList.append({"domain":tmpOnlyDomain,"url":tmpOtherDomain})

            # 构建返回结果
            reDic = {}
            reDic["url"] = url
            reDic["status"] = status
            reDic["title"] = title
            reDic["contentLength"] = len(content)
            reDic["linkList"] = reLinkList
            reDic["sensiveInfoList"] = sensiveInfoList
            reDic["otherDomainList"] = finalOtherDomainList
            reDic["urlType"] = urlSuffix if urlSuffix != "" else "无"
            reDicStr = json.dumps(reDic)
        else:  # if reDic["checkFlag"]
            pass
        return reDicStr

    # 分析一个Html页面，提取其中的URI及URL
    # 返回一个，字典结构为：{"url":[URL数组],"otherDomains":[其他域名数组]}
    def analysisHtmlPage(self, pageUrl="", pageContent="", unvisitInterfaceUri=[]):
        reDic = {}
        reUrlList = []
        reOtherDomainList = []

        # 获得当前URL的域名值
        nowDomain = myUtils.getUrlDomain(pageUrl)

        totalUrlList = []
        totalUriList = []

        # 使用正则匹配所有script标签，提取其中的src属性
        regexStr = "<script[ /]+?[^>]*?src[ ]*?=[ ]*?['|\"](?P<jsUrl>.+?)['|\"].*?>"
        regexScriptResultList = re.findall(regexStr, pageContent, re.I)
        regexScriptResultList = sorted(regexScriptResultList, key=lambda uri: len(uri), reverse=True)
        # 从响应文本中替换所有匹配到的URL
        for tmpUrl in regexScriptResultList:
            while pageContent.find(tmpUrl) != -1:
                pageContent = pageContent.replace(tmpUrl, "")

        # 使用正则匹配所有link标签，提取其中的href属性
        regexStr = "<link[ /]+?[^>]*?href[ ]*?=[ ]*?['|\"](?P<hrefUrl>.+?)['|\"].*?>"
        regexLinkResultList = re.findall(regexStr, pageContent, re.I)
        regexLinkResultList = sorted(regexLinkResultList, key=lambda uri: len(uri), reverse=True)
        # 从响应文本中替换所有匹配到的URL
        for tmpUrl in regexLinkResultList:
            while pageContent.find(tmpUrl) != -1:
                pageContent = pageContent.replace(tmpUrl, "")

        regexResultList = regexScriptResultList+regexLinkResultList

        # 处理正则获取的URL
        for tmpSrcStr in regexResultList:
            tmpSrcStr = tmpSrcStr.strip()
            tmpUrlParseResult = urllib.parse.urlparse(tmpSrcStr)

            # 判断获取的src是否包含netloc属性（即是否为完整的http请求）
            if tmpUrlParseResult.netloc != "":
                # 为完整的http请求
                totalUrlList.append(tmpSrcStr)
            else:
                # 不是完整的http请求
                totalUriList.append(tmpSrcStr)

        # 提取所有符合URL格式的字符串
        extractUrlsResults = myUtils.extractUrls(pageContent)
        extractUrlsResults = sorted(extractUrlsResults, key=lambda uri: len(uri), reverse=True)
        # 从响应文本中替换所有匹配到的URL
        for tmpUrl in extractUrlsResults:
            while pageContent.find(tmpUrl) != -1:
                pageContent = pageContent.replace(tmpUrl, "")

        # 提取特殊URI
        extractSpecilUrisResults = myUtils.extractSpecilUris(pageContent)
        extractSpecilUrisResults = sorted(extractSpecilUrisResults, key=lambda uri: len(uri), reverse=True)
        # 从响应文本中替换所有匹配到的特殊URI
        for tmpUri in extractSpecilUrisResults:
            while pageContent.find(tmpUri) != -1:
                pageContent = pageContent.replace(tmpUri, "")

        # 提取URI
        extractUrisResults = myUtils.extractUris(pageContent)

        # 汇总提取数据
        totalUrlList = totalUrlList+extractUrlsResults
        totalUrlList = myUtils.solveExtractedUrls(totalUrlList)
        totalUriList = totalUriList+extractSpecilUrisResults+extractUrisResults
        totalUriList = myUtils.solveExtractedUrls(totalUriList)

        # 处理URL
        for tmpUrl in totalUrlList:
            # 判断链接是否能够爬取
            ifUnvisit = False
            for tmpUri in unvisitInterfaceUri:
                ifUnvisit = ifUnvisit or myUtils.ifSameUri(tmpUrl, tmpUri)
                if ifUnvisit:
                    break
                else:
                    pass
            if ifUnvisit:
                continue
            else:
                pass
            # 判断是否属于爬取域名的子域名
            if myUtils.ifSameMainDomain(nowDomain, myUtils.getUrlDomain(tmpUrl)):
                reUrlList.append(tmpUrl)
            else:
                reOtherDomainList.append(tmpUrl)

        # 处理URI
        for tmpUri in totalUriList:
            # 判断链接是否能够爬取
            ifUnvisit = False
            for tmpVisitInterfaceUri in unvisitInterfaceUri:
                ifUnvisit = ifUnvisit or myUtils.ifSameUri(tmpUri, tmpVisitInterfaceUri)
                if ifUnvisit:
                    break
                else:
                    pass
            if ifUnvisit:
                continue
            else:
                pass
            # 将URI进行拼接
            nowHref = urllib.parse.urljoin(pageUrl, tmpUri)
            reUrlList.append(nowHref)

        # 结果去重
        reUrlList = list(set(reUrlList))
        reOtherDomainList = list(set(reOtherDomainList))

        # 构造返回字典
        reDic["url"] = reUrlList
        reDic["otherDomains"] = reOtherDomainList
        return reDic

    # 分析css文件，传入一个网站域名，当前css文件地址，以及css文件的源码，需要额外拼接的URL列表，返回一个链接列表
    def analysisCssPage(self, nowScrawlUrl="", nowUrl="", pageContent="", extraUrlArr=[], unvisitInterfaceUri=[]):
        reList = []
        reOtherDomainList = []

        nowScrawlDomain = myUtils.getUrlDomain(nowScrawlUrl)
        nowUrlDomain = myUtils.getUrlDomain(nowUrl)
        nowStartDomain = myUtils.getUrlDomain(self.startUrl)

        # 解析URL函数中的参数
        tmpUrlFuncPartern = "url([ ]*['\"](?P<uri>.+?)['\"][ ]*)"
        matchUriStrList = re.findall(tmpUrlFuncPartern, pageContent)

        # 对提取到的URL及URI字符串进行处理
        matchUriStrList = list(set(matchUriStrList))
        matchUriStrList = myUtils.solveExtractedUrls(matchUriStrList)
        # 处理解析到的URI
        for tmpUriStr in matchUriStrList:
            tmpSrcStr = tmpUriStr.strip()
            tmpUrlParseResult = urllib.parse.urlparse(tmpSrcStr)

            # 判断获取的src是否包含netloc属性（即是否为完整的http请求）
            if tmpUrlParseResult.netloc != "":
                # 为完整的http请求
                if myUtils.ifSameMainDomain(nowScrawlDomain, myUtils.getUrlDomain(tmpSrcStr)):
                    # 判断链接是否能够爬取
                    ifUnvisit = False
                    for tmpUri in unvisitInterfaceUri:
                        ifUnvisit = ifUnvisit or myUtils.ifSameUri(tmpUri, tmpSrcStr)
                        if ifUnvisit:
                            break
                        else:
                            pass
                    if ifUnvisit:
                        continue
                    else:
                        reList.append(tmpSrcStr)
                else:
                    # 非爬取域名的子域名，加入其他域名列表
                    reOtherDomainList.append(tmpSrcStr)
            else:
                # 不是完整的http请求
                link = tmpUriStr.strip()
                # 判断链接是否能够爬取
                ifUnvisit = False
                for tmpVisitInterfaceUri in unvisitInterfaceUri:
                    ifUnvisit = ifUnvisit or myUtils.ifSameUri(link, tmpVisitInterfaceUri)
                    if ifUnvisit:
                        break
                    else:
                        pass
                if ifUnvisit:
                    continue
                else:
                    pass
                # 与当前输入网站域名结合
                reList.append(urllib.parse.urljoin(nowScrawlDomain, link))
                # 与当前输入网站URL结合
                reList.append(urllib.parse.urljoin(myUtils.getUrlWithoutFile(nowScrawlUrl), link))
                # 与开始输入网站域名相结合
                reList.append(urllib.parse.urljoin(nowStartDomain, link))
                # 与当前输入网站URL结合
                reList.append(urllib.parse.urljoin(myUtils.getUrlWithoutFile(self.startUrl), link))
                # 与js文件域名结合
                reList.append(urllib.parse.urljoin(nowUrlDomain, link))
                # 与js文件地址结合
                reList.append(urllib.parse.urljoin(myUtils.getUrlWithoutFile(nowUrl), link))
                # 与额外传入的URL地址结合
                for nowExtraUrl in extraUrlArr:
                    reList.append(urllib.parse.urljoin(nowExtraUrl, link))
                    reList.append(myUtils.joinUrl(nowExtraUrl, link))

        # 去重
        reList = list(set(reList))
        reOtherDomainList = list(set(reOtherDomainList))
        return reList, reOtherDomainList

    # 分析js文件，传入一个网站域名，当前js文件地址，以及js文件的源码，需要额外拼接的URL列表，返回一个链接列表
    def analysisJSPage(self, nowScrawlUrl="", nowUrl="", pageContent="", extraUrlArr=[], unvisitInterfaceUri=[]):
        reList = []
        reOtherDomainList = []

        nowScrawlDomain = myUtils.getUrlDomain(nowScrawlUrl)
        nowUrlDomain = myUtils.getUrlDomain(nowUrl)
        nowStartDomain = myUtils.getUrlDomain(self.startUrl)
        # 提取所有符合URL格式的字符串
        extractUrlsResults = list(set(myUtils.extractUrls(pageContent)))
        extractUrlsResults = sorted(extractUrlsResults, key=lambda uri: len(uri), reverse=True)
        # 从响应文本中替换所有匹配到的URL
        for tmpUrl in extractUrlsResults:
            while pageContent.find(tmpUrl) != -1:
                pageContent = pageContent.replace(tmpUrl, "")

        # 提取特殊URI
        extractSpecilUrisResults = list(set(myUtils.extractSpecilUris(pageContent)))
        extractSpecilUrisResults = sorted(extractSpecilUrisResults, key=lambda uri: len(uri), reverse=True)
        # 从响应文本中替换所有匹配到的特殊URI
        for tmpUri in extractSpecilUrisResults:
            while pageContent.find(tmpUri) != -1:
                pageContent = pageContent.replace(tmpUri, "")

        # 提取URI
        extractUrisResults = list(set(myUtils.extractUris(pageContent)))

        # 对提取到的URL字符串进行处理
        extractUrlsResults = myUtils.solveExtractedUrls(extractUrlsResults)
        extractSpecilUrisResults = myUtils.solveExtractedUrls(extractSpecilUrisResults)
        extractUrisResults = myUtils.solveExtractedUrls(extractUrisResults)
        extractUrisResults = list(set(extractSpecilUrisResults+extractUrisResults))

        # 处理URL
        # 判断是否属于爬取域名的子域名
        for tmpUrl in extractUrlsResults:
            if myUtils.ifSameMainDomain(nowScrawlDomain, myUtils.getUrlDomain(tmpUrl)):
                # 判断链接是否能够爬取
                ifUnvisit = False
                for tmpUri in unvisitInterfaceUri:
                    ifUnvisit = ifUnvisit or myUtils.ifSameUri(tmpUri, tmpUrl)
                    if ifUnvisit:
                        break
                    else:
                        pass
                if ifUnvisit:
                    continue
                else:
                    reList.append(tmpUrl)
            else:
                # 非爬取域名的子域名，加入其他域名列表
                reOtherDomainList.append(tmpUrl)

        # 处理URI
        for tmpUri in extractUrisResults:
            link = tmpUri
            # 判断链接是否能够爬取
            ifUnvisit = False
            for tmpVisitInterfaceUri in unvisitInterfaceUri:
                ifUnvisit = ifUnvisit or myUtils.ifSameUri(link, tmpVisitInterfaceUri)
                if ifUnvisit:
                    break
                else:
                    pass
            if ifUnvisit:
                continue
            else:
                pass
            # 与当前输入网站域名结合
            reList.append(urllib.parse.urljoin(nowScrawlDomain, link))
            # 与当前输入网站URL结合
            reList.append(urllib.parse.urljoin(myUtils.getUrlWithoutFile(nowScrawlUrl), link))
            # 与开始输入网站域名相结合
            reList.append(urllib.parse.urljoin(nowStartDomain, link))
            # 与当前输入网站URL结合
            reList.append(urllib.parse.urljoin(myUtils.getUrlWithoutFile(self.startUrl), link))
            # 与js文件域名结合
            reList.append(urllib.parse.urljoin(nowUrlDomain, link))
            # 与js文件地址结合
            reList.append(urllib.parse.urljoin(myUtils.getUrlWithoutFile(nowUrl), link))
            # 与额外传入的URL地址结合
            for nowExtraUrl in extraUrlArr:
                reList.append(urllib.parse.urljoin(nowExtraUrl, link))
                reList.append(myUtils.joinUrl(nowExtraUrl, link))

        # 去重
        reList = list(set(reList))
        reOtherDomainList = list(set(reOtherDomainList))
        return reList,reOtherDomainList

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
