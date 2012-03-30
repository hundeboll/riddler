from os import path
import cPickle as pickle
import time
from PySide.QtCore import *
from PySide.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

import riddler_interface as interface

tcp_algos = ['bic', 'cubic', 'highspeed', 'htcp', 'hybla', 'illinois', 'lp', 'reno', 'scalable', 'vegas', 'veno', 'westwood', 'yeah']

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
        self.parentWidget().send_args()
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

class test_config(QGroupBox):
    def __init__(self, parent=None):
        super(test_config, self).__init__(parent)
        self.setTitle("Test Config")
        self.current_profile = 0
        self.do_layout()

    def do_layout(self):
        vbox = QGridLayout()

        self.profile = QComboBox(self)
        self.profile.currentIndexChanged.connect(self.profile_changed)
        vbox.addWidget(QLabel("Profile:"), 0, 0)
        vbox.addWidget(self.profile, 0, 1)

        self.loops = QSpinBox(self)
        self.loops.setReadOnly(True)
        vbox.addWidget(QLabel("Loops:"), 1, 0)
        vbox.addWidget(self.loops, 1, 1)

        self.time = QSpinBox(self)
        self.time.setReadOnly(True)
        vbox.addWidget(QLabel("Time:"), 2, 0)
        vbox.addWidget(self.time, 2, 1)

        self.sleep = QSpinBox(self)
        self.sleep.setReadOnly(True)
        vbox.addWidget(QLabel("Sleep"), 3, 0)
        vbox.addWidget(self.sleep, 3, 1)

        vbox.addItem(QSpacerItem(0,0), 4,0)
        vbox.setRowStretch(4, 10)
        self.setLayout(vbox)

    def add_profile(self, profile):
        self.profile.addItem(profile.name, userData=profile)

    def profile_changed(self, index):
        self.profile.itemData(self.current_profile).hide()
        self.current_profile = index
        self.profile.itemData(self.current_profile).show()

    def add_event(self, event):
        if event == interface.CONNECTDED:
            self.loops.setReadOnly(False)
            self.time.setReadOnly(False)
            self.sleep.setReadOnly(False)

        elif event == interface.DISCONNECTED:
            self.loops.setReadOnly(True)
            self.time.setReadOnly(True)
            self.sleep.setReadOnly(True)

    def add_args(self, args):
        idx = self.profile.findText(args.test_profile)
        if idx >= 0:
            self.profile.setCurrentIndex(idx)
        self.loops.setValue(args.test_loops)
        self.time.setValue(args.test_time)
        self.sleep.setValue(args.test_sleep)

    def get_args(self, args):
        args.test_profile = self.profile.currentText()
        args.test_loops = self.loops.value()
        args.test_time = self.time.value()
        args.test_sleep = self.time.value()


class udp_rates_config(QGroupBox):
    def __init__(self, parent=None):
        super(udp_rates_config, self).__init__(parent)
        self.name = "udp_rates"
        self.setTitle("UDP Rates Config")
        self.hide()
        self.do_layout()

    def do_layout(self):
        vbox = QGridLayout()

        self.start = QSpinBox()
        self.start.setReadOnly(True)
        self.start.setMaximum(2147483647)
        vbox.addWidget(QLabel("Rate Start:"), 0, 0)
        vbox.addWidget(self.start, 0, 1)

        self.stop = QSpinBox()
        self.stop.setReadOnly(True)
        self.stop.setMaximum(2147483647)
        vbox.addWidget(QLabel("Rate Stop:"), 1, 0)
        vbox.addWidget(self.stop, 1, 1)

        self.step = QSpinBox()
        self.step.setReadOnly(True)
        self.step.setMaximum(2147483647)
        vbox.addWidget(QLabel("Rate Step:"), 2, 0)
        vbox.addWidget(self.step)

        vbox.addItem(QSpacerItem(0,0), 4,0)
        vbox.setRowStretch(4, 10)
        self.setLayout(vbox)

    def add_event(self, event):
        if event == interface.CONNECTDED:
            self.start.setReadOnly(False)
            self.stop.setReadOnly(False)
            self.step.setReadOnly(False)

        elif event == interface.DISCONNECTED:
            self.start.setReadOnly(True)
            self.stop.setReadOnly(True)
            self.step.setReadOnly(True)

    def add_args(self, args):
        self.start.setValue(args.rate_start)
        self.stop.setValue(args.rate_stop)
        self.step.setValue(args.rate_step)

    def get_args(self, args):
        args.rate_start = self.start.value()
        args.rate_stop = self.stop.value()
        args.rate_step = self.step.value()


class udp_ratio_config(QGroupBox):
    def __init__(self, parent=None):
        super(udp_ratio_config, self).__init__(parent)
        self.name = "udp_ratios"
        self.setTitle("UDP Ratios Config")
        self.hide()
        self.do_layout()

    def do_layout(self):
        vbox = QGridLayout()

        self.start = QSpinBox()
        self.start.setReadOnly(True)
        self.start.setMaximum(2147483647)
        vbox.addWidget(QLabel("Ratio Start:"), 0, 0)
        vbox.addWidget(self.start, 0, 1)

        self.stop = QSpinBox()
        self.stop.setReadOnly(True)
        self.stop.setMaximum(2147483647)
        vbox.addWidget(QLabel("Ratio Stop:"), 1, 0)
        vbox.addWidget(self.stop, 1, 1)

        self.step = QSpinBox()
        self.step.setReadOnly(True)
        self.step.setMaximum(2147483647)
        vbox.addWidget(QLabel("Ratio Step:"), 2, 0)
        vbox.addWidget(self.step, 2, 1)

        vbox.addItem(QSpacerItem(0,0), 3, 0)
        vbox.setRowStretch(3, 10)
        self.setLayout(vbox)

    def add_event(self, event):
        if event == interface.CONNECTDED:
            self.start.setReadOnly(False)
            self.stop.setReadOnly(False)
            self.step.setReadOnly(False)

        elif event == interface.DISCONNECTED:
            self.start.setReadOnly(True)
            self.stop.setReadOnly(True)
            self.step.setReadOnly(True)

    def add_args(self, args):
        self.start.setValue(args.ratio_start)
        self.stop.setValue(args.ratio_stop)
        self.step.setValue(args.ratio_step)

    def get_args(self, args):
        args.ratio_start = self.start.value()
        args.ratio_stop = self.stop.value()
        args.ratio_step = self.step.value()


class tcp_window_config(QGroupBox):
    def __init__(self, parent=None):
        super(tcp_window_config, self).__init__(parent)
        self.name = "tcp_windows"
        self.setTitle("TCP Window Config")
        self.hide()
        self.do_layout()

    def do_layout(self):
        vbox = QGridLayout()


        self.algo = QComboBox()
        for algo in tcp_algos:
            self.algo.addItem(algo)
        vbox.addWidget(QLabel("TCP Algo:"), 0, 0)
        vbox.addWidget(self.algo, 0, 1)

        self.start = QSpinBox()
        self.start.setReadOnly(True)
        self.start.setMaximum(2147483647)
        vbox.addWidget(QLabel("Window Start:"), 1, 0)
        vbox.addWidget(self.start, 1, 1)

        self.stop = QSpinBox()
        self.stop.setReadOnly(True)
        self.stop.setMaximum(2147483647)
        vbox.addWidget(QLabel("Window Stop:"), 2, 0)
        vbox.addWidget(self.stop, 2, 1)

        self.step = QSpinBox()
        self.step.setReadOnly(True)
        self.step.setMaximum(2147483647)
        vbox.addWidget(QLabel("Window Step:"), 3, 0)
        vbox.addWidget(self.step, 3, 1)

        vbox.addItem(QSpacerItem(0,0), 4, 0)
        vbox.setRowStretch(4, 10)
        self.setLayout(vbox)

    def add_event(self, event):
        if event == interface.CONNECTDED:
            self.start.setReadOnly(False)
            self.stop.setReadOnly(False)
            self.step.setReadOnly(False)

        elif event == interface.DISCONNECTED:
            self.start.setReadOnly(True)
            self.stop.setReadOnly(True)
            self.step.setReadOnly(True)

    def add_args(self, args):
        idx = self.algo.findText(args.tcp_algo)
        if idx >= 0:
            self.algo.setCurrentIndex(idx)
        self.start.setValue(args.window_start)
        self.stop.setValue(args.window_stop)
        self.step.setValue(args.window_step)

    def get_args(self, args):
        args.tcp_algo = self.algo.currentText()
        args.window_start = self.start.value()
        args.window_stop = self.stop.value()
        args.window_step = self.step.value()


class tcp_algos_config(QGroupBox):
    def __init__(self, parent=None):
        super(tcp_algos_config, self).__init__(parent)
        self.name = "tcp_algos"
        self.setTitle("TCP Algos")
        self.hide()
        self.do_layout()
        self.add_algos()

    def do_layout(self):
        vbox = QGridLayout()

        self.model = QStandardItemModel()
        self.view = QListView()
        self.view.setModel(self.model)
        vbox.addWidget(self.view, 0,0)

        vbox.addItem(QSpacerItem(0,0), 1,0)
        vbox.setRowStretch(1, 10)
        self.setLayout(vbox)

    def add_algo(self, algo):
        item = QStandardItem(algo)
        item.setCheckable(True)
        self.model.appendRow(item)

    def add_algos(self):
        for algo in tcp_algos:
            self.add_algo(algo)

    def add_event(self, event):
        pass

    def add_args(self, args):
        for algo in args.tcp_algos:
            for item in self.model.findItems(algo):
                item.setCheckState(Qt.Checked)

    def get_args(self, args):
        algos = []
        for algo in tcp_algos:
            for item in self.model.findItems(algo):
                if item.CheckState() == Qt.Checked:
                    algos.append(item.text())
        args.tcp_algos = algos


class parameters(QWidget):
    def __init__(self, parent=None):
        super(parameters, self).__init__(parent)
        self.socket = None
        self.test_config = test_config(self)
        self.udp_rates_config = udp_rates_config(self)
        self.udp_ratio_config = udp_ratio_config(self)
        self.tcp_window_config = tcp_window_config(self)
        self.tcp_algos_config = tcp_algos_config(self)

        self.test_config.add_profile(self.udp_rates_config)
        self.test_config.add_profile(self.udp_ratio_config)
        self.test_config.add_profile(self.tcp_window_config)
        self.test_config.add_profile(self.tcp_algos_config)

        self.do_layout()

    def do_layout(self):
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.test_config)
        self.layout.addWidget(self.udp_rates_config)
        self.layout.addWidget(self.udp_ratio_config)
        self.layout.addWidget(self.tcp_window_config)
        self.layout.addWidget(self.tcp_algos_config)
        self.layout.addStretch()
        self.setLayout(self.layout)

    def set_socket(self, socket):
        self.socket = socket

    def add_node(self, obj):
        print([node['name'] for node in obj.nodes])

    def add_run_info(self, obj):
        print(obj.run_info['rate'])

    def add_args(self, obj):
        self.test_config.add_args(obj.args)
        self.udp_rates_config.add_args(obj.args)
        self.udp_ratio_config.add_args(obj.args)
        self.tcp_window_config.add_args(obj.args)
        self.tcp_algos_config.add_args(obj.args)
        self.args = obj.args

    def get_args(self):
        self.test_config.get_args(self.args)
        self.udp_rates_config.get_args(self.args)
        self.udp_ratio_config.get_args(self.args)
        self.tcp_window_config.get_args(self.args)
        self.tcp_algos_config.get_args(self.args)
        return self.args

    def send_args(self):
        if not self.socket:
            return
        self.socket.send(interface.CLIENT_ARGS, args=self.get_args())

    def add_event(self, event):
        self.test_config.add_event(event)
        self.udp_rates_config.add_event(event)
        self.udp_ratio_config.add_event(event)
        self.tcp_window_config.add_event(event)
        self.tcp_algos_config.add_event(event)


class control(QWidget):
    def __init__(self, parent=None):
        super(control, self).__init__(parent)
        self.toolbar = toolbar(self)
        self.log = log(self)
        self.parameters = parameters(self)
        self.do_layout()

    def do_layout(self):
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.parameters)
        self.splitter.addWidget(self.log)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.splitter)
        self.setLayout(self.layout)

    def set_socket(self, socket):
        socket.subscribe(self, interface.CLIENT_NODES, self.parameters.add_node)
        socket.subscribe(self, interface.CLIENT_RUN_INFO, self.parameters.add_run_info)
        socket.subscribe(self, interface.CLIENT_ARGS, self.parameters.add_args)
        socket.subscribe(self, interface.CLIENT_EVENT, self.add_event)
        self.toolbar.set_socket(socket)
        self.parameters.set_socket(socket)

    def controller_connected(self):
        self.toolbar.add_event(interface.CONNECTDED)
        self.parameters.add_event(interface.CONNECTDED)

    def controller_disconnected(self):
        self.toolbar.add_event(interface.DISCONNECTED)
        self.parameters.add_event(interface.DISCONNECTED)

    def add_event(self, obj):
        self.toolbar.add_event(obj.event)

    def send_args(self):
        self.parameters.send_args()
