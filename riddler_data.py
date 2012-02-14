import time
import numpy
import cPickle as pickle

class run_data:
    def __init__(self, run_info):
        self.run_info = run_info
        self.time_begin = time.time()
        self.time_end = None
        self.samples = []
        self.result = None

    def samples_has_field(self, field):
        if not self.samples:
            return False
        return self.samples[0].has_key(field)

    def result_has_field(self, field):
        if not self.result:
            return False
        return self.result.has_key(field)

    def append_samples(self, samples):
        self.samples.extend(samples)

    def set_result(self, result):
        self.result = result
        self.time_end = time.time()

    def get_samples(self, field):
        return map(lambda s: s[field], self.samples)

    def get_result(self, field):
        return self.result[field]


class node_data:
    def __init__(self, node):
        self.node = node
        self.data_sets = {}

    def new_run(self, run_info):
        self.key = run_info['key']
        self.data_sets[self.key] = run_data(run_info)

    def save_result(self, result):
        self.data_sets[self.key].set_result(result)

    def append_samples(self, samples):
        self.data_sets[self.key].append_samples(samples)

    def get_samples(self, key, field):
        return self.data_sets[key].get_samples(field)

    def get_result(self, key, field):
        return self.data_sets[key].get_result(field)

    def result_has_field(self, field):
        data = next(self.data_sets.itervalues())
        return data.result_has_field(field)

    def samples_has_field(self, field):
        data = next(self.data_sets.itervalues())
        return data.samples_has_field(field)


class data:
    def __init__(self, nodes, test_profile):
        self.nodes = map(lambda n: n.name, nodes)
        self.profile = test_profile
        self.run_list = []

        self.data = {}
        self.paths = {}
        for node in nodes:
            self.data[node.name] = node_data(node.name)
            self.paths[node.name] = map(lambda n: n.name, node.dests)

    def run_key(self, run_info):
        run_info['key'] = reduce(lambda s,i: s + i[0] + ": " + str(i[1]) + " ", run_info.iteritems(), "")
        self.run_list.append(run_info)
        return run_info

    def new_run(self, run_info):
        run_info = self.run_key(run_info)
        for node in self.nodes:
            self.data[node].new_run(run_info)

    def append_samples(self, node, samples):
        self.data[node].append_samples(samples)

    def save_result(self, node, result):
        self.data[node].save_result(result)

    def get_param_range(self, param):
        r = map(lambda r: r[param], self.run_list)
        return sorted(set(r))

    def _get_samples(self, node, key, field):
        return self.data[node].get_samples(key, field)

    def get_samples(self, node, keys, field):
        return [self._get_samples(node, key, field) for key in keys]

    def _get_samples_avg(self, node, key, field):
        return numpy.average(self._get_samples(node, key, field))

    def get_samples_avg(self, node, keys, field):
        return [self._get_samples_avg(node, key, field) for key in keys]

    def _get_samples_num(self, node, key, field):
        samples = self._get_samples(node, key, field)
        return samples[-1] - samples[0]

    def get_samples_num(self, node, keys, field):
        return [self._get_samples_num(node, key, field) for key in keys]

    def get_result(self, node, key, field):
        return self.data[node].get_result(key, field)

    def get_results(self, node, keys, field):
        return map(lambda key: self.data[node].get_result(key, field), keys)

    def get_keys(self, conditions, sortby='rate'):
        run_list = self.run_list
        for condition in conditions:
            run_list = filter(lambda r: r[condition] == conditions[condition], run_list)
        run_list = sorted(run_list, key=lambda r: r[sortby])
        return map(lambda r: r['key'], run_list)

    def results(self, node, conditions, field):
        r = []
        for loop in self.get_param_range('loop'):
            conditions['loop'] = loop
            keys = self.get_keys(conditions, 'rate')
            r.append(self.get_results(node, keys, field))

        return numpy.average(r, axis=0)

    def samples(self, node, conditions, field):
        loops = self.get_param_range('loop')
        s = []
        for loop in loops:
            conditions['loop'] = loop
            keys = self.get_keys(conditions, 'rate')
            s.append(self.get_samples_avg(node, keys, field))

        return numpy.average(s, axis=0)

    def samples_num(self, node, conditions, field):
        loops = self.get_param_range('loop')
        s = []
        for loop in loops:
            conditions['loop'] = loop
            keys = self.get_keys(conditions, 'rate')
            s.append(self.get_samples_num(node, keys, field))

        return numpy.average(s, axis=0)

    def result_has_field(self, node, field):
        return self.data[node].result_has_field(field)

    def samples_has_field(self, node, field):
        return self.data[node].result_has_field(field)

def dump_data(data, filename):
    f = open(filename, 'w')
    pickle.dump(data, f)
    f.close()
