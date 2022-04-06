#!/usr/bin/env python
# coding=utf-8
from PyQt5.QtCore import QThread, pyqtSignal

import myUtils


class ConnectProxy(QThread):
    signal_result = pyqtSignal(bool)

    def __init__(self, ip="", port="", parent=None):
        super(ConnectProxy, self).__init__(parent)
        self.ip = ip
        self.port = port

    def run(self):
        connectResult = myUtils.connectIpPort(self.ip, int(self.port))
        self.signal_result.emit(connectResult)
