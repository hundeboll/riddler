import time
import threading
import riddler_interface as interface
import riddler_data as data

class controller(threading.Thread):
    def __init__(self, args, nodes):
        super(controller, self).__init__(None)
        self.name = "controller"
        self.args = args
        self.nodes = nodes
        self.data = data.data(nodes, args.test_sweep)
        self.test_finished = threading.Event()
        self.end = threading.Event()
        self.daemon = True

    def stop(self):
        self.end.clear()
        data.dump_data(self.data, self.args.data_file)

    def run(self):
        try:
            self.control()
        except KeyboardInterrupt:
            return

    def control(self):
        self.init_ranges()
        for loop in self.loops:
            for rate in self.rates:
                for hold in self.hold_times:
                    for purge in self.purge_times:
                        for coding in self.codings:
                            self.set_run_info(loop, rate, hold, purge, coding)
                            self.execute_run()

        self.test_finished.set()

    def execute_run(self):
        while True:
            self.prepare_run()
            self.start_run()
            if self.wait_run():
                print("Test failed, retrying.")
                self.finish_run()
                continue

            self.finish_run()
            self.save_results()
            self.save_samples()
            break

    def init_ranges(self):
        args = self.args
        self.loops = range(args.test_loops)

        if args.rate_step and args.test_protocol == "udp":
            self.rates = range(args.rate_start, args.rate_stop+1, args.rate_step)
        else:
            self.rates = [args.rate_start]

        if args.hold_step:
            self.hold_times = range(args.hold_start, args.hold_stop+1, args.hold_step)
        else:
            self.hold_times = [args.hold_start]

        if args.purge_step:
            self.purge_times = range(args.purge_start, args.purge_stop+1, args.purge_step)
        else:
            self.purge_times = [args.purge_start]

        if args.toggle_coding:
            self.codings = [True, False]
        else:
            self.codings = [args.coding]

    def set_run_info(self, loop, rate, hold, purge, coding):
        self.run_info = {}
        self.run_info['test_time'] = self.args.test_time
        self.run_info['test_protocol'] = self.args.test_protocol
        self.run_info['sample_interval'] = self.args.sample_interval
        self.run_info['loop'] = loop
        self.run_info['rate'] = rate
        self.run_info['hold'] = hold
        self.run_info['purge'] = purge
        self.run_info['coding'] = coding
        print self.run_info
        self.data.new_run(self.run_info)

    def prepare_run(self):
        for node in self.nodes:
            node.prepare_run(self.args.test_protocol)
        time.sleep(1)

    def start_run(self):
        for node in self.nodes:
            node.start_run(self.run_info)

    def wait_run(self):
        for node in self.nodes:
            if node.wait_run():
                return True

    def finish_run(self):
        for node in self.nodes:
            node.finish_run()

    def save_results(self):
        for node in self.nodes:
            result = node.get_result()
            if not result:
                continue
            self.data.save_result(node.name, result)

    def save_samples(self):
        for node in self.nodes:
            samples = node.get_samples()
            self.data.append_samples(node.name, samples)
