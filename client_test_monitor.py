from PySide.QtCore import *
from PySide.QtGui import *
import pylab
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec

class monitor(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.rates = {}
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
        self.tp_canvas.draw()

    def create_overview(self):
        self.tp_fig()

        layout = QGridLayout()
        layout.addWidget(self.tp_canvas, 0, 0)

        self.overview = QGroupBox(self.tr("Overview"))
        self.overview.setLayout(layout)

    def tp_fig(self):
        self.tp_fig = Figure(figsize=(600,600), dpi=72, facecolor=(1,1,1), edgecolor=(0,0,0))
        self.tp_ax = self.tp_fig.add_subplot(self.gs[0,1])
        self.tp_ax.set_title("Throughput")
        self.tp_ax.set_ylabel("Kbit/s")
        self.tp_ax.set_xlabel("Offered Load [kbit/s]")
        self.tp_ax.set_ylim(0,100)
        self.tp_ax.grid(True)
        self.tp_canvas = FigureCanvas(self.tp_fig)
        self.tp_lines = {}
        self.tps = {}

    def add_node(self, node):
        self.rates[node] = [0]

        self.tps[node] = {'coding': [0], 'nocoding': [0]}
        self.tp_lines[node] = {}
        self.tp_lines[node]['coding'], = self.tp_ax.plot(self.rates[node], self.tps[node]['coding'], label=node.title()+" with coding")
        self.tp_lines[node]['nocoding'], = self.tp_ax.plot(self.rates[node], self.tps[node]['nocoding'], label=node.title()+" without coding")
        self.tp_ax.legend(loc='upper left', shadow=True)

    def clear(self):
        for node in self.rates:
            self.rates[node] = [0]
            self.tps[node] = {'coding': [0], 'nocoding': [0]}

    def add_result(self, node, run_info, result):
        if run_info['rate'] in self.rates[node]:
            self.clear()

        self.rates[node].append(run_info['rate'])
        self.add_tp(node, result['throughput'], run_info)

    def add_tp(self, node, tp, coding):
        coding = 'coding' if coding else 'nocoding'

        self.tps[node][coding].append(tp)
        max_coding = max(self.tps[node]['coding'])
        max_nocoding = max(self.tps[node]['nocoding'])

        self.tp_lines[node][coding].set_xdata(self.rates[node])
        self.tp_lines[node][coding].set_ydata(self.tps[node][coding])
        self.tp_ax.set_xlim(self.rates[node][0], self.rates[node][-1]+1)
        self.tp_ax.set_ylim(0, max([max_coding, max_nocoding])*1.1+1)
