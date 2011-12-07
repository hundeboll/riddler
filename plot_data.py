class data:
    def __init__(self, data):
        self.data = data

    def read_params(self):
        self.rates = self.data.get_param_range('rate')
        self.coding = self.data.get_param_range('coding')
        self.hold_times = self.data.get_param_range('hold')
        self.purge_times = self.data.get_param_range('purge')
        self.nodes = self.data.nodes
        self.sweep = self.data.sweep

    def throughput_test(self, node, coding):
        if len(self.hold_times) > 1 or len(self.purge_times) > 1:
            print("Data file has multiple dimensions, selecting first hold and purge times")

        conditions = {}
        conditions['hold'] = self.hold_times[0]
        conditions['purge'] = self.purge_times[0]
        conditions['coding'] = coding

        data = self.data.results(node, conditions, field='throughput')
        return self.rates, data

