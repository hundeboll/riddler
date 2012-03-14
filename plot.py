#!/usr/bin/env python2

import argparse
import numpy
import cPickle as pickle
import plot_data as data
import plot_graph as graph

parser = argparse.ArgumentParser(description="Riddler Plotting Tools")
parser.add_argument("--config", default="plot_defaults")
(args,dummy) = parser.parse_known_args()

try:
    c = __import__(args.config)
    defaults = dict((k, v) for k,v in c.__dict__.iteritems() if not k.startswith('__'))
except ImportError:
    print("Unable to load config file: {0}".format(args.config))
    sys.exit(1)

parser.add_argument("--data")
parser.add_argument("--out")
parser.add_argument("--show")
parser.set_defaults(**defaults)
args = parser.parse_args()

class plot:
    def __init__(self, args):
        self.args = args
        self.aggregated_throughput = {}
        self.data = data.data(args.data)
        self.graph = graph.graph()

    def plot(self):
        if self.data.profile == 'udp_rates':
            # For each source
            for node in self.data.sources:
                self.plot_udp_source(node)
            self.plot_udp_aggregated_throughput()

            # For each relay
            for node in self.data.relays:
                self.plot_udp_relay(node)

        elif self.data.profile == 'tcp_algos':
            for node in self.data.sources:
                self.plot_tcp_source(node)
            for node in self.data.relays:
                self.plot_tcp_relay(node)

        elif self.data.profile == 'tcp_windows':
            for node in self.data.sources:
                self.plot_tcp_window_source(node)
            for node in self.data.relays:
                self.plot_tcp_window_relay(node)

        self.graph.show()

    def plot_udp_aggregated_throughput(self):
        for coding in (True, False):
            data = self.aggregated_throughput[coding]
            self.graph.plot_udp_aggregated_throughput(data, coding)

    def add_udp_aggregated_throughput(self, data, coding):
        if not coding in self.aggregated_throughput:
            self.aggregated_throughput[coding] = {}
            self.aggregated_throughput[coding]['rates'] = numpy.array(data['rates'])
            self.aggregated_throughput[coding]['throughput'] = numpy.array(data['throughput'])
            return

        self.aggregated_throughput[coding]['throughput'] += data['throughput']
        self.aggregated_throughput[coding]['rates'] += data['rates']

    def plot_udp_source(self, node):
        for coding in (True, False):
            data = self.data.udp_source_data(node, coding)
            self.graph.plot_throughput(node, data, coding)
            self.graph.plot_cpu(node, data, coding)
            self.graph.plot_power(node, data, coding)
            self.add_udp_aggregated_throughput(data, coding)

    def plot_udp_relay(self, node):
        data = self.data.udp_relay_data(node, coding=True)
        self.graph.plot_coded(node, data)

    def plot_tcp_source(self, node):
        for coding in (True, False):
            data = self.data.tcp_source_data(node, coding)
            self.graph.plot_tcp_throughput(node, data, coding)

    def plot_tcp_relay(self, node):
        pass

    def plot_tcp_window_source(self, node):
        for coding in (True, False):
            data = self.data.tcp_window_source_data(node, coding)
            self.graph.plot_tcp_window_throughput(node, data, coding)
            print data

    def plot_tcp_window_relay(self, node):
        pass


if __name__ == "__main__":
    p = plot(args)
    p.plot()
