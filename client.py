#!/usr/bin/env python2

import sys

try:
    from PySide.QtCore import *
    from PySide.QtGui import *
except ImportError:
    print("You need the PySide module to use riddler_client!")
    sys.exit(1)

import client_gui as gui

class client:
    def __init__(self):
        self.gui = gui.main_window()


if __name__ == "__main__":
    try:
        q = QApplication(sys.argv)
        c = client()
        q.exec_()
    except KeyboardInterrupt:
        pass
