import numpy
import cPickle as pickle
from operator import itemgetter

macs = {'alice': '1c:7e:e5:5c:9a:d7', 'relay': '1c:7e:e5:5c:97:e5', 'bob': '34:08:04:99:f2:f6'}

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
        self.macs = macs

    # Read specified field in sorted order
    def keys(self, rd, field):
        keys = map(lambda r: r[0].run_info[field], rd)
        keys = list(set(keys))
        return sorted(keys)

    # Return values of a dictionary sorted by their keys
    def sort_data(self, data):
        # Yeah, we love it
        return numpy.array(map(lambda i: i[1], sorted(data.iteritems())))

    def result_has_key(self, rd, field):
        if not rd[0][0].result.has_key(field):
            print("Missing result key: {}".format(field))
            return False
        else:
            return True

    def sample_has_key(self, rd, field):
        if not rd[0][0].samples[0].has_key(field):
            print("Missing sample key: {}".format(field))
            return False
        else:
            return True

    # Average over a field in a result set
    def average_result(self, rd, field, par):
        if not self.result_has_key(rd, field):
            return numpy.array([])

        avg = {}
        # For each run_no in test
        for r in rd:
            key = r[0].run_info[par]
            # Remove empty last result
            if not r[-1].result: r.pop(-1)
            # Read result field for each loop in run_no
            val = map(lambda d: d.result[field], r)
            avg[key] = numpy.average(val)
        # Return a list sorted by rates
        return self.sort_data(avg)

    def prepare_grids(self, c):
        # Mad man sorting
        x,y,z = zip(*c)
        c_sorted = [c[i] for i in numpy.lexsort((z,y,x))]

        # Shape our sorted axes and values
        x_,y_,z_ = zip(*c_sorted)
        x_len = len(numpy.unique(x_))
        y_len = len(numpy.unique(y_))
        x_ = numpy.reshape(x_, (y_len, x_len), order='F')
        y_ = numpy.reshape(y_, (y_len, x_len), order='F')
        z_ = numpy.reshape(z_, (y_len, x_len), order='F')

        return {'x': x_, 'y': y_, 'z': z_}

    def average_result_3d(self, rd, field, x_par, y_par):
        if not self.result_has_key(rd, field):
            return numpy.array([])

        c = []
        for r in rd:
            x = r[0].run_info[x_par]
            y = r[0].run_info[y_par]
            z = map(lambda d: d.result[field], r)
            z = numpy.average(z)
            c.append((x, y, z))

        return self.prepare_grids(c)

    def average_samples_3d(self, rd, field, x_par, y_par):
        if not self.sample_has_key(rd, field):
            return numpy.array([])

        c = []
        for r in rd:
            x = r[0].run_info[x_par]
            y = r[0].run_info[y_par]
            z = self.average_run_samples(r, field)
            c.append((x,y,z))

        return self.prepare_grids(c)


    def difference_samples_3d(self, rd, field, x_par, y_par):
        if not self.sample_has_key(rd, field):
            return numpy.array([])

        sample_diff = lambda r, f: r.samples[-1][f] - r.samples[0][f]
        c = []

        for r in rd:
            x = r[0].run_info[x_par]
            y = r[0].run_info[y_par]
            z = map(lambda d: sample_diff(d, field), r)
            z = numpy.average(z)
            c.append((x,y,z))

        return self.prepare_grids(c)

    # Average over a field in a sample set (from one run)
    def average_run_samples(self, r, field):
        avg = []
        # For each loop in run_no
        for loop in r:
            if not loop.samples:
                continue
            # Read sample field for each sample set in loop
            samples = map(lambda s: s[field], loop.samples)
            # Average over samples in this loop
            avg.append(numpy.average(samples))
        return numpy.average(avg)

    # Average over a field in a sample set (from multiple loops)
    def average_samples(self, rd, field, par):
        if not self.sample_has_key(rd, field):
            return numpy.array([])

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
        if not self.sample_has_key(rd, field):
            return numpy.array([])

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
        if not self.sample_has_key(rd, field):
            return numpy.array([])

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

        # Add data to existing data
        self.avg_count[name][coding] += 1
        for key,val in data.items():
            if not len(val):
                continue

            if key not in self.agg_data[name][coding]:
                self.agg_data[name][coding][key] = numpy.zeros(len(val))

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
        rd = self.data.get_run_data_node(node, {'coding': coding})
        self.run_info = rd[0][0].run_info

        # Read out data from objects
        data = {}
        data['rates']      = self.keys(rd, 'rate')
        data['throughput'] = self.average_result(rd, 'throughput', 'rate')
        data['jitter']     = self.average_result(rd, 'jitter', 'rate')
        data['power']      = self.average_samples(rd, 'power_watt', 'rate')
        data['cpu']        = self.difference_samples(rd, 'cpu', 'rate')
        data['iw_rx']      = self.difference_samples(rd, 'iw rx bytes', 'rate')
        data['ip_rx']      = self.difference_samples(rd, 'ip_rx_bytes', 'rate')
        data['iw_tx_pkts'] = self.difference_samples(rd, 'iw tx packets', 'rate')
        data['iw_tx_retries'] = self.difference_samples(rd, 'iw tx retries', 'rate')
        data['ping_avg']   = self.average_result(rd, 'ping_avg', 'rate')
        data['decoded']    = self.difference_samples(rd, 'bat_nc_decode', 'rate')
        data['decode_failed']    = self.difference_samples(rd, 'bat_nc_decode_failed', 'rate')
        data['overheard']  = self.difference_samples(rd, 'bat_nc_overheard', 'rate')

        self.update_system_data('udp_sources', data, coding)

        return data

    def udp_ratio_source_data(self, node, coding):
        rd = self.data.get_run_data_node(node, {'coding': coding})

        data = {}
        data['throughput'] = self.average_result_3d(rd, 'throughput', 'ratio', 'rate')
        return data

    def udp_ratio_relay_data(self, node, coding):
        rd = self.data.get_run_data_node(node, {'coding': coding})

        data = {}
        data['coded'] = self.difference_samples_3d(rd, 'bat_nc_code', 'ratio', 'rate')
        data['power'] = self.average_samples_3d(rd, 'power_watt', 'ratio', 'rate')
        return data

    def udp_relay_data(self, node, coding):
        # Get data objects from storage
        rd = self.data.get_run_data_node(node, {'coding': coding})
        self.run_info = rd[0][0].run_info

        # Read out data from objects
        data = {}
        data['rates']      = self.keys(rd, 'rate')
        data['power']      = self.average_samples(rd, 'power_watt', 'rate')
        data['cpu']        = self.difference_samples(rd, 'cpu', 'rate')
        data['coded']      = self.difference_samples(rd, 'bat_nc_code', 'rate')
        data['recoded']    = self.difference_samples(rd, 'bat_nc_recode', 'rate')
        data['decoded']    = self.difference_samples(rd, 'bat_nc_decode', 'rate')
        data['decode_failed']    = self.difference_samples(rd, 'bat_nc_decode_failed', 'rate')
        data['overheard']  = self.difference_samples(rd, 'bat_nc_overheard', 'rate')
        data['fwd']        = self.difference_samples(rd, 'bat_forward', 'rate')
        #data['fwd_coded']  = self.difference_samples(rd, 'bat_nc_fwd_coded', 'rate')
        data['tx']         = self.difference_samples(rd, 'iw tx bytes', 'rate')
        data['iw_tx_pkts'] = self.difference_samples(rd, 'iw tx packets', 'rate')
        data['iw_tx_retries'] = self.difference_samples(rd, 'iw tx retries', 'rate')
        data['capture_rx'] = numpy.array([]) #self.udp_mac_capture_rx(rd, 'rate')
        data['coded_diff'] = numpy.array([]) #self.udp_rx_coded_diff(rd, 'rate')


        #data['ratio_coded'] = data['coded']/data['fwd_coded']/2
        #data['ratio_fwd']   = data['fwd']/data['fwd_coded']
        #data['ratio_total'] = data['ratio_coded'] + data['ratio_fwd']

        self.update_system_data('udp_relays', data, coding)

        return data

    def tcp_source_data(self, node, coding):
        rd = self.data.get_run_data_node(node, {'coding': coding})

        data = {}
        data['algos']       = self.keys(rd, 'tcp_algo')
        data['throughput']  = self.average_result(rd, 'throughput', 'tcp_algo')

        return data

    def tcp_window_source_data(self, node, coding):
        rd = self.data.get_run_data_node(node, {'coding': coding})

        data = {}
        data['tcp_windows'] = self.keys(rd, 'tcp_window')
        data['throughput']  = self.average_result(rd, 'throughput', 'tcp_window')

        return data

    def udp_mac_capture(self, coding):
        sample_diff = lambda s, f: s[-1][f] - s[0][f]

        # This is slow as hell - yes, I know!
        rd = {}
        loops = {}
        vals = {}
        rates = []
        diffs = []

        for node in self.sources:
            rd[node] = self.data.get_run_data_node(node, {'coding': coding})

        for i in range(len(rd[node])):
            for node in self.sources:
                loops[node] = map(lambda d: d.samples, rd[node][i])
                vals[node] = numpy.array(map(lambda s: sample_diff(s, 'iw tx packets'), loops[node]))

            rate = rd[node][i][0].run_info['rate']
            time = rd[node][i][0].run_info['test_time']
            diff = vals['alice'] - vals['bob']
            diff_avg = numpy.average(numpy.absolute(diff))
            rates.append(rate)
            diffs.append(diff_avg)

        return {'rates': rates, 'diffs': diffs}

    def udp_mac_capture_rx(self, rd, par):
        sample_diff = lambda s, f: s[-1][f] - s[0][f]

        data = {}

        # For each new parameter
        for r in rd:
            key = r[0].run_info[par]
            vals = []

            # For each loop with this parameter
            for loop in r:
                rx = []
                for node in self.sources:
                    field = "iw {} rx packets".format(self.macs[node])
                    if not self.sample_has_key(rd, field):
                        return numpy.array([])
                    val = sample_diff(loop.samples, field)
                    rx.append(val)

                # Calculate and save the Mean Absolute Deviation (MAD)
                #rx = numpy.array(rx)
                #mad = numpy.abs(rx - rx.mean()).sum() / len(rx)

                # Until now, we can live with the difference of two sources
                if rx:
                    vals.append(numpy.absolute(rx[0] - rx[1]))

            data[key] = numpy.average(vals)

        return self.sort_data(data)

    def udp_rx_coded_diff(self, rd, par):
        sample_diff = lambda s, f: s[-1][f] - s[0][f]

        data = {}

        for r in rd:
            key = r[0].run_info[par]
            vals = []

            for loop in r:
                rx = []
                for node in self.sources:
                    field = "iw {} rx packets".format(self.macs[node])
                    if not self.sample_has_key(rd, field):
                        return numpy.array([])
                    val = sample_diff(loop.samples, field)
                    rx.append(val)
                if not self.sample_has_key(rd, "bat_nc_code"):
                    return numpy.array([])
                coded = sample_diff(loop.samples, "bat_nc_code")
                #print("rx: {}  coded: {}".format(min(rx), coded))
                diff = (min(rx) - coded/2)
                vals.append(diff)

            data[key] = numpy.average(vals)

        return self.sort_data(data)
