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
import client_topology as topology
import client_control as control
import riddler_interface as interface


class main_window(QMainWindow):
    def __init__(self, parent=None):
        super(main_window, self).__init__(parent)
        self.setWindowTitle("Riddler Client")

        self.live_monitor = live_monitor.monitor(parent=self)
        self.topology = topology.topology(parent=self)
        self.control = control.control(parent=self)

        menu = self.menuBar().addMenu("File")
        status = self.statusBar()

        self.addToolBar(self.control.toolbar)
        self.addToolBar(self.live_monitor.gui.toolbar)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.control, "Controller")
        self.tabs.addTab(self.live_monitor.gui, "Live Monitor")
        self.tabs.addTab(self.topology, "Topology")
        self.tabs.setTabPosition(QTabWidget.West)
        self.setCentralWidget(self.tabs)

        # Add key bindings to scroll tabs
        self.ctrl_pgup = QShortcut(QKeySequence("Ctrl+PgUp"), self)
        self.ctrl_pgup.activated.connect(self.tab_prev)
        self.ctrl_pgdown = QShortcut(QKeySequence("Ctrl+PgDown"), self)
        self.ctrl_pgdown.activated.connect(self.tab_next)


        self.setMinimumSize(160,160)
        self.resize(1024,768)
        self.show()

    def tab_next(self):
        self.tab_shift(1)

    def tab_prev(self):
        self.tab_shift(-1)

    def tab_shift(self, i):
        current = self.tabs.currentIndex()
        count = self.tabs.count()
        index = (current + i) % count
        self.tabs.setCurrentIndex(index)

    def set_socket(self, sock):
        self.control.set_socket(sock)
        self.live_monitor.add_subscriptions(sock)
        self.topology.set_socket(sock)


if __name__ == "__main__":
    a = QApplication(sys.argv)
    f = main_window()
    a.exec_()
