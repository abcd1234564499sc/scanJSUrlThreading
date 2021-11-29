#!/usr/bin/env python
# coding=utf-8
import json
import os
import re
import sys
import warnings

import openpyxl as oxl
from PyQt5.QtCore import QDir
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor, QBrush, QColor
from PyQt5.QtWidgets import QApplication, QWidget, QHeaderView, QTableWidgetItem, QFileDialog

import myUtils
from ConfWinodw import ConfWindow
from UrlScrapyManage import UrlScrapyManage
from ui.ui_main import Ui_Main_Form


class Main(QWidget, Ui_Main_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setHorizontalHeaderLabels(["URL", "响应码", "标题", "包长度"])
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tableWidget.setColumnWidth(1, 60)
        self.tableWidget.hideColumn(4)
        self.tableWidget_2.setColumnCount(3)
        self.tableWidget_2.setHorizontalHeaderLabels(["URL", "关键词", "敏感信息"])
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tableWidget_2.setColumnWidth(1, 100)
        self.urlRegex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        self.urlScrapy = None
        self.confFileName = "扫描器配置.conf"
        self.confHeadList = ["最大线程数", "敏感信息关键词列表", "过滤信息列表"]
        warnings.filterwarnings("ignore")
        self.confDic = self.initConfFile()
        self.confWindow = ConfWindow(self.confDic)

    # 初始化配置文件，生成配置文件并返回一个配置字典
    # 字典结构为：{
    # "confFileName":配置文件文件名,
    # "maxThreadCount":最大线程数,
    # "sensiveKeyList":敏感信息关键词列表,
    # "filterList":过滤条件列表，列表内容为一个包含3个元素的列表，3个元素分别是：
    #       过滤项：0代表标题，1代表包长度
    #       过滤条件：0代表包含，1代表不包含，2代表等于，3代表不等于
    #       过滤值,
    # "confHeaderList":配置名列表
    # }
    def initConfFile(self):
        defaultMaxThreadCount = 50
        defaultSensiveKeyList = ["默认密码", "默认账号", "默认用户名", "default username", "default password"]
        defaultFilterList = []
        defaultConfHeaderList = self.confHeadList
        confDic = {defaultConfHeaderList[0]: defaultMaxThreadCount, defaultConfHeaderList[1]: defaultSensiveKeyList,
                   defaultConfHeaderList[2]: defaultFilterList, "confHeader": defaultConfHeaderList}

        # 判断是否存在配置文件
        confFilePath = os.path.join(os.getcwd(), self.confFileName)
        if not os.path.exists(confFilePath):
            myUtils.writeToConfFile(confFilePath, confDic)
        else:
            confDic = myUtils.readConfFile(confFilePath)
        headerList = confDic["confHeader"]

        reConfDic = {"confFilePath": confFilePath, "maxThreadCount": int(confDic[headerList[0]]),
                     "sensiveKeyList": confDic[headerList[1]], "filterList": confDic[headerList[2]],
                     "confHeaderList": headerList}
        return reConfDic

    def createCrawlObj(self, scrawlUrlArr=[], maxThreadCount=50, sensiveKeyList=[]):
        urlScrapy = UrlScrapyManage(scrawlUrlArr=scrawlUrlArr, maxThreadCount=maxThreadCount,
                                    sensiveKeyList=sensiveKeyList)
        urlScrapy.signal_log[str].connect(self.writeLog)
        urlScrapy.signal_log[str, str].connect(self.writeLog)
        urlScrapy.signal_url_result.connect(self.writeUrlResult)
        urlScrapy.signal_sensive_result.connect(self.writeSensiveResult)
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
                     "confHeaderList": headerList}
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
                self.tableWidget.item(index, 4).setText("0")
                # 设置当前行的背景色
                for colIndex in range(self.tableWidget.columnCount()):
                    self.tableWidget.item(index,colIndex).setBackground(QBrush(QColor(136, 136, 136)))
                # 设置是否显示当前行
                if self.checkBox.checkState() == 0:
                    ifHidden = True
                else:
                    ifHidden = False
                self.tableWidget.setRowHidden(index, ifHidden)
            else:
                # 设置状态列
                self.tableWidget.item(index, 4).setText("1")
                # 设置当前行的背景色
                for colIndex in range(self.tableWidget.columnCount()):
                    self.tableWidget.item(index,colIndex).setBackground(QBrush(QColor(255,255,255)))
                # 设置显示当前行
                self.tableWidget.setRowHidden(index,False)
        self.confDic = reConfDic

    def startCrawl(self):
        # 清空日志区域
        self.textEdit.setText("")
        # 获取最大线程数
        maxThreadCount = self.confDic["maxThreadCount"]
        # 获取初始URL
        nowUrlArr = [a for a in self.plainTextEdit.toPlainText().split("\n") if a != ""]
        if len(nowUrlArr) == 0:
            self.writeLog("请输入需要扫描的URL", color="red")
            return
        # 判断输入的URL是否符合URL格式
        for index, nowUrl in enumerate(nowUrlArr):
            if nowUrl == "" or not self.urlRegex.match(nowUrl):
                self.writeLog("输入的第{0}行URL格式不正确，请输入正确格式的URL".format(index + 1), color="red")
                return
        # 清空结果区域
        self.clearTable()
        # 设置按钮状态
        self.pushButton.setEnabled(False)
        self.pushButton_2.setEnabled(True)

        self.urlScrapy = self.createCrawlObj(nowUrlArr, maxThreadCount)

        try:
            self.urlScrapy.start()
        except Exception as ex:
            self.writeLog(ex, color="red")

    def exportResult(self):
        nowCount = self.tableWidget.rowCount()
        if nowCount == 0:
            self.writeLog("当前无可导出数据", color="red")
            return
        filename = "导出文件-" + myUtils.getNowSeconed().replace("-", "").replace(" ", "").replace(":", "")
        # 创建一个excell文件对象
        wb = oxl.Workbook()
        ws = wb.active
        ws.title = "URL扫描结果"
        # 创建表头
        headArr = ["序号", "URL", "响应码", "标题", "包长度", "状态"]
        myUtils.writeExcellHead(ws, headArr)

        # 遍历当前结果
        for rowIndex in range(nowCount):
            # 获取当前行的值
            nowUrl = self.tableWidget.item(rowIndex, 0).text()
            nowStatus = self.tableWidget.item(rowIndex, 1).text()
            nowTitle = self.tableWidget.item(rowIndex, 2).text()
            nowContentLength = self.tableWidget.item(rowIndex, 3).text()
            nowState = "被过滤" if int(self.tableWidget.item(rowIndex, 4).text()) == 0 else "正常"

            # 将值写入excell对象
            myUtils.writeExcellCell(ws, rowIndex + 2, 1, rowIndex + 1, 0, True)
            myUtils.writeExcellCell(ws, rowIndex + 2, 2, nowUrl, 0, False, hyperLink=nowUrl)
            myUtils.writeExcellCell(ws, rowIndex + 2, 3, nowStatus, 0, True)
            myUtils.writeExcellCell(ws, rowIndex + 2, 4, nowTitle, 0, False)
            myUtils.writeExcellCell(ws, rowIndex + 2, 5, nowContentLength, 0, False)
            myUtils.writeExcellCell(ws, rowIndex + 2, 6, nowState, 0, True)
            myUtils.writeExcellSpaceCell(ws, rowIndex + 2, 7)

        # 设置列宽
        colWidthArr = [7, 70, 7, 60, 10, 10]
        myUtils.setExcellColWidth(ws, colWidthArr)

        # 保存文件
        myUtils.saveExcell(wb, saveName=filename)
        self.writeLog("")
        self.writeLog("成功保存文件：{0}.xlsx 至当前文件夹".format(filename), color="blue")

    def clearTable(self):
        while self.tableWidget.rowCount() != 0:
            self.tableWidget.removeRow(self.tableWidget.rowCount() - 1)

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
        for index, tempKey in enumerate(resultDic.keys()):
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
        self.tableWidget.setItem(nowRowCount, 4, tempItem)

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
            nowState = int(self.tableWidget.item(index, 4).text())
            if nowState == 0:
                self.tableWidget.setRowHidden(index, ifHidden)
            else:
                pass

    def writeSensiveResult(self, resultListStr):
        resultList = json.loads(resultListStr)
        nowRowCount = self.tableWidget_2.rowCount()
        for resultDic in resultList:
            self.tableWidget_2.insertRow(nowRowCount)
            for index, tempKey in enumerate(resultDic.keys()):
                tempItem = QTableWidgetItem(str(resultDic[tempKey]))
                self.tableWidget_2.setItem(nowRowCount, index, tempItem)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainForm = Main()
    mainForm.show()
    sys.exit(app.exec_())
