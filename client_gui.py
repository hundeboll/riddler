#!/usr/bin/env python2

import sys
import os
os.environ["QT_API"] = "pyside"

from PySide.QtCore import *
from PySide.QtGui import *
import matplotlib
matplotlib.use('Qt4Agg')

import client_live_monitor as live_monitor
import client_test_monitor as test_monitor


class main_window(QMainWindow):
    def __init__(self, parent=None):
        super(main_window, self).__init__(parent)
        self.setWindowTitle("Riddler Client")

        self.test_monitor = test_monitor.monitor(parent=self)
        self.live_monitor = live_monitor.monitor(parent=self)

        tabs = QTabWidget()
        tabs.addTab(self.live_monitor.gui, self.tr("Live Monitor"))
        tabs.addTab(self.test_monitor.gui, self.tr("Test Monitor"))

        vbox = QVBoxLayout()
        vbox.addWidget(tabs)

        widget = QWidget()
        widget.setLayout(vbox)
        self.setCentralWidget(widget)

        self.setMinimumSize(160,160)
        self.resize(640,480)
        self.show()


if __name__ == "__main__":
    a = QApplication(sys.argv)
    f = main_window()
    a.exec_()
