from PySide.QtCore import *
from PySide.QtGui import *
import pylab
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec

class monitor_gui(QWidget):
    new_loop = Signal(int)
    update_tp_data = Signal(str, str, list, list)
    reset_node = Signal(str)

    def __init__(self, parent=None):
        super(monitor_gui, self).__init__(parent)

        self.gs = gridspec.GridSpec(2, 2, height_ratios=[0.95, 0.05], width_ratios=[0.02, 0.98])

        layout = QGridLayout()
        self.setLayout(layout)

        self.new_loop.connect(self._new_loop)
        self.update_tp_data.connect(self._update_tp_data)
        self.reset_node.connect(self._reset_node)

    @Slot(int)
    def _new_loop(self, loop):
        self.tp = self.tp_fig(loop)
        self.layout().addWidget(self.tp['canvas'])
        self.tp['canvas'].draw()

    @Slot(str, str, list, list)
    def _update_tp_data(self, node, coding, x, y):
        max_coding = max(x)
        max_nocoding = max(y)
        self.tp['lines'][node][coding].set_data(x, y)
        self.tp['ax'].set_xlim(x[0], x[-1]+1)
        self.tp['ax'].set_ylim(0, max([max_coding, max_nocoding])*1.1+1)
        self.tp['canvas'].draw()

    @Slot(str)
    def _reset_node(self, node):
        self.tp['lines'][node] = {}
        self.tp['lines'][node]['coding'], = self.tp['ax'].plot([0], [0], label=node.title()+" with coding")
        self.tp['lines'][node]['nocoding'], = self.tp['ax'].plot([0], [0], label=node.title()+" without coding")
        self.tp['ax'].legend(loc='upper left', shadow=True)

    def tp_fig(self, loop):
        tp = {}
        tp['fig'] = Figure(facecolor=(1,1,1), edgecolor=(0,0,0))
        tp['ax'] = tp['fig'].add_subplot(self.gs[0,1])
        tp['ax'].set_title("Throughput Loop {0}".format(loop))
        tp['ax'].set_ylabel("Kbit/s")
        tp['ax'].set_xlabel("Offered Load [kbit/s]")
        tp['ax'].set_ylim(0,100)
        tp['ax'].grid(True)
        tp['canvas'] = FigureCanvas(tp['fig'])
        tp['lines'] = {}
        return tp


class monitor:
    def __init__(self, parent=None):
        self.gui = monitor_gui(parent)

        self.rates = {}
        self.tp_data = {}
        self.nodes = []
        self.loops = []

    def add_node(self, node):
        self.nodes.append(node)

    def new_loop(self, loop):
        self.loops.append(loop)
        self.gui.new_loop.emit(loop)
        for node in self.nodes:
            self.rates[node] = [0]
            self.tp_data[node] = {'coding': [0], 'nocoding': [0]}
            self.gui.reset_node.emit(node)

    def add_result(self, node, run_info, result):
        if not run_info['loop'] in self.loops:
            self.new_loop(run_info['loop'])
        if not run_info['rate'] in self.rates[node]:
            self.rates[node].append(run_info['rate'])
        self._add_tp(node, result['throughput'], run_info['coding'])

    def _add_tp(self, node, tp, coding):
        coding = 'coding' if coding else 'nocoding'
        self.tp_data[node][coding].append(tp)
        self.gui.update_tp_data.emit(node, coding, self.rates[node], self.tp_data[node][coding])
