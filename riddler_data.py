import time
import copy
import cPickle as pickle

"""
Data structure:

    data = {
        'node0': {
            '0': [ run_data, run_data, ... ],
            '1': [ run_data, run_data, ... ],
            ...
        },
        'node1': {
            '0': [ run_data, run_data, ... ],
            '1': [ run_data, run_data, ... ],
            ...
        },
        ...
    }

Node dictionaries contain a list for each run_no. These lists contain
run_data objects for each loop in the test. When retrieving data,
each run_data contains a run_info dictionary, which can be used to
determine relevant parameters.
"""

class run_data:
    def __init__(self, run_info):
        self.run_info = run_info
        self.result = []
        self.samples = []

class data:
    def __init__(self, args):
        self.args = args
        self.nodes = []
        self.sources = []
        self.relays = []
        self.macs = {}
        self.rd = {}

    def add_nodes(self, nodes):
        for node in nodes:
            name = node.name
            self.rd[name] = []
            self.macs[name] = node.mac
            if node.dests:
                self.sources.append(name)
            else:
                self.relays.append(name)

    def add_run_info(self, run_info):
        run_info = copy.deepcopy(run_info)
        run_no = run_info['run_no']
        loop = run_info['loop']

        for node in self.rd:
            if loop == 0:
                self.rd[node].append([])

            rd = run_data(run_info)
            self.rd[node][run_no].append(rd)
        self.run_no = run_no

    def add_samples(self, node, samples):
        # Add samples to latest run_data
        d = self.rd[node][self.run_no][-1]
        d.samples = samples

    def add_result(self, node, result):
        # Add result to latest run_data
        d = self.rd[node][self.run_no][-1]
        d.result = result

    def get_run_data_node(self, node, conditions):
        d = self.rd[node]
        test = lambda rd, k, v: rd[0].run_info[k] == v

        for key,val in conditions.items():
            d = filter(lambda rd: test(rd, key, val), d)
        return d


def dump_data(data, filename):
    f = open(filename, 'w')
    pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
    f.close()
