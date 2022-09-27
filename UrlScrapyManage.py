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
    signal_log = pyqtSignal([str], [str, str])
    signal_progress = pyqtSignal(str, str, str)
    signal_end = pyqtSignal(bool)

    def __init__(self, scrawlUrlArr=[], maxThreadCount=50, sensiveKeyList=[], parent=None, extraUrlArr=[],
                 nowCookie="", proxies=None, unvisitInterfaceUri=[]):
        super(UrlScrapyManage, self).__init__(parent)
        self.scrawlUrlArr = scrawlUrlArr
        self.scrawlUrl = ""
        self.vistedLinkList = []       # 该列表用于去重，只记录URL参数，不记录参数的值
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

    def run(self):
        self.signal_log[str, str].emit("扫描开始", "blue")
        self.signal_log.emit("")
        visitedCount = 0

        # 将启动URL加入队列
        for scrawlUrl in self.scrawlUrlArr:
            self.urlQueue.put((scrawlUrl, scrawlUrl))
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
                nowScrapyThread = self.createThreadObj(nowUrl, self.sensiveKeyList, startUrl=nowStartUrl,
                                                       extraUrlArr=self.extraUrlArr, nowCookie=self.nowCookie,
                                                       proxies=self.proxies,
                                                       unvisitInterfaceUri=self.unvisitInterfaceUri)
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

    def createThreadObj(self, scrawlUrl="", sensiveKeyList=[], startUrl="", extraUrlArr=[], nowCookie="", proxies=None,
                        unvisitInterfaceUri=[]):
        threadObj = UrlScrapyThreading(scrawlUrl, sensiveKeyList, startUrl=startUrl, extraUrlArr=extraUrlArr,
                                       nowCookie=nowCookie, proxies=proxies, unvisitInterfaceUri=unvisitInterfaceUri)
        threadObj.signal_end.connect(self.solveThreadResult)
        return threadObj

    # 请求地址线程结束信号绑定函数
    def solveThreadResult(self, reDicStr):
        if reDicStr != "":
            reDic = json.loads(reDicStr)
            reLinkList = reDic.pop("linkList")
            reSensiveList = reDic.pop("sensiveInfoList")
            # 写入新的链接
            for tempLinkItem in reLinkList:
                tempLink = tempLinkItem[0]
                tempStartLink = tempLinkItem[1]
                tempLinkWithoutArgValue = myUtils.parseUrlWithoutArgsValue(tempLinkItem[0])
                if tempLinkWithoutArgValue not in self.vistedLinkList:
                    self.vistedLinkList.append(tempLinkWithoutArgValue)
                    self.urlQueue.put((tempLink, tempStartLink))
                else:
                    pass
            # 显示结果
            reDicStr = json.dumps(reDic)
            self.signal_url_result.emit(reDicStr)
            reSensiveStr = json.dumps(reSensiveList)
            self.signal_sensive_result.emit(reSensiveStr)
        else:
            pass
