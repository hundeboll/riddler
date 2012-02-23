#!/usr/bin/env python2

import cPickle as pickle
import plot_data as data
import plot_graph as graph

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

class plot:
    def __init__(self, filename):
        d = pickle.load(open(filename))
        self.data = data.data(d)
        self.graph = graph.graph()

    def plot(self):
        sources,relays = self.data.typed_nodes()

        if self.data.profile == 'udp_rates':
            for node in sources:
                self.plot_throughput_udp(node)
                #self.plot_received(node)
            for node in relays:
                #self.plot_coded(node)
                pass

        elif self.data.profile == 'tcp_algos':
            for node in sources:
                self.plot_throughput_tcp(node)
            for node in relays:
                self.plot_coded(node)

        self.graph.show()

    def plot_throughput_udp(self, node):
        for coding in self.data.codings:
            rates,data = self.data.throughput_udp(node, coding)
            self.graph.plot_throughput(node, rates, data, coding)

    def plot_coded(self, node):
        try:
            rates,coded,forwarded,total = self.data.coded(node)
        except Exception as e:
            pass

    def plot_received(self, node):
        for coding in self.data.codings:
            rates,received = self.data.received(node, coding)
            print received

if __name__ == "__main__":
    p = plot("test.pickle")
    p.plot()
