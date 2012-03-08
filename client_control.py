from os import path
import cPickle as pickle
import time
from PySide.QtCore import *
from PySide.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

import riddler_interface as interface

class add_connection(QDialog):
    def __init__(self, callback, parent=None):
        super(add_connection, self).__init__(parent)
        self.callback = callback
        self.do_layout()

    def do_layout(self):
        # Name for connection
        self.name_field = QLineEdit()
        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("Name:"))
        self.layout.addWidget(self.name_field)

        # Hostname
        self.host_field = QLineEdit()
        host_box = QVBoxLayout()
        host_box.addWidget(QLabel("Host:"))
        host_box.addWidget(self.host_field)

        # Port number
        self.port_field = QLineEdit()
        self.port_field.setMaximumWidth(50)
        port_box = QVBoxLayout()
        port_box.addWidget(QLabel("Port:"))
        port_box.addWidget(self.port_field)

        # Add host and port
        host_port_box = QHBoxLayout()
        host_port_box.addLayout(host_box)
        host_port_box.addLayout(port_box)
        self.layout.addLayout(host_port_box)

        # Save connection
        self.save_checkbox = QCheckBox()
        self.save_checkbox.stateChanged.connect(self.save_changed)
        save_box = QHBoxLayout()
        save_box.addWidget(QLabel("Save connection:"))
        save_box.addWidget(self.save_checkbox)
        self.layout.addLayout(save_box)

        # Auto connection
        self.auto_checkbox = QCheckBox()
        self.auto_checkbox.setEnabled(False)
        auto_box = QHBoxLayout()
        auto_box.addWidget(QLabel("Auto connect on start:"))
        auto_box.addWidget(self.auto_checkbox)
        self.layout.addLayout(auto_box)

        # OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.close)

        self.setLayout(self.layout)

    def save_changed(self, b):
        self.auto_checkbox.setEnabled(b)
        if not b:
            self.auto_checkbox.setChecked(False)

    def accept(self):
        conn = {}
        conn['name'] = self.name_field.text()
        conn['host'] = self.host_field.text()
        conn['port'] = self.port_field.text()
        conn['auto'] = self.auto_checkbox.isChecked()

        save = self.save_checkbox.isChecked()
        self.close()
        self.callback(conn, save)


class toolbar(QToolBar):
    def __init__(self, parent=None):
        super(toolbar, self).__init__(parent)
        self.path = 'connections.pickle'
        self.socket = None
        self.add_actions()
        self.load_connections()

    def add_menu(self, text, icon):
        menu = QMenu(self)
        button = QToolButton(self)
        button.setIcon(QIcon.fromTheme(icon))
        button.setText(text)
        button.setMenu(menu)
        button.setPopupMode(QToolButton.InstantPopup)
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addWidget(button)
        return menu

    def add_actions(self):
        # Connect menu
        self.connect_menu = self.add_menu("Connect", "network-wired")
        self.connect_action = self.connect_menu.addAction("New Connection", self.new_connection)

        # Disconnect button
        self.disconnect_action = self.addAction(QIcon.fromTheme("network-offline"), "Disconnect")
        self.disconnect_action.triggered.connect(self.disconnect)
        self.disconnect_action.setEnabled(False)

        # Start button
        self.start_action = self.addAction(QIcon.fromTheme("media-playback-start"), "Start")
        self.start_action.triggered.connect(self.start_test)
        self.start_action.setEnabled(False)

        # Stop button
        self.stop_action = self.addAction(QIcon.fromTheme("media-playback-stop"), "Stop")
        self.stop_action.triggered.connect(self.stop_test)
        self.stop_action.setEnabled(False)

        # Pause button
        self.pause_action = self.addAction(QIcon.fromTheme("media-playback-pause"), "Pause")
        self.pause_action.triggered.connect(self.pause)
        self.pause_action.setCheckable(True)
        self.pause_action.setEnabled(False)

        # Recover button
        self.recover_action = self.addAction(QIcon.fromTheme("edit-redo"), "Recover")
        self.recover_action.triggered.connect(self.recover)
        self.recover_action.setEnabled(False)

        # Save button
        self.save_action = self.addAction(QIcon.fromTheme("document-save"), "Save Data")
        self.save_action.triggered.connect(self.save)
        self.save_action.setEnabled(False)

    def load_connection(self, conn):
        # Create action with connection data
        a = self.connect_menu.addAction(conn['name'], self.connect)
        a.setData(conn)

    def load_connections(self):
        if not path.exists(self.path):
            self.connections = []
        else:
            self.connections = pickle.load(open(self.path, 'r'))

        if self.connections:
            self.connect_menu.addSeparator()

        for conn in self.connections:
            self.load_connection(conn)

    def new_connection(self):
        self.connect_dialog = add_connection(self.add_connection, self)
        self.connect_dialog.show()

    def add_connection(self, conn, save):
        self.load_connection(conn)

        # Make sure we only have one auto connect
        if save and conn['auto']:
            for conn in self.connections:
                conn['auto'] = False

        # Add connection to storage
        if save:
            self.connections.append(conn)
            pickle.dump(self.connections, open(self.path, 'w'), pickle.HIGHEST_PROTOCOL)

    def set_socket(self, socket):
        self.socket = socket
        for conn in self.connections:
            if conn['auto']:
                self.connect(conn)

    def enable_connect(self, b):
        # Disable further connects until disconnected
        a = self.connect_menu.menuAction().associatedWidgets()
        for w in a:
            w.setEnabled(b)

    def connect(self, conn=None):
        if not conn:
            # Read connection data
            conn = self.sender().data()

        # Connect to controller
        if self.socket and not self.socket.connect(conn['host'], conn['port']):
            print(self.socket.get_error())
            return

    def disconnect(self):
        if not self.socket:
            return
        self.socket.disconnect()

    def add_event(self, event):
        if event == interface.CONNECTDED:
            self.enable_connect(False)
            self.disconnect_action.setEnabled(True)
            self.start_action.setEnabled(True)
        elif event == interface.DISCONNECTED:
            self.enable_connect(True)
            self.disconnect_action.setEnabled(False)
            self.start_action.setEnabled(False)
            self.stop_action.setEnabled(False)
            self.pause_action.setEnabled(False)
            self.pause_action.setChecked(False)
            self.recover_action.setEnabled(False)
        elif event == interface.STOPPED:
            self.start_action.setEnabled(True)
            self.stop_action.setEnabled(False)
            self.pause_action.setEnabled(False)
            self.pause_action.setChecked(False)
            self.recover_action.setEnabled(False)
        elif event == interface.STARTED:
            self.start_action.setEnabled(False)
            self.stop_action.setEnabled(True)
            self.pause_action.setEnabled(True)
            self.recover_action.setEnabled(True)
        elif event == interface.PAUSED:
            self.add_event(interface.STARTED)
            self.pause_action.setChecked(True)
        elif event == interface.UNPAUSED:
            self.add_event(interface.STARTED)
        else:
            print("Received unknown event")

    def start_test(self):
        print("Start")
        if not self.socket:
            return
        self.socket.send(interface.CLIENT_EVENT, event=interface.STARTED)

    def stop_test(self):
        print("Stop")
        if not self.socket:
            return
        self.socket.send(interface.CLIENT_EVENT, event=interface.STOPPED)

    def pause(self):
        print("Pause")
        if not self.socket:
            return
        if self.pause_action.isChecked():
            self.socket.send(interface.CLIENT_EVENT, event=interface.PAUSED)
        else:
            self.socket.send(interface.CLIENT_EVENT, event=interface.UNPAUSED)

    def recover(self):
        print("Recover")
        if not self.socket:
            return
        self.socket.send(interface.CLIENT_EVENT, event=interface.RECOVERING)

    def save(self):
        print("Save")
        if not self.socket:
            return
        self.socket.send(interface.CLIENT_EVENT, event=interface.STARTED)


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

    def add_node(self, obj):
        print(obj.nodes)

    def add_run_info(self, obj):
        print(obj.run_info['rate'])

    def add_args(self, obj):
        print(obj.args.test_profile)


class control(QWidget):
    def __init__(self, parent=None):
        super(control, self).__init__(parent)
        self.toolbar = toolbar(self)
        self.log = log(self)
        self.info = info(self)
        self.do_layout()

    def do_layout(self):
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.info)
        self.splitter.addWidget(self.log)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.splitter)
        self.setLayout(self.layout)

    def set_socket(self, socket):
        socket.subscribe(self, interface.CLIENT_NODES, self.info.add_node)
        socket.subscribe(self, interface.CLIENT_RUN_INFO, self.info.add_run_info)
        socket.subscribe(self, interface.CLIENT_ARGS, self.info.add_args)
        socket.subscribe(self, interface.CLIENT_EVENT, self.add_event)
        self.toolbar.set_socket(socket)

    def controller_connected(self):
        self.toolbar.add_event(interface.CONNECTDED)

    def controller_disconnected(self):
        self.toolbar.add_event(interface.DISCONNECTED)

    def add_event(self, obj):
        self.toolbar.add_event(obj.event)
