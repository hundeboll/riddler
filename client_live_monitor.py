import time
from PySide.QtCore import *
from PySide.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation

class checkbox:
    def __init__(self, handle, name):
        self.name = name
        self.handle = handle
        self.cb = QCheckBox(name)
        self.cb.toggle()
        self.cb.stateChanged.connect(self.state_changed)

    def state_changed(self, num):
        print(self.name)
        if self.cb.isChecked():
            self.handle.canvas.show()
            self.handle.update_lines()
            self.handle.canvas.draw()
        else:
            self.handle.canvas.hide()

class plot_selector(QWidget):
    def __init__(self, parent=None):
        super(plot_selector, self).__init__(parent)
        self.checkboxes = []
        self.locs = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
                     (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
                     (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
                     (3, 0), (3, 1), (3, 2), (3, 3), (3, 4),
                     (4, 0), (4, 1), (4, 2), (4, 3), (4, 4)]

        self.layout = QGridLayout()
        self.setLayout(self.layout)

    def add_plot(self, handle, name):
        cb = checkbox(handle, name)
        self.checkboxes.append(cb)
        loc = self.locs.pop(0)
        self.layout.addWidget(cb.cb, loc[0], loc[1])

class live_plot(QObject):
    def __init__(self, title, ylabel, ylim=None, scale=1.1):
        super(live_plot, self).__init__(parent=None)
        plot = {}
        self.x_window = 60
        self.x = range(self.x_window)
        self.fig = Figure()
        self.ax = self.fig.add_axes([0.20, 0.1, 0.75, 0.75])
        self.ax.set_title(title)
        self.ax.set_ylabel(ylabel)
        if ylim: self.ax.set_ylim(0,ylim)
        self.ax.grid(True)
        self.ax.xaxis.set_ticks([])
        self.canvas = FigureCanvas(self.fig)
        self.lines = {}
        self.data = {}
        self.canvas.mpl_connect('draw_event', self.on_draw)
        self.scale = scale
        self.bg = None
        self.canvas.draw()

        self.startTimer(self.x_window/4 * 1000) # Every quarter window size

    def timerEvent(self, event):
        self.scale_y(new_max=None, force=True)

    def on_draw(self, event):
        self.bg = self.canvas.copy_from_bbox(self.fig.bbox)

    def update_lines(self):
        if not self.bg:
            return

        self.canvas.restore_region(self.bg)
        self.ax.set_xlim(0, self.x_window)
        for node in self.data:
            y = self.data[node]
            self.lines[node].set_data(self.x, y)
            self.ax.draw_artist(self.lines[node])

        self.canvas.blit(self.ax.bbox)

    def update_data(self, node, y):
        self.data[node] = y
        self.scale_y(new_max=max(y))

    def add_node(self, node):
        self.lines[node], = self.ax.plot([], [], label=node.title(), animated=True)

    def scale_y(self, new_max, force=False):
        if not self.scale:
            return
        if not self.ax._cachedRenderer:
            return


        # Read minimum (d) and maximum (old_max) from plot
        d,current_max = self.ax.get_ybound()

        if force or new_max > current_max:
            # Scale axes if new maximum has arrived
            self.ax.relim()
            self.ax.autoscale_view(scalex=False)
            self.ax.draw_artist(self.ax.yaxis)
            self.update_lines()
            self.canvas.draw()


class monitor_gui(QWidget):
    add_node = Signal(str)
    update_data = Signal(str, str, list)

    def __init__(self, parent=None):
        super(monitor_gui, self).__init__(parent)
        self.plots = {}
        self.selector = plot_selector(self)
        self.add_fig('tx', "TX Rate", "Rate [kbit/s]")
        self.add_fig('rx', "RX Rate", "Rate [kbit/s]")
        self.add_fig('ip tx', "IP TX Rate", "Rate [kbit/s]")
        self.add_fig('ip rx', "IP RX Rate", "Rate [kbit/s]")
        self.add_fig('cpu', "CPU Usage", "Usage [%]", ylim=100, scale=False)
        self.add_fig('coded', "Coded Packets", "Ratio [%]", ylim=1.05, scale=False)
        self.add_legend()

        self.add_node.connect(self._add_node)
        self.update_data.connect(self._update_data)

        layout = QGridLayout()
        layout.addWidget(self.selector, 0, 0, 1, 2)
        layout.addWidget(self.legend['canvas'], 1, 0, 1, 2, Qt.AlignTop)
        layout.addWidget(self.plots['tx'].canvas, 2, 0)
        layout.addWidget(self.plots['rx'].canvas, 2, 1)
        layout.addWidget(self.plots['ip tx'].canvas, 3, 0)
        layout.addWidget(self.plots['ip rx'].canvas, 3, 1)
        layout.addWidget(self.plots['cpu'].canvas, 4, 0)
        layout.addWidget(self.plots['coded'].canvas, 4, 1)
        layout.setRowMinimumHeight(0, 30)
        layout.setRowMinimumHeight(1, 40)
        layout.setRowStretch(0, 0)
        layout.setRowStretch(1, 1)
        layout.setRowStretch(2, 0)
        layout.setRowStretch(3, 0)
        layout.setRowStretch(4, 0)
        self.setLayout(layout)

        self.timer = self.startTimer(1000)


    def timerEvent(self, time):
        for key in self.plots:
            self.plots[key].update_lines()

    @Slot(str)
    def _add_node(self, node):
        for key in self.plots:
            self.plots[key].add_node(node)
        handles, labels = self.plots[key].ax.get_legend_handles_labels()
        self.legend['fig'].legend(handles, labels, ncol=5, loc='upper center')
        self.legend['canvas'].draw()

    @Slot(str, str, list)
    def _update_data(self, plot, node, y):
        self.plots[plot].update_data(node, y)

    def add_fig(self, name, title, ylabel, ylim=None, scale=1.1):
        plot = live_plot(title, ylabel, ylim, scale)
        self.selector.add_plot(plot, name)
        self.plots[name] = plot

    def add_legend(self):
        legend = {}
        legend['fig'] = Figure(figsize=(3,2))
        legend['canvas'] = FigureCanvas(legend['fig'])
        self.legend = legend



class monitor:
    def __init__(self, parent=None):
        self.gui = monitor_gui(parent)

        self.timestamps = {}
        self.start_time = time.time()

        self.cpu_y = {}
        self.bytes = {}
        self.bytes_last = {}
        self.tx_y = {}
        self.rx_y = {}
        self.tx_last = {}
        self.rx_last = {}
        self.ratio = {}
        self.coded_last = {}
        self.fwd_last = {}
        self.fwd_last = {}

    def add_node(self, node):
        self.timestamps[node] = [0]*60
        self.cpu_y[node] = [0]*60
        self.bytes[node] = {}
        self.bytes_last[node] = {}
        self.tx_last[node] = 0
        self.tx_y[node] = [0]*60
        self.rx_last[node] = 0
        self.rx_y[node] = [0]*60
        self.ratio[node] = [0]*60
        self.coded_last[node] = 0
        self.fwd_last[node] = 0
        self.gui.add_node.emit(node)

    def add_sample(self, node, sample):
        self.timestamps[node].pop(0)
        self.timestamps[node].append(sample['timestamp'] - self.start_time)

        if sample.has_key('cpu'):
            self.add_cpu(node, sample['cpu'])
        if sample.has_key('iw tx bytes'):
            self.add_tx(node, sample['iw tx bytes'])
        if sample.has_key('iw rx bytes'):
            self.add_rx(node, sample['iw rx bytes'])
        if sample.has_key('nc Coded') and sample.has_key('nc Forwarded'):
            self.add_coded(node, sample['nc Coded'], sample['nc Forwarded'])
        if sample.has_key('ip_rx_bytes'):
            self.add_bytes('ip rx', node, sample['ip_rx_bytes'])
        if sample.has_key('ip_tx_bytes'):
            self.add_bytes('ip tx', node, sample['ip_tx_bytes'])

    def add_cpu(self, node, cpu):
        self.cpu_y[node].pop(0)
        self.cpu_y[node].append(cpu)
        self.gui.update_data.emit('cpu', node, self.cpu_y[node])

    def add_bytes(self, name, node, this_bytes):
        this_bytes = this_bytes*8 / 1024
        if not self.bytes_last[node].has_key(name):
            self.bytes_last[node][name] = this_bytes
            self.bytes[node][name] = [0]*60
            return

        this_time = self.timestamps[node][-1]
        last_time = self.timestamps[node][-2]
        bytes = (this_bytes - self.bytes_last[node][name]) / (this_time - last_time)
        self.bytes_last[node][name] = this_bytes
        self.bytes[node][name].pop(0)
        self.bytes[node][name].append(bytes)
        self.gui.update_data.emit(name, node, self.bytes[node][name])

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
        self.gui.update_data.emit('tx', node, self.tx_y[node])

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
        self.gui.update_data.emit('rx', node, self.rx_y[node])

    def add_coded(self, node, coded, fwd):
        if not coded:
            return

        # Initialize last sample
        if not self.coded_last[node]:
            self.coded_last[node] = coded
            self.fwd_last[node] = fwd
            return

        # Calculate number and ratio since last sample
        this_coded = coded - self.coded_last[node]
        this_fwd = fwd - self.fwd_last[node]
        this_total = this_coded + this_fwd
        this_ratio = this_coded/float(this_total) if this_total else 0

        # Save values for use in next calculation
        self.coded_last[node] = coded
        self.fwd_last[node] = fwd

        # Update plot data
        self.ratio[node].pop(0)
        self.ratio[node].append(this_ratio)
        self.gui.update_data.emit('coded', node, self.ratio[node])
