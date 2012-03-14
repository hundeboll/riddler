import numpy
import cPickle as pickle
from operator import itemgetter

class data:
    def __init__(self, path):
        self.load_pickle(path)
        self.profile = self.data.args.test_profile

    def load_pickle(self, path):
        self.data = pickle.load(open(path))
        self.relays = self.data.relays
        self.sources = self.data.sources
        self.nodes = self.data.nodes


    def keys(self, rd, field):
        keys = map(lambda r: r[0].run_info[field], rd)
        return sorted(keys)

    def sort_data(self, data):
        # Yeah, we love it
        return numpy.array(map(lambda i: i[1], sorted(data.iteritems())))

    def average_result(self, rd, field, par):
        avg = {}
        # For each run_no in test
        for r in rd:
            key = r[0].run_info[par]
            # Read result field for each loop in run_no
            val = map(lambda d: d.result[field], r)
            avg[key] = numpy.average(val)
        # Return a list sorted by rates
        return self.sort_data(avg)

    def average_run_samples(self, r, field):
        avg = []
        # For each loop in run_no
        for loop in r:
            # Read sample field for each sample set in loop
            samples = map(lambda s: s[field], loop.samples)
            # Average over samples in this loop
            avg.append(numpy.average(samples))
        return numpy.average(avg)

    def average_samples(self, rd, field, par):
        avg = {}
        # For each run_no in test
        for r in rd:
            key = r[0].run_info[par]
            val = self.average_run_samples(r, field)
            avg[key] = val
        # Return a list sorted by rates
        return self.sort_data(avg)

    def difference_samples(self, rd, field, par):
        sample_diff = lambda r, f: r.samples[-1][f] - r.samples[0][f]
        avg = {}
        # For each run_no in test
        for r in rd:
            key = r[0].run_info[par]

            # Read difference in first and last sample in each loop
            val = map(lambda d: sample_diff(d, field) if d.samples else 0, r)
            avg[key] = numpy.average(val)
        # Return a list sorted by rates
        return self.sort_data(avg)

    def udp_source_data(self, node, coding):
        # Get data objects from storage
        rd = self.data.get_run_data(node, {'coding': coding})

        # Read out data from objects
        data = {}
        data['rates']      = self.keys(rd, 'rate')
        data['throughput'] = self.average_result(rd, 'throughput', 'rate')
        data['jitter']     = self.average_result(rd, 'jitter', 'rate')
        data['cpu']        = self.average_samples(rd, 'cpu', 'rate')
        data['power']      = self.average_samples(rd, 'power_watt', 'rate')

        return data

    def udp_relay_data(self, node, coding):
        # Get data objects from storage
        rd = self.data.get_run_data(node, {'coding': coding})

        # Read out data from objects
        data = {}
        data['rates']     = self.keys(rd, 'rate')
        data['cpu']       = self.average_samples(rd, 'cpu', 'rate')
        data['coded']     = self.difference_samples(rd, 'nc Coded', 'rate')
        data['fwd']       = self.difference_samples(rd, 'nc Forwarded', 'rate')
        data['fwd_coded'] = self.difference_samples(rd, 'nc FwdCoded', 'rate')

        return data

    def tcp_source_data(self, node, coding):
        rd = self.data.get_run_data(node, {'coding': coding})

        data = {}
        data['algos']       = self.keys(rd, 'tcp_algo')
        data['throughput']  = self.average_result(rd, 'throughput', 'tcp_algo')

        return data

    def tcp_window_source_data(self, node, coding):
        rd = self.data.get_run_data(node, {'coding': coding})

        data = {}
        data['tcp_windows'] = self.keys(rd, 'tcp_window')
        data['throughput']  = self.average_result(rd, 'throughput', 'tcp_window')

        return data
