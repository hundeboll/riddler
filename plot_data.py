import numpy
import cPickle as pickle
from operator import itemgetter

class data:
    def __init__(self, path):
        self.load_pickle(path)
        self.profile = self.data.args.test_profile
        self.agg_data = {}
        self.avg_data = {}
        self.avg_count = {}

    # Read measurements from riddler test
    def load_pickle(self, path):
        self.data = pickle.load(open(path))
        self.relays = self.data.relays
        self.sources = self.data.sources
        self.nodes = self.data.nodes

    # Read specified field in sorted order
    def keys(self, rd, field):
        keys = map(lambda r: r[0].run_info[field], rd)
        return sorted(keys)

    # Return values of a dictionary sorted by their keys
    def sort_data(self, data):
        # Yeah, we love it
        return numpy.array(map(lambda i: i[1], sorted(data.iteritems())))

    # Average over a field in a result set
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

    # Average over a field in a sample set (from one run)
    def average_run_samples(self, r, field):
        avg = []
        # For each loop in run_no
        for loop in r:
            # Read sample field for each sample set in loop
            samples = map(lambda s: s[field], loop.samples)
            # Average over samples in this loop
            avg.append(numpy.average(samples))
        return numpy.average(avg)

    # Average over a field in a sample set (from multiple loops)
    def average_samples(self, rd, field, par):
        avg = {}
        # For each run_no in test
        for r in rd:
            key = r[0].run_info[par]
            val = self.average_run_samples(r, field)
            avg[key] = val
        # Return a list sorted by rates
        return self.sort_data(avg)

    # Read the difference from the first and last sample in each sample set
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

    def sum_samples(self, rd, field, par):
        avg = {}
        for r in rd:
            key = r[0].run_info[par]
            summed = []

            for loop in r:
                s = reduce(lambda acc, sample: acc + sample[field], loop.samples, 0)
                summed.append(s)
            avg[key] = numpy.average(summed)

        return self.sort_data(avg)

    # Add data to system data
    def update_system_data(self, name, data, coding):
        # Initialize zeros if needed
        if name not in self.agg_data:
            self.agg_data[name] = {coding: {}, not coding: {}}
            self.avg_data[name] = {coding: {}, not coding: {}}
            self.avg_count[name] = {coding: 0, not coding: 0}

            # Read length of data
            l = len(data.values()[0])

            # Initialize zeros
            for key in data:
                self.agg_data[name][coding][key] = numpy.zeros(l)
                self.agg_data[name][not coding][key] = numpy.zeros(l)
                self.avg_data[name][coding][key] = numpy.zeros(l)
                self.avg_data[name][not coding][key] = numpy.zeros(l)

        # Add data to existing data
        self.avg_count[name][coding] += 1
        for key,val in data.items():
            # Add to summed data
            self.agg_data[name][coding][key] += val

            # Update average
            agg = self.agg_data[name][coding][key]
            self.avg_data[name][coding][key] = agg/self.avg_count[name][coding]

    # Read out system data
    def get_system_data(self, name, coding):
        agg = self.agg_data[name][coding]
        avg = self.avg_data[name][coding]
        return agg,avg

    def udp_source_data(self, node, coding):
        # Get data objects from storage
        rd = self.data.get_run_data(node, {'coding': coding})

        # Read out data from objects
        data = {}
        data['rates']      = self.keys(rd, 'rate')
        data['throughput'] = self.average_result(rd, 'throughput', 'rate')
        data['jitter']     = self.average_result(rd, 'jitter', 'rate')
        data['cpu']        = self.average_samples(rd, 'cpu', 'rate')
        data['power']      = self.sum_samples(rd, 'power_watt', 'rate')

        self.update_system_data('udp_sources', data, coding)

        return data

    def udp_relay_data(self, node, coding):
        # Get data objects from storage
        rd = self.data.get_run_data(node, {'coding': coding})

        # Read out data from objects
        data = {}
        data['rates']     = self.keys(rd, 'rate')
        data['cpu']       = self.average_samples(rd, 'cpu', 'rate')
        data['power']     = self.sum_samples(rd, 'power_watt', 'rate')
        data['coded']     = self.difference_samples(rd, 'nc Coded', 'rate')
        data['fwd']       = self.difference_samples(rd, 'nc Forwarded', 'rate')
        data['fwd_coded'] = self.difference_samples(rd, 'nc FwdCoded', 'rate')

        data['ratio_coded'] = data['coded']/data['fwd_coded']/2
        data['ratio_fwd']   = data['fwd']/data['fwd_coded']
        data['ratio_total'] = data['ratio_coded'] + data['ratio_fwd']

        self.update_system_data('udp_relays', data, coding)

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
