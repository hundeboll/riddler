import pylab
import matplotlib.gridspec as gridspec

class graph:
    def __init__(self):
        self.throughputs = {}

    def show(self):
        pylab.show()

    def setup_fig(self, title, xlabel, ylabel):
        fig = pylab.figure()
        ax = fig.add_subplot(111)
        ax.grid(True)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        return ax

    def finish_fig(self, ax):
        ax.legend(loc='upper left', shadow=True)

    def plot_throughput(self, node, rates, data, coding):
        if not self.throughputs.has_key(node):
            fig = self.setup_fig("Throughput for {0}".format(node.title()),
                    "Total Offered Load [kbit/s]", "Measured Throughput")
            self.throughputs[node] = fig
        else:
            fig = self.throughputs[node]

        label = "With Coding" if coding else "Without Coding"
        fig.plot(rates, data, linewidth=2, label=label)
        self.finish_fig(fig)
