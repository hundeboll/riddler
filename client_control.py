import time
from PySide.QtCore import *
from PySide.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

class toolbar(QToolBar):
    def __init__(self, parent=None):
        super(toolbar, self).__init__(parent)
        self.hide()
        self.add_actions()
        self.testing = False

    def add_actions(self):
        self.connect_action = self.addAction(QIcon.fromTheme("network-wired"), "Connect")
        self.connect_action.toggled.connect(self.connect)
        self.connect_action.setCheckable(True)

        self.toggle_action = self.addAction(QIcon.fromTheme("media-playback-start"), "Start")
        self.toggle_action.triggered.connect(self.toggle_test)
        self.toggle_action.setEnabled(False)

        self.pause_action = self.addAction(QIcon.fromTheme("media-playback-pause"), "Pause")
        self.pause_action.toggled.connect(self.pause)
        self.pause_action.setCheckable(True)
        self.pause_action.setEnabled(False)

        self.recover_action = self.addAction(QIcon.fromTheme("edit-redo"), "Recover")
        self.recover_action.triggered.connect(self.recover)
        self.recover_action.setEnabled(False)

        self.save_action = self.addAction(QIcon.fromTheme("document-save"), "Save Data")
        self.save_action.triggered.connect(self.save)
        self.save_action.setEnabled(False)

    @Slot(int)
    def connect(self, b):
        self.toggle_action.setEnabled(b)
        self.pause_action.setEnabled(b)
        self.recover_action.setEnabled(b)
        self.save_action.setEnabled(b)

    def toggle_test(self):
        self.testing = False if self.testing else True
        if self.testing:
            self.toggle_action.setText("Stop")
            self.toggle_action.setIcon(QIcon.fromTheme("media-playback-stop"))
        else:
            self.toggle_action.setText("Start")
            self.toggle_action.setIcon(QIcon.fromTheme("media-playback-start"))

    @Slot(int)
    def pause(self, b):
        pass

    def recover(self):
        pass

    def save(self):
        pass


class log(QPlainTextEdit):
    def __init__(self, parent=None):
        super(log, self).__init__(parent)
        self.setMaximumSize(32767,32767)
        self.setMinimumSize(0,0)
        self.setMaximumBlockCount(100)
        self.setReadOnly(True)

    def add_line(self, line):
        self.appendPlainText(line)


class info(QWidget):
    def __init__(self, parent=None):
        super(info, self).__init__(parent)
        self.do_layout()

    def do_layout(self):
        self.params_box = QVBoxLayout()
        self.params_box.addWidget(QLabel("Loops: 5"))
        self.params_box.addWidget(QLabel("Profile: Blah"))
        self.params_box.addStretch()
        self.params = QGroupBox("Parameters")
        self.params.setLayout(self.params_box)

        self.profile_box = QVBoxLayout()
        self.profile_box.addWidget(QLabel("Start rate: 100"))
        self.profile_box.addWidget(QLabel("Stop rate: 4000"))
        self.profile_box.addWidget(QLabel("Step rate: 100"))
        self.profile_box.addStretch()
        self.profile = QGroupBox("Profile Config")
        self.profile.setLayout(self.profile_box)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.params)
        self.layout.addWidget(self.profile)
        self.layout.addStretch()
        self.setLayout(self.layout)


class control(QWidget):
    def __init__(self, parent=None):
        super(control, self).__init__(parent)
        self.toolbar = toolbar(self)
        self.log = log(self)
        self.info = info(self)
        self.do_layout()

    def showEvent(self, event):
        self.toolbar.show()

    def hideEvent(self, event):
        self.toolbar.hide()

    def do_layout(self):
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.info)
        self.splitter.addWidget(self.log)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.splitter)
        self.setLayout(self.layout)

