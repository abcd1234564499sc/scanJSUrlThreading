#!/usr/bin/env python
# coding=utf-8
import json
import time
import myUtils
from queue import Queue

from PyQt5.QtCore import QThread, pyqtSignal

from UrlScrapyThreading import UrlScrapyThreading


class UrlScrapyManage(QThread):
    signal_url_result = pyqtSignal(str)
    signal_sensive_result = pyqtSignal(str)
    signal_other_domain_result = pyqtSignal(str)
    signal_log = pyqtSignal([str], [str, str])
    signal_progress = pyqtSignal(str, str, str)
    signal_end = pyqtSignal(bool)

    def __init__(self, scrawlUrlArr=[], maxThreadCount=50, sensiveKeyList=[], parent=None, extraUrlArr=[],
                 nowCookie={}, proxies=None, unvisitInterfaceUri=[],userAgent="",nowHeaders={}):
        super(UrlScrapyManage, self).__init__(parent)
        self.scrawlUrlArr = scrawlUrlArr
        self.scrawlUrl = ""
        self.vistedLinkList = []       # 该列表用于去重，只记录URL参数，不记录参数的值
        self.fileContentHashList =[]   # 记录请求内容的hash值，防止重复请求相同
        self.urlQueue = Queue()
        self.processCount = 5
        self.resultList = []
        self.maxThreadCount = maxThreadCount
        self.threadPool = []
        self.sensiveKeyList = sensiveKeyList
        self.extraUrlArr = extraUrlArr
        self.nowCookie = nowCookie
        self.proxies = proxies
        self.unvisitInterfaceUri = unvisitInterfaceUri
        self.userAgent = userAgent
        self.nowHeaders = nowHeaders

    def run(self):
        self.signal_log[str, str].emit("扫描开始", "blue")
        self.signal_log.emit("")
        visitedCount = 0

        # 将启动URL加入队列
        for scrawlUrl in self.scrawlUrlArr:
            self.urlQueue.put((scrawlUrl, scrawlUrl,scrawlUrl))
            self.vistedLinkList.append(myUtils.parseUrlWithoutArgsValue(scrawlUrl))

        # 创建一个候选线程队列
        scrapyWaitQueue = Queue()
        # 开启多线程
        while (not self.urlQueue.empty()) or (not scrapyWaitQueue.empty()) or len(self.threadPool) != 0:
            # 将url队列中所有URL取出并创建线程，加入候选线程队列
            while not self.urlQueue.empty():
                nowItem = self.urlQueue.get()
                nowUrl = nowItem[0]
                nowStartUrl = nowItem[1]
                nowCrawlerUrl = nowItem[2]
                nowScrapyThread = self.createThreadObj(nowUrl, self.sensiveKeyList,crawlerUrl=nowCrawlerUrl, startUrl=nowStartUrl,
                                                       extraUrlArr=self.extraUrlArr, nowCookie=self.nowCookie,
                                                       proxies=self.proxies,
                                                       unvisitInterfaceUri=self.unvisitInterfaceUri,userAgent=self.userAgent,nowHeaders=self.nowHeaders)
                scrapyWaitQueue.put(nowScrapyThread)

            # 遍历线程池，将已经完成的线程移除
            for index, tempThread in enumerate(self.threadPool):
                if tempThread.isFinished():
                    tempThread.terminate()
                    tempThread.quit()
                    visitedCount = visitedCount + 1
                    self.threadPool.pop(index)

            # 判断当前现称池中线程是否超过最大线程数，
            # 若未超过，则从候选线程队列取出一个线程加入线程池，并启动
            while len(self.threadPool) < self.maxThreadCount:
                if scrapyWaitQueue.empty():
                    break
                nowThread = scrapyWaitQueue.get()

                self.signal_log.emit("请求地址：" + nowThread.getScrawlUrl())
                try:
                    nowThread.start()
                except Exception as ex:
                    self.signal_log.emit(str(ex), color="red")
                self.threadPool.append(nowThread)

            # 打印当前进度
            self.signal_progress.emit(str(visitedCount), str(scrapyWaitQueue.qsize()), str(len(self.threadPool)))
            time.sleep(1)

        self.signal_log.emit("")
        self.signal_log[str, str].emit("扫描结束", "blue")
        self.signal_end.emit(True)

    def createThreadObj(self, scrawlUrl="", sensiveKeyList=[], crawlerUrl="",startUrl="", extraUrlArr=[], nowCookie={}, proxies=None,
                        unvisitInterfaceUri=[],userAgent="",nowHeaders={}):
        threadObj = UrlScrapyThreading(scrawlUrl, sensiveKeyList, crawlerUrl=crawlerUrl,startUrl=startUrl, extraUrlArr=extraUrlArr,
                                       nowCookie=nowCookie, proxies=proxies, unvisitInterfaceUri=unvisitInterfaceUri,userAgent=userAgent,nowHeaders=nowHeaders)
        threadObj.signal_end.connect(self.solveThreadResult)
        return threadObj

    # 请求地址线程结束信号绑定函数
    def solveThreadResult(self, reDicStr):
        if reDicStr != "":
            reDic = json.loads(reDicStr)
            tmpResContent = reDic.pop("content")
            reLinkList = reDic.pop("linkList")
            reSensiveList = reDic.pop("sensiveInfoList")
            reOtherDomainList = reDic.pop("otherDomainList")
            # 计算返回内容的hash值
            tmpContentHash = myUtils.calcResponseHash(tmpResContent)
            if tmpContentHash not in self.fileContentHashList:
                self.fileContentHashList.append(tmpContentHash)
                # 写入新的链接
                for tempLinkItem in reLinkList:
                    tempLink = tempLinkItem[0]
                    tempStartLink = tempLinkItem[1]
                    tempCrawlerUrl = tempLinkItem[2]
                    # tempLinkWithoutArgValue = myUtils.parseUrlWithoutArgsValue(tempLinkItem[0])
                    if tempLink not in self.vistedLinkList:
                        self.vistedLinkList.append(tempLink)
                        self.urlQueue.put((tempLink, tempStartLink,tempCrawlerUrl))
                    else:
                        pass
                # 显示结果
                reDicStr = json.dumps(reDic)
                self.signal_url_result.emit(reDicStr)
                reSensiveStr = json.dumps(reSensiveList)
                self.signal_sensive_result.emit(reSensiveStr)
                reOtherDomainStr = json.dumps(reOtherDomainList)
                self.signal_other_domain_result.emit(reOtherDomainStr)
            else:
                pass
        else:
            pass
