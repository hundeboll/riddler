import numpy

class data:
    def __init__(self, data):
        self.data = data
        self.profile = self.data.profile
        self.codings = self.data.get_param_range('coding')

    def typed_nodes(self):
        relays = []
        sources = []
        for node in self.data.paths:
            if self.data.paths[node]:
                sources.append(node)
            else:
                relays.append(node)
        return sources,relays

    def throughput_udp(self, node, coding):
        conditions = {'coding': coding}

        rates = self.data.get_param_range('rate')
        data = self.data.results(node, conditions, field='throughput')
        return rates, data

    def coded(self, node):
        if not self.data.samples_has_field(node, 'nc Coded'):
            print("{0} has not sampled nc stats".format(node.title()))
            raise Exception("No sample")

        rates = self.data.get_param_range('rate')
        coded = self.data.samples_num(node, {'coding': True}, 'nc Coded')
        forwarded = self.data.samples_num(node, conditions, 'nc Forwarded')
        total = numpy.sum(coded, fowarded, axis=0)
        return rates,coded,fowarded,total

    def received(self, node, coding):
        if  self.data.samples_has_field(node, 'nc Received'):
            print("{0} has not sampled nc stats".format(node.title()))
            return False,False

        conditions = {'coding': coding}
        rates = self.data.get_param_range('rate')
        received = self.data.samples_num(node, conditions, 'nc Received')
        return rates,received
