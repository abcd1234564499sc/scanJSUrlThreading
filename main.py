#!/usr/bin/env python
# coding=utf-8
import json
import re
import sys
import warnings

import openpyxl as oxl
from PyQt5.QtCore import QDir
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication, QWidget, QHeaderView, QTableWidgetItem, QFileDialog

import myUtils
from UrlScrapyManage import UrlScrapyManage
from ui.ui_main import Ui_Main_Form


class Main(QWidget, Ui_Main_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(["URL", "响应码", "标题"])
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tableWidget.setColumnWidth(1, 60)
        self.urlRegex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        self.urlScrapy = None
        warnings.filterwarnings("ignore")

    def createCrawlObj(self, scrawlUrlArr=[], maxThreadCount=50):
        urlScrapy = UrlScrapyManage(scrawlUrlArr=scrawlUrlArr, maxThreadCount=maxThreadCount)
        urlScrapy.signal_log[str].connect(self.writeLog)
        urlScrapy.signal_log[str, str].connect(self.writeLog)
        urlScrapy.signal_result.connect(self.writeResult)
        urlScrapy.signal_progress.connect(self.writeProgress)
        urlScrapy.signal_end.connect(self.terminateCrawl)
        return urlScrapy

    def startCrawl(self):
        # 清空日志区域
        self.textEdit.setText("")
        # 获取最大线程数
        maxThreadCount = self.lineEdit.text()
        # 判断输入线程数是否为正整数
        if maxThreadCount.isdigit():
            maxThreadCount = int(maxThreadCount)
        else:
            self.writeLog("输入的最大线程数必须为一个正整数", color="red")
            return
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
        headArr = ["序号", "URL", "响应码", "标题"]
        myUtils.writeExcellHead(ws, headArr)

        # 遍历当前结果
        for rowIndex in range(nowCount):
            # 获取当前行的值
            nowUrl = self.tableWidget.item(rowIndex, 0).text()
            nowStatus = self.tableWidget.item(rowIndex, 1).text()
            nowTitle = self.tableWidget.item(rowIndex, 2).text()

            # 将值写入excell对象
            myUtils.writeExcellCell(ws, rowIndex + 2, 1, rowIndex + 1, 0, True)
            myUtils.writeExcellCell(ws, rowIndex + 2, 2, nowUrl, 0, False, hyperLink=nowUrl)
            myUtils.writeExcellCell(ws, rowIndex + 2, 3, nowStatus, 0, True)
            myUtils.writeExcellCell(ws, rowIndex + 2, 4, nowTitle, 0, True)
            myUtils.writeExcellSpaceCell(ws, rowIndex + 2, 5)

        # 设置列宽
        colWidthArr = [7, 70, 7, 60]
        myUtils.setExcellColWidth(ws, colWidthArr)

        # 保存文件
        myUtils.saveExcell(wb, saveName=filename)
        self.writeLog("")
        self.writeLog("成功保存文件：{0}.xlsx 至当前文件夹".format(filename), color="blue")

    def clearTable(self):
        while self.tableWidget.rowCount() != 0:
            self.tableWidget.removeRow(self.tableWidget.rowCount() - 1)

    def terminateCrawl(self):
        self.pushButton.setEnabled(True)
        self.pushButton_2.setEnabled(False)
        self.urlScrapy.terminate()
        self.urlScrapy.quit()
        self.writeLog("")
        self.writeLog("扫描提前中断", color="red")
        self.writeProgress(0, 0, 0)

    def writeLog(self, log, color="black"):
        colorDic = {"black": "#000000", "red": "#FF0000", "yellow": "#FFFF00", "blue": "#0000FF"}
        log = '<font color="{0}" size="4">'.format(colorDic[color]) + log + "</font><br>"
        self.textEdit.moveCursor(QTextCursor.End)
        self.textEdit.insertHtml(log)
        self.textEdit.moveCursor(QTextCursor.End)

    def writeResult(self, resultDicStr):
        resultDic = json.loads(resultDicStr)
        nowRowCount = self.tableWidget.rowCount()
        self.tableWidget.insertRow(nowRowCount)
        for index, tempKey in enumerate(resultDic.keys()):
            tempItem = QTableWidgetItem(str(resultDic[tempKey]))
            self.tableWidget.setItem(nowRowCount, index, tempItem)

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
