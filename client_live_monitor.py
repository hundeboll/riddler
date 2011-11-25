import time
from PySide.QtCore import *
from PySide.QtGui import *
import pylab
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec

class monitor(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.timestamps = {}
        self.start_time = time.time()
        self.gs = gridspec.GridSpec(2, 2, height_ratios=[0.95, 0.05], width_ratios=[0.02, 0.98])
        self.create_overview()

        bottom = QWidget()
        bottom.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.addWidget(self.overview)
        layout.addWidget(bottom)
        self.setLayout(layout)

        self.startTimer(1000)

    def timerEvent(self, time):
        self.cpu_canvas.draw()
        self.tx_canvas.draw()
        self.rx_canvas.draw()

    def create_overview(self):
        self.cpu_fig()
        self.tx_fig()
        self.rx_fig()

        layout = QGridLayout()
        layout.addWidget(self.tx_canvas, 0, 0)
        layout.addWidget(self.rx_canvas, 0, 1)
        layout.addWidget(self.cpu_canvas, 1, 0)

        self.overview = QGroupBox(self.tr("Overview"))
        self.overview.setLayout(layout)

    def cpu_fig(self):
        self.cpu_fig = Figure(figsize=(600,600), dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0))
        self.cpu_ax = self.cpu_fig.add_subplot(self.gs[0,1])
        self.cpu_ax.set_title("CPU Usage")
        self.cpu_ax.set_ylabel("Percent")
        self.cpu_ax.set_xlabel("Sec")
        self.cpu_ax.set_ylim(0,100)
        self.cpu_ax.grid(True)
        self.cpu_canvas = FigureCanvas(self.cpu_fig)
        self.cpu_lines = {}
        self.cpu_y = {}

    def tx_fig(self):
        self.tx_fig = Figure(figsize=(600,600), dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0))
        self.tx_ax = self.tx_fig.add_subplot(self.gs[0,1])
        self.tx_ax.set_title("TX Rate")
        self.tx_ax.set_ylabel("Kbit/s")
        self.tx_ax.set_xlabel("Sec")
        self.tx_ax.set_ylim(0,100)
        self.tx_ax.grid(True)
        self.tx_canvas = FigureCanvas(self.tx_fig)
        self.tx_lines = {}
        self.tx_y = {}
        self.tx_last = {}

    def rx_fig(self):
        self.rx_fig = Figure(figsize=(600,600), dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0))
        self.rx_ax = self.rx_fig.add_subplot(self.gs[0,1])
        self.rx_ax.set_title("RX Rate")
        self.rx_ax.set_ylabel("Kbit/s")
        self.rx_ax.set_xlabel("Sec")
        self.rx_ax.set_ylim(0,100)
        self.rx_ax.grid(True)
        self.rx_canvas = FigureCanvas(self.rx_fig)
        self.rx_lines = {}
        self.rx_y = {}
        self.rx_last = {}

    def add_node(self, node):
        self.timestamps[node] = []

        self.cpu_y[node] = []
        self.cpu_lines[node], = self.cpu_ax.plot(self.timestamps[node], self.cpu_y[node], label=node.title())
        self.cpu_ax.legend(loc='upper left', shadow=True)

        self.tx_last[node] = 0
        self.tx_y[node] = []
        self.tx_lines[node], = self.tx_ax.plot(self.timestamps[node], self.tx_y[node], label=node.title())
        self.tx_ax.legend(loc='upper left', shadow=True)

        self.rx_last[node] = 0
        self.rx_y[node] = []
        self.rx_lines[node], = self.rx_ax.plot(self.timestamps[node], self.rx_y[node], label=node.title())
        self.rx_ax.legend(loc='upper left', shadow=True)

    def add_sample(self, node, sample):
        self.timestamps[node].append(sample['timestamp'] - self.start_time)
        self.add_cpu(node, sample['cpu'])
        self.add_tx(node, sample['iw tx bytes'])
        self.add_rx(node, sample['iw rx bytes'])

    def add_cpu(self, node, cpu):
        self.cpu_y[node].append(cpu)
        self.cpu_lines[node].set_xdata(self.timestamps[node])
        self.cpu_lines[node].set_ydata(self.cpu_y[node])
        self.cpu_ax.set_xlim(self.timestamps[node][-1] - 60, self.timestamps[node][-1])

    def add_tx(self, node, this_tx):
        this_tx = this_tx*8 / 1024
        if not self.tx_last[node]:
            self.tx_last[node] = this_tx
            return

        this_time = self.timestamps[node][-1]
        last_time = self.timestamps[node][-2]
        tx = (this_tx - self.tx_last[node]) / (this_time - last_time)
        self.tx_last[node] = this_tx
        self.tx_y[node].append(tx)
        self.tx_lines[node].set_xdata(self.timestamps[node][1:])
        self.tx_lines[node].set_ydata(self.tx_y[node])
        self.tx_ax.set_xlim(self.timestamps[node][-1] - 60, self.timestamps[node][-1])
        self.tx_ax.set_ylim(0, max(self.tx_y[node])*1.1+1)

    def add_rx(self, node, this_rx):
        this_rx = this_rx*8 / 1024
        if not self.rx_last[node]:
            self.rx_last[node] = this_rx
            return

        this_time = self.timestamps[node][-1]
        last_time = self.timestamps[node][-2]
        rx = (this_rx - self.rx_last[node]) / (this_time - last_time)
        self.rx_last[node] = this_rx
        self.rx_y[node].append(rx)
        self.rx_lines[node].set_xdata(self.timestamps[node][1:])
        self.rx_lines[node].set_ydata(self.rx_y[node])
        self.rx_ax.set_xlim(self.timestamps[node][-1] - 60, self.timestamps[node][-1])
        self.rx_ax.set_ylim(0, max(self.rx_y[node])*1.1+1)
