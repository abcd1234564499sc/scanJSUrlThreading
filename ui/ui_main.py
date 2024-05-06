# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_main.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Main_Form(object):
    def setupUi(self, Main_Form):
        Main_Form.setObjectName("Main_Form")
        Main_Form.resize(1027, 843)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/图片/icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Main_Form.setWindowIcon(icon)
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(Main_Form)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(Main_Form)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_7 = QtWidgets.QLabel(Main_Form)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.label_7.setFont(font)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 1, 0, 1, 1)
        self.unvisitInterfaceUriTextEdit = QtWidgets.QPlainTextEdit(Main_Form)
        self.unvisitInterfaceUriTextEdit.setObjectName("unvisitInterfaceUriTextEdit")
        self.gridLayout.addWidget(self.unvisitInterfaceUriTextEdit, 1, 4, 1, 1)
        self.cookiesTextEdit = QtWidgets.QTextEdit(Main_Form)
        self.cookiesTextEdit.setObjectName("cookiesTextEdit")
        self.gridLayout.addWidget(self.cookiesTextEdit, 1, 1, 1, 2)
        self.label_6 = QtWidgets.QLabel(Main_Form)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.label_6.setFont(font)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 0, 3, 1, 1)
        self.plainTextEdit = QtWidgets.QPlainTextEdit(Main_Form)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.gridLayout.addWidget(self.plainTextEdit, 0, 1, 1, 2)
        self.label_10 = QtWidgets.QLabel(Main_Form)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.label_10.setFont(font)
        self.label_10.setObjectName("label_10")
        self.gridLayout.addWidget(self.label_10, 2, 3, 1, 1)
        self.extraUrlTextEdit = QtWidgets.QPlainTextEdit(Main_Form)
        self.extraUrlTextEdit.setObjectName("extraUrlTextEdit")
        self.gridLayout.addWidget(self.extraUrlTextEdit, 0, 4, 1, 1)
        self.userAgentValTextEdit = QtWidgets.QPlainTextEdit(Main_Form)
        self.userAgentValTextEdit.setObjectName("userAgentValTextEdit")
        self.gridLayout.addWidget(self.userAgentValTextEdit, 2, 4, 1, 1)
        self.label_8 = QtWidgets.QLabel(Main_Form)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.label_8.setFont(font)
        self.label_8.setObjectName("label_8")
        self.gridLayout.addWidget(self.label_8, 1, 3, 1, 1)
        self.label_9 = QtWidgets.QLabel(Main_Form)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.label_9.setFont(font)
        self.label_9.setObjectName("label_9")
        self.gridLayout.addWidget(self.label_9, 2, 0, 1, 1)
        self.userAgentModelComboBox = QtWidgets.QComboBox(Main_Form)
        self.userAgentModelComboBox.setObjectName("userAgentModelComboBox")
        self.userAgentModelComboBox.addItem("")
        self.userAgentModelComboBox.addItem("")
        self.userAgentModelComboBox.addItem("")
        self.gridLayout.addWidget(self.userAgentModelComboBox, 2, 1, 1, 2)
        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 4)
        self.gridLayout.setColumnStretch(3, 1)
        self.gridLayout.setColumnStretch(4, 4)
        self.horizontalLayout_2.addLayout(self.gridLayout)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.pushButton_4 = QtWidgets.QPushButton(Main_Form)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/图片/打开文件.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_4.setIcon(icon1)
        self.pushButton_4.setObjectName("pushButton_4")
        self.verticalLayout_3.addWidget(self.pushButton_4)
        self.pushButton = QtWidgets.QPushButton(Main_Form)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/图片/开始.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon2)
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout_3.addWidget(self.pushButton)
        self.pushButton_2 = QtWidgets.QPushButton(Main_Form)
        self.pushButton_2.setEnabled(False)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/图片/中止.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_2.setIcon(icon3)
        self.pushButton_2.setObjectName("pushButton_2")
        self.verticalLayout_3.addWidget(self.pushButton_2)
        self.pushButton_5 = QtWidgets.QPushButton(Main_Form)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/图片/设置.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_5.setIcon(icon4)
        self.pushButton_5.setObjectName("pushButton_5")
        self.verticalLayout_3.addWidget(self.pushButton_5)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem)
        self.horizontalLayout_2.addLayout(self.verticalLayout_3)
        self.verticalLayout_5.addLayout(self.horizontalLayout_2)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_2 = QtWidgets.QLabel(Main_Form)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_2.addWidget(self.label_2, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        self.textEdit = QtWidgets.QTextEdit(Main_Form)
        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName("textEdit")
        self.verticalLayout_2.addWidget(self.textEdit)
        self.verticalLayout_5.addLayout(self.verticalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_3 = QtWidgets.QLabel(Main_Form)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.verticalLayout.addWidget(self.label_3, 0, QtCore.Qt.AlignHCenter)
        self.tableWidget = QtWidgets.QTableWidget(Main_Form)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.verticalLayout.addWidget(self.tableWidget)
        self.checkBox = QtWidgets.QCheckBox(Main_Form)
        self.checkBox.setObjectName("checkBox")
        self.verticalLayout.addWidget(self.checkBox, 0, QtCore.Qt.AlignRight)
        self.horizontalLayout_3.addLayout(self.verticalLayout)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.label_5 = QtWidgets.QLabel(Main_Form)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        font.setBold(False)
        font.setWeight(50)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.verticalLayout_4.addWidget(self.label_5, 0, QtCore.Qt.AlignHCenter)
        self.tableWidget_2 = QtWidgets.QTableWidget(Main_Form)
        self.tableWidget_2.setObjectName("tableWidget_2")
        self.tableWidget_2.setColumnCount(0)
        self.tableWidget_2.setRowCount(0)
        self.verticalLayout_4.addWidget(self.tableWidget_2)
        self.label_4 = QtWidgets.QLabel(Main_Form)
        self.label_4.setText("")
        self.label_4.setObjectName("label_4")
        self.verticalLayout_4.addWidget(self.label_4)
        self.horizontalLayout_3.addLayout(self.verticalLayout_4)
        self.verticalLayout_5.addLayout(self.horizontalLayout_3)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEdit_2 = QtWidgets.QLineEdit(Main_Form)
        self.lineEdit_2.setReadOnly(True)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.horizontalLayout.addWidget(self.lineEdit_2)
        self.pushButton_3 = QtWidgets.QPushButton(Main_Form)
        self.pushButton_3.setEnabled(True)
        self.pushButton_3.setObjectName("pushButton_3")
        self.horizontalLayout.addWidget(self.pushButton_3)
        self.verticalLayout_5.addLayout(self.horizontalLayout)
        self.verticalLayout_5.setStretch(0, 2)
        self.verticalLayout_5.setStretch(1, 2)
        self.verticalLayout_5.setStretch(2, 4)

        self.retranslateUi(Main_Form)
        self.pushButton.clicked.connect(Main_Form.startCrawl) # type: ignore
        self.pushButton_2.clicked.connect(Main_Form.terminateCrawl) # type: ignore
        self.pushButton_3.clicked.connect(Main_Form.exportResult) # type: ignore
        self.pushButton_4.clicked.connect(Main_Form.selectUrlFromFile) # type: ignore
        self.pushButton_5.clicked.connect(Main_Form.openConfWindow) # type: ignore
        self.checkBox.stateChanged['int'].connect(Main_Form.ifShowFilterChnage) # type: ignore
        self.userAgentModelComboBox.currentIndexChanged['int'].connect(Main_Form.userAgentModelChange) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Main_Form)

    def retranslateUi(self, Main_Form):
        _translate = QtCore.QCoreApplication.translate
        Main_Form.setWindowTitle(_translate("Main_Form", "JS中URL扫描器"))
        self.label.setText(_translate("Main_Form", "目标地址"))
        self.label_7.setText(_translate("Main_Form", "  Cookie  "))
        self.unvisitInterfaceUriTextEdit.setPlaceholderText(_translate("Main_Form", "填写程序不应该请求的接口，比如退出登录接口，接口格式为：/loginout，一行填写一个接口"))
        self.cookiesTextEdit.setPlaceholderText(_translate("Main_Form", "输入报文中的cookie字段，例：报文为：Cookie:uuid=123456; d_c0=456789,则在此处输入 uuid=123456; d_c0=456789，留空则不使用cookie"))
        self.label_6.setText(_translate("Main_Form", "额外地址"))
        self.plainTextEdit.setPlaceholderText(_translate("Main_Form", "填写要爬取接口的地址，多个地址一行填写一个"))
        self.label_10.setText(_translate("Main_Form", "UA值"))
        self.extraUrlTextEdit.setPlaceholderText(_translate("Main_Form", "填写需要与找到接口进行拼接的其他地址，该地址不会爬取其中的接口，但会将其与目的地址中爬取到的接口进行拼接后请求"))
        self.userAgentValTextEdit.setPlainText(_translate("Main_Form", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"))
        self.userAgentValTextEdit.setPlaceholderText(_translate("Main_Form", "填写请求使用的User-Agent，可通过UA模板下拉框使用内置模板"))
        self.label_8.setText(_translate("Main_Form", "不访问接口"))
        self.label_9.setText(_translate("Main_Form", "UA模板"))
        self.userAgentModelComboBox.setItemText(0, _translate("Main_Form", "chrome"))
        self.userAgentModelComboBox.setItemText(1, _translate("Main_Form", "firefox"))
        self.userAgentModelComboBox.setItemText(2, _translate("Main_Form", "ie"))
        self.pushButton_4.setText(_translate("Main_Form", "文件导入"))
        self.pushButton.setText(_translate("Main_Form", "开始运行"))
        self.pushButton_2.setText(_translate("Main_Form", "中止运行"))
        self.pushButton_5.setText(_translate("Main_Form", "配置"))
        self.label_2.setText(_translate("Main_Form", "运行日志"))
        self.label_3.setText(_translate("Main_Form", "请求结果"))
        self.tableWidget.setSortingEnabled(True)
        self.checkBox.setText(_translate("Main_Form", "显示过滤内容"))
        self.label_5.setText(_translate("Main_Form", "敏感信息"))
        self.tableWidget_2.setSortingEnabled(True)
        self.pushButton_3.setText(_translate("Main_Form", "导出结果"))
import resource.source_rc
