import time
from PySide.QtCore import *
from PySide.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

class control_gui(QWidget):
    def __init__(self, parent=None):
        super(control_gui, self).__init__(parent)

        label = QLabel("Controller GUI")

        layout = QGridLayout()
        layout.addWidget(label, 0, 0)
        self.setLayout(layout)

class control:
    def __init__(self, parent=None):
        self.gui = control_gui(parent)

