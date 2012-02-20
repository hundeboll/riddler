import time
import threading
from PySide.QtCore import *
from PySide.QtGui import *
import pylab
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec

class monitor_gui(QWidget):
    add_node = Signal(str)
    update_cpu = Signal(str, list, list)
    update_tx = Signal(str, list, list)
    update_rx = Signal(str, list, list)

    def __init__(self, parent=None):
        super(monitor_gui, self).__init__(parent)
        self.gs = gridspec.GridSpec(2, 2, height_ratios=[0.95, 0.05], width_ratios=[0.02, 0.98])
        self.cpu_fig()
        self.tx_fig()
        self.rx_fig()

        self.draw_lock = threading.Lock()

        self.add_node.connect(self._add_node)
        self.update_cpu.connect(self._update_cpu)
        self.update_tx.connect(self._update_tx)
        self.update_rx.connect(self._update_rx)

        layout = QGridLayout()
        layout.addWidget(self.tx_canvas, 0, 0)
        layout.addWidget(self.rx_canvas, 0, 1)
        layout.addWidget(self.cpu_canvas, 1, 0)
        self.setLayout(layout)

        self.startTimer(2000)

    @Slot(str)
    def _add_node(self, node):
        self.cpu_lines[node], = self.cpu_ax.plot([], [], label=node.title())
        self.cpu_ax.legend(loc='upper left', shadow=True)
        self.tx_lines[node], = self.tx_ax.plot([], [], label=node.title())
        self.tx_ax.legend(loc='upper left', shadow=True)
        self.rx_lines[node], = self.rx_ax.plot([], [], label=node.title())
        self.rx_ax.legend(loc='upper left', shadow=True)

    @Slot(str, list, list)
    def _update_cpu(self, node, x, y):
        self.draw_lock.acquire()
        self.cpu_lines[node].set_data(x, y)
        self.draw_lock.release()
        self.cpu_ax.set_xlim(x[-1] - 60, x[-1])

    @Slot(str, list, list)
    def _update_tx(self, node, x, y):
        self.draw_lock.acquire()
        self.tx_lines[node].set_data(x, y)
        self.draw_lock.release()
        self.tx_ax.set_xlim(x[-1] - 60, x[-1])
        self.tx_ax.set_ylim(0, max(y)*1.1+1)

    @Slot(str, list, list)
    def _update_rx(self, node, x, y):
        self.draw_lock.acquire()
        self.rx_lines[node].set_data(x, y)
        self.draw_lock.release()
        self.rx_ax.set_xlim(x[-1] - 60, x[-1])
        self.rx_ax.set_ylim(0, max(y)*1.1+1)

    def timerEvent(self, time):
        self.draw_lock.acquire()
        self.cpu_canvas.draw_idle()
        self.tx_canvas.draw_idle()
        self.rx_canvas.draw_idle()
        self.draw_lock.release()

    def cpu_fig(self):
        c = self.palette().button().color()
        self.cpu_fig = Figure(facecolor=(c.redF(), c.greenF(), c.blueF()), edgecolor=(0,0,0))
        self.cpu_ax = self.cpu_fig.add_subplot(self.gs[0,1])
        self.cpu_ax.set_title("CPU Usage")
        self.cpu_ax.set_ylabel("Usage [%]")
        self.cpu_ax.set_xlabel("Time [s]")
        self.cpu_ax.set_ylim(0,100)
        self.cpu_ax.grid(True)
        self.cpu_canvas = FigureCanvas(self.cpu_fig)
        self.cpu_lines = {}

    def tx_fig(self):
        c = self.palette().button().color()
        self.tx_fig = Figure(facecolor=(c.redF(), c.greenF(), c.blueF()), edgecolor=(0,0,0))
        self.tx_ax = self.tx_fig.add_subplot(self.gs[0,1])
        self.tx_ax.set_title("TX Rate")
        self.tx_ax.set_ylabel("Rate [kbit/s]")
        self.tx_ax.set_xlabel("Time [s]")
        self.tx_ax.set_ylim(0,100)
        self.tx_ax.grid(True)
        self.tx_canvas = FigureCanvas(self.tx_fig)
        self.tx_lines = {}

    def rx_fig(self):
        self.rx_fig = Figure(facecolor=(1,1,1), edgecolor=(0,0,0))
        self.rx_ax = self.rx_fig.add_subplot(self.gs[0,1])
        self.rx_ax.set_title("RX Rate")
        self.rx_ax.set_ylabel("Rate [kbit/s]")
        self.rx_ax.set_xlabel("Time [s]")
        self.rx_ax.set_ylim(0,100)
        self.rx_ax.grid(True)
        self.rx_canvas = FigureCanvas(self.rx_fig)
        self.rx_lines = {}


class monitor:
    def __init__(self, parent=None):
        self.gui = monitor_gui(parent)

        self.timestamps = {}
        self.start_time = time.time()

        self.cpu_y = {}
        self.tx_y = {}
        self.rx_y = {}
        self.tx_last = {}
        self.rx_last = {}

    def add_node(self, node):
        self.timestamps[node] = [0]*60
        self.cpu_y[node] = [0]*60
        self.tx_last[node] = 0
        self.tx_y[node] = [0]*60
        self.rx_last[node] = 0
        self.rx_y[node] = [0]*60
        self.gui.add_node.emit(node)

    def add_sample(self, node, sample):
        self.timestamps[node].pop(0)
        self.timestamps[node].append(sample['timestamp'] - self.start_time)
        self.add_cpu(node, sample['cpu'])
        self.add_tx(node, sample['iw tx bytes'])
        self.add_rx(node, sample['iw rx bytes'])
        print("{0}: {1}".format(node, sample['power_amp']))

    def add_cpu(self, node, cpu):
        self.cpu_y[node].pop(0)
        self.cpu_y[node].append(cpu)
        self.gui.update_cpu.emit(node, self.timestamps[node], self.cpu_y[node])

    def add_tx(self, node, this_tx):
        this_tx = this_tx*8 / 1024
        if not self.tx_last[node]:
            self.tx_last[node] = this_tx
            return

        this_time = self.timestamps[node][-1]
        last_time = self.timestamps[node][-2]
        tx = (this_tx - self.tx_last[node]) / (this_time - last_time)
        self.tx_last[node] = this_tx
        self.tx_y[node].pop(0)
        self.tx_y[node].append(tx)
        self.gui.update_tx.emit(node, self.timestamps[node], self.tx_y[node])

    def add_rx(self, node, this_rx):
        this_rx = this_rx*8 / 1024
        if not self.rx_last[node]:
            self.rx_last[node] = this_rx
            return

        this_time = self.timestamps[node][-1]
        last_time = self.timestamps[node][-2]
        rx = (this_rx - self.rx_last[node]) / (this_time - last_time)
        self.rx_last[node] = this_rx
        self.rx_y[node].pop(0)
        self.rx_y[node].append(rx)
        self.gui.update_rx.emit(node, self.timestamps[node], self.rx_y[node])
