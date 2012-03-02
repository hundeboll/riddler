import time
from PySide.QtCore import *
from PySide.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends import backend_pdf
from matplotlib import _png

class toolbar(QToolBar):
    def __init__(self, parent=None):
        super(toolbar, self).__init__(parent)
        self.hide()
        self.plots = {}
        self.add_menus()

    def add_menus(self):
        # Save-menu
        self.save_menu = self.add_menu('Save', 'document-save')
        self.save_menu.addAction("All Visible", self.save_all)
        self.save_menu.addSeparator()

        # Pause-menu
        self.pause_menu = self.add_menu('Pause', 'media-playback-pause')

        # View-menu
        self.view_menu = self.add_menu('View', 'edit-find')
        p = self.view_menu.addAction("All Visible", self.pause_all)
        p.setCheckable(True)
        self.view_menu.addSeparator()


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

    def add_plot(self, plot):
        self.plots[plot.name] = plot
        self.save_menu.addAction(plot.title, plot.save_plot)
        v = self.view_menu.addAction(plot.title, plot.toggle_hide)
        p = self.pause_menu.addAction(plot.title, plot.toggle_pause)

        v.setCheckable(True)
        v.setChecked(True)
        p.setCheckable(True)

    def save_all(self):
        self.pause_all(True)
        folder = QFileDialog.getExistingDirectory(self, "Save plots as files")
        if not folder:
            self.pause_all(False)
            return

        for plot in self.plots.values():
            if not plot.isHidden():
                filename = "{}/{}.pdf".format(folder, plot.name)
                plot.save_file(filename, 'pdf')
        self.pause_all(False)

    def pause_all(self, b=None):
        for plot in self.plots.values():
            plot.toggle_pause(b)


class live_plot(QGroupBox):
    def __init__(self, name, title, ylabel, ylim=None, scale=1.1, parent=None):
        super(live_plot, self).__init__(title, parent)
        self.name = name
        self.title = title
        self.pause = False
        self.lines = {}
        self.data = {}
        self.scale = scale
        self.bg = None

        self.layout = QHBoxLayout()
        self.add_fig(title, ylabel, ylim, scale)
        self.setLayout(self.layout)

        self.timer = QTimer()

    def on_draw(self, event):
        self.bg = self.canvas.copy_from_bbox(self.ax.bbox)

    def add_fig(self, title, ylabel, ylim=None, scale=1.1):
        c = self.parent().palette().button().color()
        self.fig = Figure(facecolor=(c.redF(), c.greenF(), c.blueF()), edgecolor=(0,0,0))
        self.ax = self.fig.add_axes([0.15, 0.1, 0.75, 0.75])
        self.ax.set_ylabel(ylabel)
        if ylim: self.ax.set_ylim(0,ylim)
        self.ax.grid(True)
        self.ax.xaxis.set_ticks([])
        self.canvas = FigureCanvas(self.fig)
        self.canvas.mpl_connect('draw_event', self.on_draw)
        self.layout.addWidget(self.canvas, 10)

    def add_node(self, node):
        self.lines[node], = self.ax.plot([0], [0], label=node.title(), animated=True)

    def update_lines(self):
        if not self.bg:
            return
        if self.pause:
            return

        self.canvas.restore_region(self.bg)
        for node in self.data:
            x,y = self.data[node]
            self.ax.set_xlim(x[0], x[-1])
            self.lines[node].set_data(x, y)
            self.ax.draw_artist(self.lines[node])

        self.canvas.blit(self.ax.bbox)

    def update_data(self, node, x, y):
        self.data[node] = (x, y)
        self.rescale(max(y))

    def rescale(self, new_max):
        if not self.scale:
            return
        if not self.ax._cachedRenderer:
            return
        if self.pause:
            return

        # Read minimum (d) and maximum (max_view) from plot
        d,max_view = self.ax.get_ybound()
        current_max = self.current_max()

        if new_max > max_view or (max_view > 10 and current_max*2 < max_view):
            # Scale axes if new maximum has arrived
            self.ax.relim()
            self.ax.autoscale_view(scalex=False)
            self.ax.draw_artist(self.ax.yaxis)
            self.update_lines()
            self.canvas.draw()

    def current_max(self):
        current_max = 0
        for line in self.lines.values():
            m = max(line.get_ydata())
            current_max = m if m > current_max else current_max
        return current_max

    def set_animated(self, b):
        # Make sure we get animated elements
        for (node,line) in self.lines.items():
            line.set_animated(b)

    def save_plot(self):
        self.toggle_pause(True)
        filename,ext = QFileDialog.getSaveFileName(self,
                "Save plot as file",
                "",
                "Portable Document File (*.pdf);;Portable Network Graphics (*.png)")
        if filename and 'png' in ext:
            print("Saving PNG file to {}".format(filename))
            fmt = 'png'
        elif filename and 'pdf' in ext:
            print("Saving PDF file to {}".format(filename))
            fmt = 'pdf'
        else:
            self.resume()
            return

        self.save_file(filename, fmt)
        self.toggle_pause(False)

    def save_file(self, filename, fmt):
        if not filename:
            return

        self.set_animated(False)
        self.ax.set_title(self.title)
        self.fig.savefig(filename, format=fmt, transparent=True, bbox_inches='tight')
        self.ax.set_title("")
        self.set_animated(True)

    def toggle_hide(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.timer.singleShot(100, self.canvas.draw)

    def toggle_pause(self, b=None):
        if b == None:
            print("b == None")
            self.pause = False if self.pause else True
        else:
            print("Pause {}: {}".format(self.name, b))
            self.pause = b

class monitor_gui(QWidget):
    add_node = Signal(str)
    update_data = Signal(str, str, list, list)

    def __init__(self, parent=None):
        super(monitor_gui, self).__init__(parent)
        self.toolbar = toolbar(self)
        self.add_legend()
        self.do_layout(2)
        self.plots = {}
        self.add_fig('iw tx bytes', "TX Rate",           "Rate [kbit/s]")
        self.add_fig('iw rx bytes', "RX Rate",           "Rate [kbit/s]")
        self.add_fig('ip_tx_bytes', "IP TX Rate",        "Rate [kbit/s]")
        self.add_fig('ip_rx_bytes', "IP RX Rate",        "Rate [kbit/s]")
        self.add_fig('cpu',         "CPU Usage",         "Usage [%]", ylim=105, scale=False)
        self.add_fig('coded',       "Coded Packets",     "Ratio [%]", ylim=1.05, scale=False)
        self.add_fig('power',       "Power Consumption", "Usage [W]")


        self.add_node.connect(self._add_node)
        self.update_data.connect(self._update_data)

        self.startTimer(1000)

    def showEvent(self, event):
        # Switch our toolbar
        self.toolbar.show()

        # Force plots to draw axes when tab becomes visible
        for (name,plot) in self.plots.items():
            plot.timer.singleShot(10, plot.canvas.draw)

    def hideEvent(self, event):
        self.toolbar.hide()

    def do_layout(self, column_num):
        self.column_num = column_num
        self.next_column = 0
        self.columns = []
        for i in range(column_num):
            self.columns.append(QSplitter(Qt.Vertical))

        splitter = QSplitter(Qt.Horizontal)
        for column in self.columns:
            splitter.addWidget(column)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.legend['canvas'])
        layout.addWidget(splitter, 1)
        self.setLayout(layout)

    def add_plot_to_column(self, handle):
        self.columns[self.next_column%self.column_num].addWidget(handle)
        self.next_column += 1

    def add_fig(self, name, title, ylabel, ylim=None, scale=1.1):
        plot = live_plot(name, title, ylabel, ylim, scale, parent=self)
        self.toolbar.add_plot(plot)
        self.plots[name] = plot
        self.add_plot_to_column(plot)

    def add_legend(self):
        c = self.palette().button().color()
        legend = {}
        legend['fig'] = Figure(facecolor=(c.redF(), c.greenF(), c.blueF()), edgecolor=(0,0,0), figsize=(3,2))
        legend['canvas'] = FigureCanvas(legend['fig'])
        legend['canvas'].setFixedHeight(40)
        self.legend = legend

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

    @Slot(str, str, list, list)
    def _update_data(self, plot, node, x, y):
        self.plots[plot].update_data(node, x, y)

class monitor:
    def __init__(self, parent=None):
        self.gui = monitor_gui(parent)

        self.timestamps = {}
        self.start_time = time.time()

        self.vals = {}
        self.bytes = {}
        self.bytes_last = {}
        self.ratio = {}
        self.coded_last = {}
        self.fwd_last = {}

    def add_node(self, node):
        self.timestamps[node] = None
        self.vals[node] = {}
        self.bytes[node] = {}
        self.bytes_last[node] = {}
        self.ratio[node] = [0]*60
        self.coded_last[node] = 0
        self.fwd_last[node] = 0
        self.gui.add_node.emit(node)


    def add_sample(self, node, sample):
        self.add_timestamp(node, sample['timestamp'])

        self.add_val('cpu', node, sample)
        self.add_val('power', node, sample)
        self.add_coded(node, sample)
        self.add_bytes('iw rx bytes', node, sample)
        self.add_bytes('iw tx bytes', node, sample)
        self.add_bytes('ip_rx_bytes', node, sample)
        self.add_bytes('ip_tx_bytes', node, sample)

    def add_timestamp(self, node, timestamp):
        if self.timestamps[node]:
            # Just add new timestamp to ringbuffer
            self.timestamps[node].pop(0)
            self.timestamps[node].append(timestamp - self.start_time)
            return

        # Initialize timestamps from first sample
        rel_time = int(timestamp - self.start_time)
        times = range(rel_time - 60, rel_time)
        self.timestamps[node] = times

    def add_val(self, name, node, sample):
        if name not in self.vals[node]:
            self.vals[node][name] = [0]*60

        val = sample.get(name, 0)
        self.vals[node][name].pop(0)
        self.vals[node][name].append(val)
        self.gui.update_data.emit(name, node, self.timestamps[node], self.vals[node][name])

    def add_bytes(self, name, node, sample):
        this_bytes = sample.get(name, 0)
        this_bytes = this_bytes*8 / 1024
        if name not in self.bytes_last[node]:
            self.bytes_last[node][name] = this_bytes
            self.bytes[node][name] = [0]*60
            return

        this_time = self.timestamps[node][-1]
        last_time = self.timestamps[node][-2]
        bytes = (this_bytes - self.bytes_last[node][name]) / (this_time - last_time)
        self.bytes_last[node][name] = this_bytes
        self.bytes[node][name].pop(0)
        self.bytes[node][name].append(bytes)
        self.gui.update_data.emit(name, node, self.timestamps[node], self.bytes[node][name])

    def add_coded(self, node, sample):
        coded = sample.get('nc Coded', 0)
        fwd = sample.get('nc Forwarded', 0)

        # Initialize last sample
        if not self.coded_last[node]:
            self.coded_last[node] = coded
            self.fwd_last[node] = fwd
            return

        # Calculate number and ratio since last sample
        this_coded = coded - self.coded_last[node]
        this_fwd = fwd - self.fwd_last[node]
        this_total = this_coded + this_fwd
        this_ratio = 0 if not this_total else this_coded/float(this_total)

        # Save values for use in next calculation
        self.coded_last[node] = coded
        self.fwd_last[node] = fwd

        # Update plot data
        self.ratio[node].pop(0)
        self.ratio[node].append(this_ratio)
        self.gui.update_data.emit('coded', node, self.timestamps[node], self.ratio[node])
