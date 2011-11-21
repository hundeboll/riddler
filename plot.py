#!/usr/bin/env python2

import cPickle as pickle
import pylab
import matplotlib.gridspec as gridspec

c = {
    "aluminium1":   "#eeeeec",
    "aluminium2":   "#d3d7cf",
    "aluminium3":   "#babdb6",
    "aluminium4":   "#888a85",
    "aluminium5":   "#555753",
    "aluminium6":   "#2e3436",
    "butter1":      "#fce94f",
    "butter2":      "#edd400",
    "butter3":      "#c4a000",
    "chameleon1":   "#8ae234",
    "chameleon2":   "#73d216",
    "chameleon3":   "#4e9a06",
    "chocolate1":   "#e9b96e",
    "chocolate2":   "#c17d11",
    "chocolate3":   "#8f5902",
    "orange1":      "#fcaf3e",
    "orange2":      "#f57900",
    "orange3":      "#ce5c00",
    "plum1":        "#ad7fa8",
    "plum2":        "#75507b",
    "plum3":        "#5c3566",
    "scarletred1":  "#ef2929",
    "scarletred2":  "#cc0000",
    "scarletred3":  "#a40000",
    "skyblue1":     "#729fcf",
    "skyblue2":     "#3465a4",
    "skyblue3":     "#204a87",
}

data = pickle.load(open("test.pickle"))

class plot:
    def __init__(self, filename):
        self.data = pickle.load(open(filename))
        self.rates = self.data.get_param_range('rate')
        self.coding = self.data.get_param_range('coding')
        self.hold_times = self.data.get_param_range('hold')
        self.purge_times = self.data.get_param_range('purge')

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

    def plot_throughput(self, node):
        ax = self.setup_fig("Throughput for {0}".format(node), "Total Offered Load [kbit/s]", "Measured Throughput")
        for hold in self.hold_times:
            for purge in self.purge_times:
                for coding in self.coding:
                    conditions = {'coding': coding, 'hold': hold, 'purge': purge}
                    data = self.data.results(node, conditions, field='throughput')
                    label = "Coding: {0}, Hold: {1}ms, Purge: {2}ms".format("On" if coding else "Off", hold, purge)
                    ax.plot(self.rates, data, linewidth=2, label=label)
        self.finish_fig(ax)


if __name__ == "__main__":
    p = plot("test.pickle")
    p.plot_throughput('alice')
    pylab.show()
