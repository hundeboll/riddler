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
import client_control as control


class main_window(QMainWindow):
    def __init__(self, parent=None):
        super(main_window, self).__init__(parent)
        self.setWindowTitle("Riddler Client")

        self.test_monitor = test_monitor.monitor(parent=self)
        self.live_monitor = live_monitor.monitor(parent=self)
        self.control = control.control(parent=self)

        menu = self.menuBar().addMenu("File")
        status = self.statusBar()

        self.addToolBar(self.control.toolbar)
        self.addToolBar(self.live_monitor.gui.toolbar)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        tabs = QTabWidget()
        tabs.addTab(self.control, self.tr("Control"))
        tabs.addTab(self.live_monitor.gui, self.tr("Live Monitor"))
        tabs.addTab(self.test_monitor.gui, self.tr("Test Monitor"))
        #tabs.setCurrentWidget(self.live_monitor.gui)
        tabs.setTabPosition(QTabWidget.West)
        self.setCentralWidget(tabs)

        self.setMinimumSize(160,160)
        self.resize(1024,768)
        self.show()


if __name__ == "__main__":
    a = QApplication(sys.argv)
    f = main_window()
    a.exec_()
