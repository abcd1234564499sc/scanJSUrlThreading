#!/usr/bin/env python
# coding=utf-8
import json
import os
import re
import sys
import urllib.parse
import warnings

from PyQt5.QtCore import QDir
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor, QBrush, QColor
from PyQt5.QtWidgets import QApplication, QWidget, QHeaderView, QTableWidgetItem, QFileDialog

import myUtils
from ConfWinodw import ConfWindow
from ExportExcellThread import ExportExcellThread
from UrlScrapyManage import UrlScrapyManage
from ui.ui_main import Ui_Main_Form


class Main(QWidget, Ui_Main_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setHorizontalHeaderLabels(["URL", "响应码", "标题", "包长度", "URL类型"])
        self.urlResultDictKeyList = ["url","status","title","contentLength","urlType"]
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tableWidget.setColumnWidth(1, 60)
        self.tableWidget.hideColumn(5)
        self.tableWidget_2.setColumnCount(3)
        self.tableWidget_2.setHorizontalHeaderLabels(["URL", "关键词", "敏感信息"])
        self.sensiveDictKeyList = ["url","key","seneiveStr"]
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tableWidget_2.setColumnWidth(1, 100)
        self.tableWidget_3.setColumnCount(2)
        self.tableWidget_3.setHorizontalHeaderLabels(["域名","URL"])
        self.otherDomainResultDictKeyList = ["domain", "url"]
        self.tableWidget_3.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget_3.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tableWidget_3.setColumnWidth(1, 600)
        self.urlRegex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        self.urlScrapy = None
        self.exportExcellThread = None
        self.confFileName = "扫描器配置.conf"
        self.confHeadList = ["最大线程数", "敏感信息关键词列表", "过滤信息列表", "是否使用代理", "代理IP", "代理端口", "代理是否使用HTTPS", "导出单次保存数据行数"]
        warnings.filterwarnings("ignore")
        self.confDic = self.initConfFile()
        self.confWindow = ConfWindow(self.confDic)
        self.userAgentDic = {}
        self.userAgentDic[0]="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        self.userAgentDic[1]="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
        self.userAgentDic[2]="Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 2.0.50727; SLCC2; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; Tablet PC 2.0; .NET4.0E)"

    # 初始化配置文件，生成配置文件并返回一个配置字典
    # 字典结构为：{
    # "confFileName":配置文件文件名,
    # "maxThreadCount":最大线程数,
    # "sensiveKeyList":敏感信息关键词列表,
    # "filterList":过滤条件列表，列表内容为一个包含3个元素的列表，3个元素分别是：
    #       过滤项：0代表标题，1代表包长度
    #       过滤条件：0代表包含，1代表不包含，2代表等于，3代表不等于
    #       过滤值,
    # "confHeaderList":配置名列表,
    # "ifProxy":是否开启代理，
    # "proxyIp":代理IP,
    # "proxyPort":代理端口,
    # "exportSaveCount":导出时每次保存处理的数据数
    # }
    def initConfFile(self):
        defaultMaxThreadCount = 50
        defaultExportSaveCount = 1000
        defaultSensiveKeyList = ["默认密码", "默认账号", "默认用户名", "default username", "default password","ftp:","ftp@","svn:","svn+",".git",".js.map","jdbc:","file:"]
        defaultFilterList = []
        defaultIfProxy = 0
        defaultIfProxyHttps = 0
        defaultProxyIp = ""
        defaultProxyPort = ""
        defaultConfHeaderList = self.confHeadList
        confDic = {defaultConfHeaderList[0]: defaultMaxThreadCount, defaultConfHeaderList[1]: defaultSensiveKeyList,
                   defaultConfHeaderList[2]: defaultFilterList, defaultConfHeaderList[3]: defaultIfProxy,
                   defaultConfHeaderList[4]: defaultProxyIp, defaultConfHeaderList[5]: defaultProxyPort,
                   defaultConfHeaderList[6]: defaultIfProxyHttps, defaultConfHeaderList[7]: defaultExportSaveCount,
                   }

        # 判断是否存在配置文件
        confFilePath = os.path.join(os.getcwd(), self.confFileName)
        if not os.path.exists(confFilePath):
            myUtils.writeToConfFile(confFilePath, confDic)
            confDic["confHeader"] = defaultConfHeaderList
        else:
            confDic = myUtils.readConfFile(confFilePath)
        headerList = confDic["confHeader"]

        reConfDic = {"confFilePath": confFilePath, "maxThreadCount": int(confDic[headerList[0]]),
                     "sensiveKeyList": confDic[headerList[1]], "filterList": confDic[headerList[2]],
                     "confHeaderList": headerList, "ifProxy": True if int(confDic[headerList[3]]) == 1 else False,
                     "proxyIp": confDic[headerList[4]], "proxyPort": confDic[headerList[5]],
                     "ifProxyUseHttps": True if int(confDic[headerList[6]]) == 1 else False,
                     "exportSaveCount": int(confDic[headerList[7]])}

        # 更新代理设置
        if reConfDic["ifProxy"]:
            proxyPro = "https" if reConfDic["ifProxyUseHttps"] else "http"
            proxyStr = "{0}://{1}:{2}".format(proxyPro, reConfDic["proxyIp"], reConfDic["proxyPort"])
            self.proxies = {"http": proxyStr, "https": proxyStr}
        else:
            self.proxies = None

        return reConfDic

    def createCrawlObj(self, scrawlUrlArr=[], maxThreadCount=50, sensiveKeyList=[], extraUrlArr=[], nowCookie={},
                       proxies=None, unvisitInterfaceUri=[],userAgent="",nowHeaders={}):
        urlScrapy = UrlScrapyManage(scrawlUrlArr=scrawlUrlArr, maxThreadCount=maxThreadCount,
                                    sensiveKeyList=sensiveKeyList, extraUrlArr=extraUrlArr, nowCookie=nowCookie,
                                    proxies=proxies, unvisitInterfaceUri=unvisitInterfaceUri,userAgent=userAgent,nowHeaders=nowHeaders)
        urlScrapy.signal_log[str].connect(self.writeLog)
        urlScrapy.signal_log[str, str].connect(self.writeLog)
        urlScrapy.signal_url_result.connect(self.writeUrlResult)
        urlScrapy.signal_sensive_result.connect(self.writeSensiveResult)
        urlScrapy.signal_other_domain_result.connect(self.writeOtherDomainResult)
        urlScrapy.signal_progress.connect(self.writeProgress)
        urlScrapy.signal_end.connect(self.terminateCrawl)
        return urlScrapy

    def openConfWindow(self):
        self.confWindow = ConfWindow(self.confDic)
        self.confWindow.signal_end.connect(self.confWindowClosed)
        self.confWindow.show()

    def confWindowClosed(self):
        # 更新当前配置
        confFilePath = os.path.join(os.getcwd(), self.confFileName)
        confDic = myUtils.readConfFile(confFilePath)
        headerList = confDic["confHeader"]
        reConfDic = {"confFilePath": confFilePath, "maxThreadCount": int(confDic[headerList[0]]),
                     "sensiveKeyList": confDic[headerList[1]], "filterList": confDic[headerList[2]],
                     "confHeaderList": headerList, "ifProxy": True if int(confDic[headerList[3]]) == 1 else False,
                     "proxyIp": confDic[headerList[4]], "proxyPort": confDic[headerList[5]],
                     "ifProxyUseHttps": True if int(confDic[headerList[6]]) == 1 else False,
                     "exportSaveCount": int(confDic[headerList[7]])}

        # 更新请求结果表格
        nowRowCount = self.tableWidget.rowCount()
        for index in range(nowRowCount):
            # 构建当前行数据字典
            dataDic = {}
            dataDic["url"] = self.tableWidget.item(index, 0).text()
            dataDic["status"] = self.tableWidget.item(index, 1).text()
            dataDic["title"] = self.tableWidget.item(index, 2).text()
            dataDic["contentLength"] = int(self.tableWidget.item(index, 3).text())
            reFlag = self.ifResultFilter(dataDic, reConfDic["filterList"])
            if reFlag:
                # 设置状态列
                self.tableWidget.item(index, 5).setText("0")
                # 设置当前行的背景色
                for colIndex in range(self.tableWidget.columnCount()):
                    self.tableWidget.item(index, colIndex).setBackground(QBrush(QColor(136, 136, 136)))
                # 设置是否显示当前行
                if self.checkBox.checkState() == 0:
                    ifHidden = True
                else:
                    ifHidden = False
                self.tableWidget.setRowHidden(index, ifHidden)
            else:
                # 设置状态列
                self.tableWidget.item(index, 5).setText("1")
                # 设置当前行的背景色
                for colIndex in range(self.tableWidget.columnCount()):
                    self.tableWidget.item(index, colIndex).setBackground(QBrush(QColor(255, 255, 255)))
                # 设置显示当前行
                self.tableWidget.setRowHidden(index, False)

        # 更新代理设置
        if reConfDic["ifProxy"]:
            proxyPro = "https" if reConfDic["ifProxyUseHttps"] else "http"
            proxyStr = "{0}://{1}:{2}".format(proxyPro, reConfDic["proxyIp"], reConfDic["proxyPort"])
            self.proxies = {"http": proxyStr, "https": proxyStr}
        else:
            self.proxies = None

        self.confDic = reConfDic

    def startCrawl(self):
        # 清空日志区域
        self.textEdit.setText("")
        # 获取最大线程数
        maxThreadCount = self.confDic["maxThreadCount"]
        # 获取初始URL
        nowUrlArr = [a for a in self.plainTextEdit.toPlainText().split("\n") if a != ""]
        nowExtraUrlArr = [a for a in self.extraUrlTextEdit.toPlainText().split("\n") if a != ""]
        if len(nowUrlArr) == 0:
            self.writeLog("请输入需要扫描的URL", color="red")
            return
        # 判断输入的URL是否符合URL格式
        for index, nowUrl in enumerate(nowUrlArr):
            if nowUrl == "" or not self.urlRegex.match(nowUrl):
                self.writeLog("输入的第{0}行URL格式不正确，请输入正确格式的URL".format(index + 1), color="red")
                return
        for index, nowUrl in enumerate(nowExtraUrlArr):
            if nowUrl == "" or not self.urlRegex.match(nowUrl):
                self.writeLog("输入的第{0}行额外URL格式不正确，请输入正确格式的URL".format(index + 1), color="red")
                return
        # 读取cookie
        nowCookie = self.cookiesTextEdit.toPlainText()
        nowCookie = nowCookie.strip(" ")
        nowCookieDic = {}
        if nowCookie != "":
            # 只取第一行
            nowCookie = nowCookie.split("\n")[0]
            tmpList = nowCookie.split(";")
            for tmpItem in tmpList:
                if tmpItem != "":
                    tmpItemList = tmpItem.split("=")
                    nowCookieDic[tmpItemList[0]] = "=".join(tmpItemList[1:])
                else:
                    continue
        else:
            pass

        # 读取headers
        nowHeaders = self.headersTextEdit.toPlainText()
        nowHeaders = nowHeaders.strip(" ")
        nowHeaderDic = {}
        headerRegexStr = "^[ ]*(?P<key>.+?)[ ]*:[ ]*(?P<value>.+?)[ ]*$"
        notUpdateHeaderKeys = []
        notUpdateHeaderKeys.append("cookie")
        notUpdateHeaderKeys.append("user-agent")
        if nowHeaders != "":
            # 按行读取
            nowHeaderList = nowHeaders.split("\n")
            for tmpHeaderIndex,tmpHeaderStr in enumerate(nowHeaderList):
                tmpRegexResult = re.search(headerRegexStr,tmpHeaderStr,re.I)
                if tmpRegexResult is not None:
                    tmpRegexResultDict = tmpRegexResult.groupdict()
                    tmpKey = tmpRegexResultDict["key"].strip()
                    tmpValue = tmpRegexResultDict["value"].strip()

                    # 判断是否是需要跳过的header key
                    ifUpdateFlag = True
                    for tmpNotUpdateKey in notUpdateHeaderKeys:
                        tmpKeyRegexResult = re.search(tmpNotUpdateKey,tmpKey,re.I)
                        if tmpKeyRegexResult is not None:
                            ifUpdateFlag = False
                            break
                        else:
                            continue

                    if ifUpdateFlag:
                        nowHeaderDic[tmpKey] = tmpValue
                    else:
                        continue
                else:
                    self.writeLog(f"输入的第{tmpHeaderIndex+1}行header格式错误，正确格式应为: key:value", color="red")
                    return
        else:
            pass

        # 读取不爬取接口
        nowUnvisitInterfaceUri = [urllib.parse.urlparse(a).path for a in self.unvisitInterfaceUriTextEdit.toPlainText().split("\n") if a != ""]

        # 读取User-Agent
        nowUserAgent = self.userAgentValTextEdit.toPlainText().strip()
        if nowUserAgent == "":
            self.writeLog("请选择或输入想使用的UA", color="red")
            return

        # 清空结果区域
        self.clearTable()
        self.clearTableSen()
        self.clearTableOther()
        self.saveOtherDomainResultList = []
        # 设置按钮状态
        self.pushButton.setEnabled(False)
        self.pushButton_2.setEnabled(True)

        self.urlScrapy = self.createCrawlObj(nowUrlArr, maxThreadCount, sensiveKeyList=self.confDic["sensiveKeyList"],
                                             extraUrlArr=nowExtraUrlArr, nowCookie=nowCookieDic, proxies=self.proxies,
                                             unvisitInterfaceUri=nowUnvisitInterfaceUri,userAgent=nowUserAgent,nowHeaders=nowHeaderDic)

        try:
            self.urlScrapy.start()
        except Exception as ex:
            self.writeLog(ex, color="red")

    def exportResult(self):
        exportSaveCount = int(self.confDic["exportSaveCount"])
        nowUrlResultCount = self.tableWidget.rowCount()
        nowSensiveResultCount = self.tableWidget_2.rowCount()
        nowOtherDomainResultCount = self.tableWidget_3.rowCount()
        if nowUrlResultCount == 0 and nowSensiveResultCount == 0 and nowOtherDomainResultCount == 0:
            self.writeLog("当前无可导出数据", color="red")
            return

        self.exportExcellThread = ExportExcellThread(self.tableWidget, self.tableWidget_2,self.tableWidget_3, exportSaveCount)
        self.exportExcellThread.signal_end.connect(self.exportCompleted)
        self.exportExcellThread.signal_log.connect(self.writeLog)
        self.exportExcellThread.start()
        self.writeLog("开始导出文件", color="blue")
        self.pushButton_3.setEnabled(False)

    def exportCompleted(self, result, logStr):
        if result:
            self.writeLog(logStr, color="blue")
        else:
            self.writeLog(logStr, color="red")
        self.pushButton_3.setEnabled(True)

    def clearTable(self):
        while self.tableWidget.rowCount() != 0:
            self.tableWidget.removeRow(self.tableWidget.rowCount() - 1)

    def clearTableSen(self):
        while self.tableWidget_2.rowCount() != 0:
            self.tableWidget_2.removeRow(self.tableWidget_2.rowCount() - 1)
    def clearTableOther(self):
        while self.tableWidget_3.rowCount() != 0:
            self.tableWidget_3.removeRow(self.tableWidget_3.rowCount() - 1)

    def terminateCrawl(self, ifAuto=False):
        self.pushButton.setEnabled(True)
        self.pushButton_2.setEnabled(False)
        self.urlScrapy.terminate()
        self.urlScrapy.quit()
        if not ifAuto:
            self.writeLog("")
            self.writeLog("扫描提前中断", color="red")
            self.writeProgress(0, 0, 0)

    def writeLog(self, log, color="black"):
        colorDic = {"black": "#000000", "red": "#FF0000", "yellow": "#FFFF00", "blue": "#0000FF"}
        log = '<font color="{0}" size="4">'.format(colorDic[color]) + log + "</font><br>"
        self.textEdit.moveCursor(QTextCursor.End)
        self.textEdit.insertHtml(log)
        self.textEdit.moveCursor(QTextCursor.End)

    def writeUrlResult(self, resultDicStr):
        resultDic = json.loads(resultDicStr)
        nowRowCount = self.tableWidget.rowCount()
        self.tableWidget.insertRow(nowRowCount)
        ifFilter = self.ifResultFilter(resultDic, self.confDic["filterList"])
        for index, tempKey in enumerate(self.urlResultDictKeyList):
            tempItem = QTableWidgetItem()
            if index != 3:
                tempItem.setText(str(resultDic[tempKey]))
            else:
                tempItem.setData(Qt.DisplayRole, int(resultDic[tempKey]))

            if ifFilter:
                tempItem.setBackground(QBrush(QColor(136, 136, 136)))
            else:
                pass
            self.tableWidget.setItem(nowRowCount, index, tempItem)
        tempItem = QTableWidgetItem()
        if ifFilter:
            tempItem.setText("0")
            ifHidden = True if self.checkBox.checkState() == 0 else False
            self.tableWidget.setRowHidden(nowRowCount, ifHidden)
        else:
            tempItem.setText("1")
        self.tableWidget.setItem(nowRowCount, 5, tempItem)

    # 判断请求结果是否要过滤，传入一个结果字典和判断条件列表，返回一个布尔值，若过滤则返回True，否则返回False
    def ifResultFilter(self, resultDic, filterConditonList):
        reFlag = False
        nowTitle = resultDic["title"]
        nowContentLength = int(resultDic["contentLength"])
        aimList = [nowTitle, nowContentLength]

        # 遍历过滤条件数组，判断是否要过滤
        for nowFilterConditonList in filterConditonList:
            nowFilterAimIndex = int(nowFilterConditonList[0])
            nowFilterConditonIndex = int(nowFilterConditonList[1])
            nowFilterValue = nowFilterConditonList[2]

            nowFilterAim = aimList[nowFilterAimIndex]

            # 构建判断字符串
            checkStr = ""
            if nowFilterConditonIndex == 2:
                checkStr = '"{0}" == "{1}"'.format(nowFilterAim, nowFilterValue)
            elif nowFilterConditonIndex == 3:
                checkStr = '"{0}" != "{1}"'.format(nowFilterAim, nowFilterValue)
            else:
                # 对于包长度，包含和不包含条件等同于等于和不等于，对于标题，正常判断
                if nowFilterAimIndex == 0:
                    if nowFilterConditonIndex == 0:
                        checkStr = '"{0}" in "{1}"'.format(nowFilterValue, nowFilterAim)
                    elif nowFilterConditonIndex == 1:
                        checkStr = '"{0}" not in "{1}"'.format(nowFilterValue, nowFilterAim)
                    else:
                        pass
                elif nowFilterAimIndex == 1:
                    if nowFilterConditonIndex == 0:
                        checkStr = '"{0}" == "{1}"'.format(nowFilterAim, nowFilterValue)
                    elif nowFilterConditonIndex == 1:
                        checkStr = '"{0}" != "{1}"'.format(nowFilterAim, nowFilterValue)
                    else:
                        pass
            tempFlag = eval(checkStr)
            if tempFlag:
                reFlag = True
                break
            else:
                pass
        return reFlag

    def ifShowFilterChnage(self, state):
        nowTableRowCount = self.tableWidget.rowCount()
        ifHidden = True
        if state == 2:
            # 显示过滤结果
            ifHidden = False
        else:
            # 不显示过滤结果
            ifHidden = True
        for index in range(nowTableRowCount):
            nowState = int(self.tableWidget.item(index, 5).text())
            if nowState == 0:
                self.tableWidget.setRowHidden(index, ifHidden)
            else:
                pass

    def writeSensiveResult(self, resultListStr):
        resultList = json.loads(resultListStr)
        nowRowCount = self.tableWidget_2.rowCount()
        for resultDic in resultList:
            self.tableWidget_2.insertRow(nowRowCount)
            for index, tempKey in enumerate(self.sensiveDictKeyList):
                tempItem = QTableWidgetItem(str(resultDic[tempKey]))
                self.tableWidget_2.setItem(nowRowCount, index, tempItem)

    def writeOtherDomainResult(self, resultListStr):
        resultList = json.loads(resultListStr)
        nowRowCount = self.tableWidget_3.rowCount()
        for resultDic in resultList:
            # 判断是否是已经写入过的数据
            tmpResultStr = json.dumps(resultDic)
            if tmpResultStr in self.saveOtherDomainResultList:
                continue
            else:
                self.tableWidget_3.insertRow(nowRowCount)
                for index, tempKey in enumerate(self.otherDomainResultDictKeyList):
                    tempItem = QTableWidgetItem(str(resultDic[tempKey]))
                    self.tableWidget_3.setItem(nowRowCount, index, tempItem)
                self.saveOtherDomainResultList.append(tmpResultStr)

    def writeProgress(self, visitedCount, remainCount, threadCount):
        log = "有{0}个线程正在访问URL，当前已完成{1}个URL的访问，还有{2}个URL需要访问".format(threadCount, visitedCount, remainCount)
        self.lineEdit_2.setText(log)

    def selectUrlFromFile(self):
        fileName, fileType = QFileDialog.getOpenFileName(self, "批量导入URL", QDir.currentPath(), "TXT Files (*.txt)")
        readStr = ""
        if fileName != "":
            with open(fileName, "r", encoding="utf-8") as fr:
                readStr = fr.read()
            readStr.replace("\r\n", "\n")

            self.plainTextEdit.setPlainText(readStr)
        else:
            pass

    def userAgentModelChange(self,modelIndex):
        nowSelectUserAgent = self.userAgentDic[modelIndex]
        self.userAgentValTextEdit.setPlainText(nowSelectUserAgent)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainForm = Main()
    mainForm.show()
    sys.exit(app.exec_())
