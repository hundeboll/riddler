#!/usr/bin/env python2

import argparse
import cPickle as pickle
import plot_data as data
import plot_graph as graph
import numpy

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
parser.add_argument("--hide", action='store_true')
parser.add_argument("--plots")
parser.set_defaults(**defaults)
args = parser.parse_args()

class plot:
    def __init__(self, args):
        self.args = args
        self.aggregated_throughput = {}
        self.data = data.data(args.data)
        self.graph = graph.graph()
        #for sample in self.data.samples():
        #    print(sample)

    def plot(self):
        if self.data.profile == 'udp_rates':
            # For each source
            for node in self.data.sources:
                self.plot_udp_rate_source(node)

            # For each relay
            for node in self.data.relays:
                self.plot_udp_rate_relay(node)

            self.plot_udp_rate_system()
            self.plot_udp_mac_capture()

        elif self.data.profile == 'udp_ratios':
            for node in self.data.sources:
                self.plot_udp_ratio_source(node)

            for node in self.data.relays:
                self.plot_udp_ratio_relay(node)

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

        elif self.data.profile == 'rlnc':
            self.plot_rlnc_throughput("source", "helper", "dest")
            #self.plot_rlnc_timeouts("source", "dest")

    def show_plots(self):
        if not self.args.hide:
            self.graph.show(self.args.plots)

        if self.args.out:
            self.graph.save_figs(self.args.out)

    def plot_udp_rate_source(self, node):
        if self.args.plots not in ('all', 'system', node):
            return

        for coding in (False, True):
            data = self.data.udp_source_data(node, coding)

            if self.args.plots in ('all', node):
                self.graph.plot_throughput(node, data, coding)
                self.graph.plot_cpu(node, data, coding)
                #self.graph.plot_power(node, data, coding)
                self.graph.plot_delay(node, data, coding)
                self.graph.plot_tx_retries(node, data, coding)

            if coding:
                self.graph.plot_tx_packets(data, node)

    def plot_udp_rate_relay(self, node):
        if self.args.plots not in ('all', 'system', node):
            return

        for coding in (False, True):
            data = self.data.udp_relay_data(node, coding)

            if coding:
                self.graph.plot_tx_packets(data, node)

            if self.args.plots in ('all', node) and coding:
                self.graph.plot_coded(node, data)
                self.graph.plot_udp_rx_coded_diff(node, data)

            if self.args.plots in ('all', node):
                #self.graph.plot_power(node, data, coding)
                self.graph.plot_udp_mac_capture_rx(node, data, coding)
                self.graph.plot_cpu(node, data, coding)
                self.graph.plot_tx_retries(node, data, coding)

    def plot_udp_rate_system(self):
        if self.args.plots not in ('all', 'system'):
            return

        for coding in (False, True):
            source_agg,source_avg = self.data.get_system_data('udp_sources', coding)
            relay_agg,relay_avg = self.data.get_system_data('udp_relays', coding)

            self.graph.plot_udp_system_throughput(source_agg, coding)
            self.graph.plot_udp_system_delay(source_avg, coding)
            self.graph.plot_system_cpu(source_avg, relay_avg, coding)
            self.graph.plot_udp_system_retries(source_avg, relay_avg, coding)
            self.graph.plot_system_tx(source_agg, relay_agg, coding, self.data.run_info)
            if coding:
                self.graph.plot_coded("system", relay_avg)
            #self.graph.plot_udp_system_power(source_agg, relay_agg, coding)
            #self.graph.plot_udp_system_power_per_bit(source_agg, relay_agg, coding)

    def plot_udp_mac_capture(self):
        if self.args.plots not in ('all', 'system'):
            return

        #for coding in (False, True):
        #    data = self.data.udp_mac_capture(coding)
        #    self.graph.plot_udp_mac_capture(data, coding)

    def plot_udp_ratio_source(self, node):
        if self.args.plots not in ('all', 'system', node):
            return

        for coding in (False, True):
            data = self.data.udp_ratio_source_data(node, coding)

            if self.args.plots in ('all', node):
                self.graph.plot_udp_ratio_throughput(node, data, coding)

    def plot_udp_ratio_relay(self, node):
        if self.args.plots not in ('all', 'system', node):
            return

        for coding in (False, True):
            data = self.data.udp_ratio_relay_data(node, coding)
            self.graph.plot_udp_ratio_power(node, data, coding)

            if self.args.plots in ('all', node) and coding:
                self.graph.plot_udp_ratio_coded(node, data)

    def plot_tcp_source(self, node):
        if self.args.plots not in ('all', 'system', node):
            return

        for coding in (False, True):
            data = self.data.tcp_source_data(node, coding)
            self.graph.plot_tcp_throughput(node, data, coding)

    def plot_tcp_relay(self, node):
        pass

    def plot_tcp_window_source(self, node):
        if self.args.plots not in ('all', 'system', node):
            return

        for coding in (False, True):
            data = self.data.tcp_window_source_data(node, coding)
            self.graph.plot_tcp_window_throughput(node, data, coding)

    def plot_tcp_window_relay(self, node):
        pass

    def plot_rlnc_throughput(self, source, helper, dest):
        gs = self.data.arg("gen_size")
        for coding in ('noloss', 'loss', 'helper', 'nohelper'):
            s_data = self.data.rlnc_source_data(source, coding)
            d_data = self.data.rlnc_dest_data(dest, coding)
            h_data = self.data.rlnc_helper_data(helper, coding)
            self.graph.plot_rlnc_throughput(s_data, d_data, coding, gs)
            self.graph.plot_rlnc_transmissions(s_data, h_data, d_data, coding, gs)
            if coding in ("helper", "nohelper"):
                self.graph.plot_rlnc_requests(source, s_data, coding, gs)
                self.graph.plot_rlnc_requests(dest, d_data, coding, gs)

    def plot_rlnc_timeouts(self, source, dest):
        for error in self.data.arg("errors"):
            maximum = numpy.array([])
            minimum = numpy.array([])
            encoder_num = []
            throughput = []
            d = {}
            for encs in self.data.arg("encoders"):
                d_3d = self.data.rlnc_to_dest_3d(dest, error, encs)
                self.graph.plot_rlnc_to_3d(d_3d, error, encs)
                d[encs] = d_3d['rate_raw']
                if maximum.size == 0:
                    maximum = d[encs][:,2]
                    minimum = d[encs][:,2]
                else:
                    maximum = numpy.maximum(maximum, d[encs][:,2])
                    minimum = numpy.minimum(minimum, d[encs][:,2])

                for timeout in ("ack_timeout", "req_timeout"):
                    if self.args.plots not in ('all', 'rlnc'):
                        break

                    s_data = self.data.rlnc_to_source_data(source, timeout, error, encs)
                    d_data = self.data.rlnc_to_dest_data(dest, timeout, error, encs)

                    self.graph.plot_rlnc_timeout(s_data, d_data, timeout, error, encs)

            if self.args.plots not in ('all', 'contour'):
                continue

            for encs,data in d.items():
                tmp = zip(*filter(lambda i: i[0][2] >= i[1], zip(data, maximum)))
                if not tmp:
                    continue
                x,y,z = zip(*tmp[0])
                throughput += tmp[0]
                encoder_num += zip(x,y, [encs]*len(z))
                e = {'points': tmp[0], 'min': min(minimum), 'max': max(maximum)}
                self.graph.plot_rlnc_to_scatter(e, error, encs)

            self.graph.plot_rlnc_to_throughput(throughput, encoder_num, error)
            self.graph.plot_rlnc_to_contour(encoder_num, error)


if __name__ == "__main__":
    p = plot(args)
    p.plot()
    p.show_plots()

