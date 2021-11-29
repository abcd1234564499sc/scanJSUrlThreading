#!/usr/bin/env python
# coding=utf-8

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog, QHeaderView, QTableWidgetItem, QMessageBox, QComboBox

import myUtils
from ui.ui_conf import Ui_Dialog


class ConfWindow(QDialog, Ui_Dialog):
    signal_end = pyqtSignal()

    def __init__(self, confDic):
        super().__init__()
        self.setupUi(self)
        # 根据传入的参数初始化数据
        self.confFilePath = confDic["confFilePath"]
        self.maxThreadCount = confDic["maxThreadCount"]
        self.sensiveKeyList = confDic["sensiveKeyList"]
        self.filterList = confDic["filterList"]
        self.confHeadList = confDic["confHeaderList"]

        # 初始化最大线程数
        self.lineEdit.setText(str(self.maxThreadCount))

        # 初始化敏感信息关键词列表
        self.tableWidget.setColumnCount(1)
        self.tableWidget.setHorizontalHeaderLabels(["敏感信息关键词"])
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tempNowCount = 0
        for index, sensiveKey in enumerate(self.sensiveKeyList):
            tempItem = QTableWidgetItem(str(sensiveKey))
            self.tableWidget.insertRow(tempNowCount)
            self.tableWidget.setItem(tempNowCount, 0, tempItem)
            tempNowCount = tempNowCount + 1

        # 初始化过滤条件
        self.tableWidget1.setColumnCount(3)
        self.tableWidget1.setHorizontalHeaderLabels(["过滤项", "过滤条件", "过滤值"])
        self.tableWidget1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tempNowCount = 0
        for index, filterItem in enumerate(self.filterList):
            self.tableWidget1.insertRow(tempNowCount)
            filterAimIndex = int(filterItem[0])
            filterConditionIndex = int(filterItem[1])
            filterValue = filterItem[2]
            # 创建一个过滤项下拉框
            filterAimCbx = QComboBox()
            filterAimCbx.addItem("标题", 0)
            filterAimCbx.addItem("包长度", 1)
            filterAimCbx.setCurrentIndex(filterAimIndex)
            self.tableWidget1.setCellWidget(tempNowCount, 0, filterAimCbx)

            # 创建一个过滤条件下拉框
            filterConditionCbx = QComboBox()
            filterConditionCbx.addItem("包含", 0)
            filterConditionCbx.addItem("不包含", 1)
            filterConditionCbx.addItem("等于", 2)
            filterConditionCbx.addItem("不等于", 3)
            filterConditionCbx.setCurrentIndex(filterConditionIndex)
            self.tableWidget1.setCellWidget(tempNowCount, 1, filterConditionCbx)

            # 创建一个过滤值项
            tempItem = QTableWidgetItem(str(filterValue))
            self.tableWidget1.setItem(tempNowCount, 2, tempItem)
            tempNowCount = tempNowCount + 1

    def saveConf(self):
        # 读取当前配置值
        nowMaxThreadCount = self.lineEdit.text()
        # 验证输入值是否符合规则
        if not nowMaxThreadCount.isdigit():
            warningStr = "最大线程数必须是一个正整数"
            self.writeWarning(warningStr)
            return
        # 读取当前敏感信息关键词
        nowSensiveKeyList = []
        nowRowCount = self.tableWidget.rowCount()
        for index in range(nowRowCount):
            tempItem = self.tableWidget.item(index, 0)
            if tempItem is None or tempItem.text == "":
                warningStr = "敏感信息关键词列表第{0}行数据为空".format(index + 1)
                self.writeWarning(warningStr)
                return
            else:
                tempItemText = tempItem.text()
                nowSensiveKeyList.append(tempItemText)
        # 读取当前过滤条件列表
        nowFilterList = []
        nowRowCount = self.tableWidget1.rowCount()
        for index in range(nowRowCount):
            nowFilterAim = int(self.tableWidget1.cellWidget(index, 0).currentData())
            nowFilterCondition = int(self.tableWidget1.cellWidget(index, 1).currentData())
            nowFilterValueItem = self.tableWidget1.item(index, 2)
            if nowFilterValueItem is None or nowFilterValueItem.text() == "":
                warningStr = "扫描结果过滤列表第{0}行数据为空".format(index + 1)
                self.writeWarning(warningStr)
                return
            else:
                nowFilterValue = nowFilterValueItem.text()
                nowFilterList.append([nowFilterAim, nowFilterCondition, nowFilterValue])

        # 生成字典
        confDic = {self.confHeadList[0]: nowMaxThreadCount, self.confHeadList[1]: nowSensiveKeyList,
                   self.confHeadList[2]: nowFilterList}

        # 保存到配置文件
        myUtils.writeToConfFile(self.confFilePath, confDic)

        self.writeWarning("保存成功")
        self.signal_end.emit()
        self.close()

    def addSensiveKey(self):
        nowRowCount = self.tableWidget.rowCount()
        # 判断最后一行是否是空行
        endRowItem = self.tableWidget.item(nowRowCount - 1, 0)
        if endRowItem is not None:
            self.tableWidget.insertRow(nowRowCount)
            self.tableWidget.scrollToBottom()

    def removeSensiveKey(self):
        selectItems = self.tableWidget.selectedItems()
        selectItems = sorted(selectItems, key=lambda x: self.tableWidget.indexFromItem(x), reverse=True)
        if len(selectItems) == 0:
            return
        answer = QMessageBox.question(self, '确认', '确认要删除{0}行敏感信息关键词？'.format(len(selectItems)),
                                      QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            for selectItem in selectItems:
                self.tableWidget.removeRow(self.tableWidget.indexFromItem(selectItem).row())

    def addFilter(self):
        nowRowCount = self.tableWidget1.rowCount()
        # 判断最后一行是否写有数据
        endRowItem = self.tableWidget1.item(nowRowCount - 1, 2)
        if nowRowCount == 0 or endRowItem is not None:
            self.tableWidget1.insertRow(nowRowCount)
            # 创建一个过滤项下拉框
            filterAimCbx = QComboBox()
            filterAimCbx.addItem("标题", 0)
            filterAimCbx.addItem("包长度", 1)
            self.tableWidget1.setCellWidget(nowRowCount, 0, filterAimCbx)

            # 创建一个过滤条件下拉框
            filterConditionCbx = QComboBox()
            filterConditionCbx.addItem("包含", 0)
            filterConditionCbx.addItem("不包含", 1)
            filterConditionCbx.addItem("等于", 2)
            filterConditionCbx.addItem("不等于", 3)
            self.tableWidget1.setCellWidget(nowRowCount, 1, filterConditionCbx)
            self.tableWidget1.scrollToBottom()

    def removeFilter(self):
        selectItems = self.tableWidget1.selectedItems()
        selectItems = sorted(selectItems, key=lambda x: self.tableWidget1.indexFromItem(x), reverse=True)
        if len(selectItems) == 0:
            return
        answer = QMessageBox.question(self, '确认', '确认要删除{0}行过滤条件？'.format(len(selectItems)),
                                      QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            for selectItem in selectItems:
                self.tableWidget1.removeRow(self.tableWidget1.indexFromItem(selectItem).row())

    def writeWarning(self, warningStr):
        self.label_5.setText(warningStr)
