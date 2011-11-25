#!/usr/bin/env python2

import sys

try:
    from PySide.QtCore import *
    from PySide.QtGui import *
except ImportError:
    print("You need the PySide module to use riddler_client!")
    sys.exit(1)

import client_socket as sock

class client:
    def __init__(self):
        self.sock = sock.sock(None)


if __name__ == "__main__":
    try:
        q = QApplication(sys.argv)
        c = client()
        q.exec_()
    except KeyboardInterrupt:
        pass
