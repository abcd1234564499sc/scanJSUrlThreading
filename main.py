#!/usr/bin/env python
# coding=utf-8
import json
import re
import sys

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

    def createCrawlObj(self, scrawlUrlArr=[]):
        urlScrapy = UrlScrapyManage(scrawlUrlArr=scrawlUrlArr)
        urlScrapy.signal_log[str].connect(self.writeLog)
        urlScrapy.signal_log[str, str].connect(self.writeLog)
        urlScrapy.signal_result.connect(self.writeResult)
        urlScrapy.signal_progress.connect(self.writeProgress)
        urlScrapy.signal_end.connect(self.terminateCrawl)
        return urlScrapy

    def startCrawl(self):
        nowUrlArr = [a for a in self.plainTextEdit.toPlainText().split("\n") if a != ""]
        self.textEdit.setText("")
        for index, nowUrl in enumerate(nowUrlArr):
            if nowUrl == "" or not self.urlRegex.match(nowUrl):
                self.writeLog("输入的第{0}行URL格式不正确，请输入正确格式的URL".format(index + 1), color="red")
                return
        self.clearTable()
        self.pushButton.setEnabled(False)
        self.pushButton_2.setEnabled(True)

        self.urlScrapy = self.createCrawlObj(nowUrlArr)

        try:
            self.urlScrapy.start()
        except Exception as ex:
            self.writeLog(ex, color="red")

    def exportResult(self):
        nowCount = self.tableWidget.rowCount()
        if nowCount == 0:
            self.writeLog("当前无可导出数据", color="red")
            return
        filename = "导出文件-" + myUtils.getNowSeconed().replace("-", "").replace(" ", "").replace(":", "") + ".csv"
        # 遍历当前表格
        with open(filename, "w+", encoding="utf-8") as fr:
            fr.write("序号,URL,响应码,标题\n")
            for rowIndex in range(nowCount):
                nowUrl = self.tableWidget.item(rowIndex, 0).text()
                nowStatus = self.tableWidget.item(rowIndex, 1).text()
                nowTitle = self.tableWidget.item(rowIndex, 2).text()
                fr.write("{0},{1},{2},{3}\n".format(rowIndex + 1, nowUrl, nowStatus, nowTitle))
        self.writeLog("成功生成文件：" + filename)

    def clearTable(self):
        while self.tableWidget.rowCount() != 0:
            self.tableWidget.removeRow(self.tableWidget.rowCount() - 1)

    def terminateCrawl(self):
        self.pushButton.setEnabled(True)
        self.pushButton_2.setEnabled(False)
        self.urlScrapy.terminate()
        self.urlScrapy.quit()

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
        log = "有{0}个线程正在访问URL，当前已完成{1}个URL的访问，还有{2}个URL需要访问".format(threadCount,visitedCount, remainCount)
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
