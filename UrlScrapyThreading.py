#!/usr/bin/env python
# coding=utf-8
import json
import re
import urllib.parse

from PyQt5.QtCore import QThread, pyqtSignal

import myUtils


class UrlScrapyThreading(QThread):
    signal_end = pyqtSignal(str)

    def __init__(self, scrawlUrl, sensiveKeyList=[], crawlerUrl="", startUrl="", parent=None, extraUrlArr=[],
                 nowCookie={},
                 proxies=None, unvisitInterfaceUri=[], userAgent="", nowHeaders={}):
        super(UrlScrapyThreading, self).__init__(parent)
        self.scrawlUrl = scrawlUrl
        self.crawlerUrl = crawlerUrl
        self.sensiveKeyList = sensiveKeyList
        self.startUrl = startUrl
        self.extraUrlArr = extraUrlArr
        self.nowCookie = nowCookie
        self.proxies = proxies
        self.unvisitInterfaceUri = unvisitInterfaceUri
        self.userAgent = userAgent
        self.nowHeaders = nowHeaders

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

        for tmpKey, tmpVal in self.nowHeaders.items():
            tmpHeader[tmpKey] = tmpVal

        # 如果请求失败，默认会重试1次
        requestCount = 0
        retryMaxCount = 2

        for requestCount in range(retryMaxCount):
            # 请求这个URL
            try:
                tempDic = myUtils.requestsUrl(url, cookie=self.nowCookie,
                                              proxies=self.proxies, header=tmpHeader)
            except Exception as ex:
                continue

            if tempDic["checkFlag"]:
                # 访问成功
                status = tempDic["status"]

                if str(status).strip() == "404" or str(status).strip() == "400":
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
                elif str(status)[0] != "2":
                    # 对于非2开头的响应，不进行爬虫操作，仅记录请求结果
                    pass
                else:
                    if urlSuffix in myUtils.getHtmlCrawlerScriptFileSuffixList():
                        # 是js文件，使用js文件分析方法分析
                        tempLinkList, tmpOtherDomainList = self.analysisJSPage(self.crawlerUrl, url, content,
                                                                               extraUrlArr=self.extraUrlArr,
                                                                               unvisitInterfaceUri=self.unvisitInterfaceUri)
                        for tempLink in tempLinkList:
                            reLinkList.append((tempLink, self.startUrl, url))

                        reOtherDomainList += tmpOtherDomainList
                    elif urlSuffix in myUtils.getHtmlCrawlerCssFileSuffixList():
                        # 是css文件，使用css文件分析方法分析
                        tempLinkList, tmpOtherDomainList = self.analysisCssPage(self.crawlerUrl, url, content,
                                                                                extraUrlArr=self.extraUrlArr,
                                                                                unvisitInterfaceUri=self.unvisitInterfaceUri)
                        for tempLink in tempLinkList:
                            reLinkList.append((tempLink, self.startUrl, url))

                        reOtherDomainList += tmpOtherDomainList
                    else:
                        # 不是js和css文件，按HTML文件分析方法分析
                        reHtmlDic = self.analysisHtmlPage(pageUrl=tempDic["url"], pageContent=content,
                                                          unvisitInterfaceUri=self.unvisitInterfaceUri,
                                                          crawlerUrl=self.crawlerUrl, extraUrlArr=self.extraUrlArr)
                        tempLinkList = reHtmlDic["url"]
                        for tempLink in tempLinkList:
                            reLinkList.append((tempLink, self.startUrl, url))

                        tmpOtherDomainList = reHtmlDic["otherDomains"]

                        reOtherDomainList += tmpOtherDomainList

                    # 分析敏感信息
                    sensiveInfoList = self.analysisSensiveInfo(url, content)

                    # 返回前去重
                    reOtherDomainList = list(set(reOtherDomainList))

                    # 将其他域名进行处理
                    finalOtherDomainList = []
                    for tmpOtherDomain in reOtherDomainList:
                        # 获取该URL的domain部分
                        tmpOnlyDomain = myUtils.getUrlOnlyDomain(tmpOtherDomain)
                        finalOtherDomainList.append({"domain": tmpOnlyDomain, "url": tmpOtherDomain})

                # 构建返回结果
                reDic = {}
                reDic["url"] = url
                reDic["status"] = status
                reDic["title"] = title
                reDic["contentLength"] = len(content)
                reDic["content"] = content
                reDic["linkList"] = reLinkList
                reDic["sensiveInfoList"] = sensiveInfoList
                reDic["otherDomainList"] = finalOtherDomainList
                reDic["urlType"] = urlSuffix if urlSuffix != "" else "无"
                reDicStr = json.dumps(reDic)
                break
            else:  # if reDic["checkFlag"]
                continue
        return reDicStr

    # 分析一个Html页面，提取其中的URI及URL
    # 返回一个，字典结构为：{"url":[URL数组],"otherDomains":[其他域名数组]}
    def analysisHtmlPage(self, pageUrl="", pageContent="", unvisitInterfaceUri=[], crawlerUrl="", extraUrlArr=[]):
        reDic = {}
        reUrlList = []
        reOtherDomainList = []

        nowUesdDomainList = myUtils.getAllUseDomainList(crawlerUrl, pageUrl, self.startUrl, extraUrlArr)

        totalUrlList = []
        totalUriList = []

        # 使用正则匹配所有script标签，提取其中的src属性
        regexStr = "<script[ /]+?[^>]*?src[ ]*?=[ ]*?['\"]{0,1}(?P<jsUrl>.+?)(?:(?:['\"].*?>)|[ >])"
        regexScriptResultList = re.findall(regexStr, pageContent, re.I)
        regexScriptResultList = sorted(regexScriptResultList, key=lambda uri: len(uri), reverse=True)
        # 从响应文本中替换所有匹配到的URL
        for tmpUrl in regexScriptResultList:
            while pageContent.find(tmpUrl) != -1:
                pageContent = pageContent.replace(tmpUrl, "")

        # 使用正则匹配所有link标签，提取其中的href属性
        regexStr = "<link[ /]+?[^>]*?href[ ]*?=[ ]*?['\"]{0,1}(?P<hrefUrl>.+?)(?:(?:['\"].*?>)|[ >])"
        regexLinkResultList = re.findall(regexStr, pageContent, re.I)
        regexLinkResultList = sorted(regexLinkResultList, key=lambda uri: len(uri), reverse=True)
        # 从响应文本中替换所有匹配到的URL
        for tmpUrl in regexLinkResultList:
            while pageContent.find(tmpUrl) != -1:
                pageContent = pageContent.replace(tmpUrl, "")

        # 使用正则匹配所有a标签，提取其中的href属性
        regexStr = "<a[ /]+?[^>]*?href[ ]*?=[ ]*?['\"]{0,1}(?P<hrefUrl>.+?)(?:(?:['\"].*?>)|[ >])"
        regexAResultList = re.findall(regexStr, pageContent, re.I)
        regexAResultList = [u for u in regexAResultList if not (u.startswith("javascript:") or u == "#")]
        regexAResultList = sorted(regexAResultList, key=lambda uri: len(uri), reverse=True)
        # 从响应文本中替换所有匹配到的URL
        for tmpUrl in regexAResultList:
            while pageContent.find(tmpUrl) != -1:
                pageContent = pageContent.replace(tmpUrl, "")

        regexResultList = regexScriptResultList + regexLinkResultList + regexAResultList

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
        totalUrlList = totalUrlList + extractUrlsResults
        totalUrlList = myUtils.solveExtractedUrls(totalUrlList)
        totalUriList = totalUriList + extractSpecilUrisResults + extractUrisResults
        totalUriList = myUtils.solveExtractedUrls(totalUriList)

        # 处理URL
        for tmpUrl in totalUrlList:

            if self.checkIfUrlSameMainDomainWithDomainList(tmpUrl, nowUesdDomainList):
                # 爬取到的URL的主域名符合要求
                # 判断URI是否能够爬取
                ifUnvisit = False
                for tmpUnvisitUri in unvisitInterfaceUri:
                    ifUnvisit = ifUnvisit or myUtils.ifSameUri(tmpUnvisitUri, tmpUrl)
                    if ifUnvisit:
                        break
                    else:
                        continue
                if ifUnvisit:
                    continue
                else:
                    reUrlList.append(tmpUrl)
                    totalUriList.append(myUtils.getUrlStartWithPath(tmpUrl))
            else:
                # 爬取到的URL的主域名不符合要求，加入其他域名列表
                reOtherDomainList.append(tmpUrl)

        # 处理URI
        for tmpUri in totalUriList:
            # 判断链接是否能够爬取
            ifUnvisit = False
            for tmpUnvisitUri in unvisitInterfaceUri:
                ifUnvisit = ifUnvisit or myUtils.ifSameUri(tmpUnvisitUri, tmpUri)
                if ifUnvisit:
                    break
                else:
                    continue
            if ifUnvisit:
                continue
            else:
                pass
            # 将URI进行拼接
            reUrlList += self.urlJoinUriWithPaths(tmpUri, self.startUrl, crawlerUrl, pageUrl, extraUrlArr)

        # 结果去重
        reUrlList = list(set(reUrlList))
        reOtherDomainList = list(set(reOtherDomainList))

        # 构造返回字典
        reDic["url"] = reUrlList
        reDic["otherDomains"] = reOtherDomainList
        return reDic

    # 分析css文件，传入一个网站域名，当前css文件地址，以及css文件的源码，需要额外拼接的URL列表，返回一个链接列表
    def analysisCssPage(self, nowCrawlerUrl="", nowUrl="", pageContent="", extraUrlArr=[], unvisitInterfaceUri=[]):
        reList = []
        reOtherDomainList = []

        nowUesdDomainList = myUtils.getAllUseDomainList(nowCrawlerUrl, nowUrl, self.startUrl, extraUrlArr)

        # 解析URL函数中的参数
        tmpUrlFuncPartern = "url\([ ]*(?P<uri>.+?)[ ]*\)"
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
                # 判断是否属于爬取域名的子域名
                if self.checkIfUrlSameMainDomainWithDomainList(tmpUriStr, nowUesdDomainList):
                    # 判断URI是否能够爬取
                    ifUnvisit = False
                    for tmpUnvisitUri in unvisitInterfaceUri:
                        ifUnvisit = ifUnvisit or myUtils.ifSameUri(tmpUnvisitUri, tmpUriStr)
                        if ifUnvisit:
                            break
                        else:
                            continue
                    if ifUnvisit:
                        continue
                    else:
                        reList.append(tmpSrcStr)
                        matchUriStrList.append(myUtils.getUrlStartWithPath(tmpSrcStr))
                else:
                    # 非爬取域名的子域名，加入其他域名列表
                    reOtherDomainList.append(tmpSrcStr)
            else:
                # 不是完整的http请求
                # 判断链接是否能够爬取
                ifUnvisit = False
                for tmpUnvisitUri in unvisitInterfaceUri:
                    ifUnvisit = ifUnvisit or myUtils.ifSameUri(tmpUnvisitUri, tmpUriStr)
                    if ifUnvisit:
                        break
                    else:
                        continue
                if ifUnvisit:
                    continue
                else:
                    pass
                # 拼接URI
                reList += self.urlJoinUriWithPaths(tmpUriStr, self.startUrl, nowCrawlerUrl, nowUrl, extraUrlArr)

        # 去重
        reList = list(set(reList))
        reOtherDomainList = list(set(reOtherDomainList))
        return reList, reOtherDomainList

    # 分析js文件，传入一个网站域名，当前js文件地址，以及js文件的源码，需要额外拼接的URL列表，返回一个链接列表
    def analysisJSPage(self, nowCrawlerUrl="", nowUrl="", pageContent="", extraUrlArr=[], unvisitInterfaceUri=[]):
        reList = []
        reOtherDomainList = []

        nowUesdDomainList = myUtils.getAllUseDomainList(nowCrawlerUrl, nowUrl, self.startUrl, extraUrlArr)

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
        for tmpUnvisitUri in extractSpecilUrisResults:
            while pageContent.find(tmpUnvisitUri) != -1:
                pageContent = pageContent.replace(tmpUnvisitUri, "")

        # 提取URI
        extractUrisResults = list(set(myUtils.extractUris(pageContent)))

        # 对提取到的URL字符串进行处理
        extractUrlsResults = myUtils.solveExtractedUrls(extractUrlsResults)
        extractSpecilUrisResults = myUtils.solveExtractedUrls(extractSpecilUrisResults)
        extractUrisResults = myUtils.solveExtractedUrls(extractUrisResults)
        extractUrisResults = list(set(extractSpecilUrisResults + extractUrisResults))

        # 处理URL
        # 判断是否属于爬取域名的子域名
        for tmpUrl in extractUrlsResults:
            if self.checkIfUrlSameMainDomainWithDomainList(tmpUrl, nowUesdDomainList):
                # 爬取到的URL的主域名符合要求
                # 判断URI是否能够爬取
                ifUnvisit = False
                for tmpUnvisitUri in unvisitInterfaceUri:
                    ifUnvisit = ifUnvisit or myUtils.ifSameUri(tmpUnvisitUri, tmpUrl)
                    if ifUnvisit:
                        break
                    else:
                        continue
                if ifUnvisit:
                    continue
                else:
                    reList.append(tmpUrl)
                    extractUrisResults.append(myUtils.getUrlStartWithPath(tmpUrl))
            else:
                # 爬取到的URL的主域名不符合要求，加入其他域名列表
                reOtherDomainList.append(tmpUrl)

        # 处理URI
        for tmpUri in extractUrisResults:
            # 判断URI是否能够爬取
            ifUnvisit = False
            for tmpUnvisitUri in unvisitInterfaceUri:
                ifUnvisit = ifUnvisit or myUtils.ifSameUri(tmpUnvisitUri, tmpUri)
                if ifUnvisit:
                    break
                else:
                    continue
            if ifUnvisit:
                continue
            else:
                pass
            # 拼接URI
            reList += self.urlJoinUriWithPaths(tmpUri, self.startUrl, nowCrawlerUrl, nowUrl, extraUrlArr)

        # 去重
        reList = list(set(reList))
        reOtherDomainList = list(set(reOtherDomainList))
        return reList, reOtherDomainList

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

    def urlJoinUriWithPaths(self, uri, startUrl, crawlerUrl, fileUrl, extraUrlList):
        reUrlList = []
        # 与开始URL的域名部分结合
        reUrlList.append(myUtils.joinUrl(myUtils.getUrlDomain(startUrl), uri))
        # 与开始URL的目录部分结合（即不包含文件名部分）
        reUrlList.append(myUtils.joinUrl(myUtils.getUrlWithoutFilePath(startUrl), uri))
        # 强制去除URL的最后一级内容，并与URI结合
        reUrlList.append(myUtils.joinUrl(myUtils.getUrlWithoutLastPath(startUrl), uri))
        # 判断来源URL与开始URL的域名+端口是否相同
        if myUtils.ifSameDomainWithTwoUrl(crawlerUrl, startUrl):
            # 与来源URL的域名部分结合
            reUrlList.append(myUtils.joinUrl(myUtils.getUrlDomain(crawlerUrl), uri))
            # 与来源URL的目录部分结合（即不包含文件名部分）
            reUrlList.append(myUtils.joinUrl(myUtils.getUrlWithoutFilePath(crawlerUrl), uri))
            # 强制去除URL的最后一级内容，并与URI结合
            reUrlList.append(myUtils.joinUrl(myUtils.getUrlWithoutLastPath(crawlerUrl), uri))
        # 判断文件URL与开始URL的域名+端口是否相同
        if myUtils.ifSameDomainWithTwoUrl(fileUrl, startUrl):
            # 与文件URL的域名部分结合
            reUrlList.append(myUtils.joinUrl(myUtils.getUrlDomain(fileUrl), uri))
            # 与文件URL的目录部分结合（即不包含文件名部分）
            reUrlList.append(myUtils.joinUrl(myUtils.getUrlWithoutFilePath(fileUrl), uri))
            # 强制去除URL的最后一级内容，并与URI结合
            reUrlList.append(myUtils.joinUrl(myUtils.getUrlWithoutLastPath(fileUrl), uri))
        # 与额外传入的URL地址结合
        for nowExtraUrl in extraUrlList:
            # 与额外传入的URL的目录部分结合（即不包含文件名部分）
            reUrlList.append(myUtils.joinUrl(myUtils.getUrlWithoutFilePath(nowExtraUrl), uri))
        # 将结果去重
        reUrlList = list(set(reUrlList))
        return reUrlList

    def checkIfUrlSameMainDomainWithDomainList(self, url, domainList):
        ifSameFlag = True
        tmpUrlDomain = myUtils.getUrlOnlyDomain(url)
        for tmpDomain in domainList:
            if not myUtils.ifSameMainDomain(tmpUrlDomain, tmpDomain):
                ifSameFlag = False
                break
            else:
                continue
        return ifSameFlag
