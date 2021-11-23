#!/usr/bin/env python
# coding=utf-8
import json
import time
from queue import Queue

from PyQt5.QtCore import QThread, pyqtSignal

from UrlScrapyThreading import UrlScrapyThreading


class UrlScrapyManage(QThread):
    signal_result = pyqtSignal(str)
    signal_log = pyqtSignal([str], [str, str])
    signal_progress = pyqtSignal(str, str, str)
    signal_end = pyqtSignal()

    def __init__(self, scrawlUrlArr=[], maxThreadCount=50, parent=None):
        super(UrlScrapyManage, self).__init__(parent)
        self.scrawlUrlArr = scrawlUrlArr
        self.scrawlUrl = ""
        self.vistedLinkList = []
        self.urlQueue = Queue()
        self.processCount = 5
        self.resultList = []
        self.maxThreadCount = maxThreadCount
        self.threadPool = []

    def run(self):
        self.signal_log[str, str].emit("扫描开始", "blue")
        self.signal_log.emit("")
        visitedCount = 0

        # 将启动URL加入队列
        for scrawlUrl in self.scrawlUrlArr:
            self.urlQueue.put(scrawlUrl)
            self.vistedLinkList.append(scrawlUrl)

        # 创建一个候选线程队列
        scrapyWaitQueue = Queue()
        # 开启多线程
        while (not self.urlQueue.empty()) or (not scrapyWaitQueue.empty()) or len(self.threadPool) != 0:
            # 将url队列中所有URL取出并创建线程，加入候选线程队列
            while not self.urlQueue.empty():
                nowUrl = self.urlQueue.get()
                nowScrapyThread = self.createThreadObj(nowUrl)
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
        self.signal_end.emit()

    def createThreadObj(self, scrawlUrl=""):
        threadObj = UrlScrapyThreading(scrawlUrl)
        threadObj.signal_end.connect(self.solveThreadResult)
        return threadObj

    # 请求地址线程结束信号绑定函数
    def solveThreadResult(self, reDicStr):
        if reDicStr != "":
            reDic = json.loads(reDicStr)
            reLinkList = reDic.pop("linkList")
            # 写入新的链接
            for tempLink in reLinkList:
                if tempLink not in self.vistedLinkList:
                    self.vistedLinkList.append(tempLink)
                    self.urlQueue.put(tempLink)
                else:
                    pass
            # 显示结果
            reDicStr = json.dumps(reDic)
            self.signal_result.emit(reDicStr)
        else:
            pass
