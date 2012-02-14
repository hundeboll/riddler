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

        # Load data object
        self.data = data.data(nodes, args.test_profile)

        self.test_finished = threading.Event()
        self.end = threading.Event()
        self.daemon = True

    def stop(self):
        # Tell thread to stop
        self.end.clear()
        # Dump data to pickle file
        data.dump_data(self.data, self.args.data_file)

    def run(self):
        try:
            self.control()
        except KeyboardInterrupt:
            return

    def control(self):
        self.init_ranges()
        profile = self.args.test_profile

        # Select control function based on configured profile
        if profile in ("udp_rates","power_meas"):
            self.test_rates()

        elif profile == "tcp_algos":
            self.test_tcp_algos()

        elif profile == "hold_times":
            self.test_hold_times()

        else:
            print("Profile '{0}' not supported.".format(profile))
            return

        self.test_finished.set()

    # Control function to swipe UDP rates
    def test_rates(self):
        hold = self.args.hold_time
        purge = self.args.purge_time

        for loop in self.loops:
            for rate in self.rates:
                for coding in self.codings:
                    self.set_run_info(loop=loop, rate=rate, hold=hold, purge=purge, coding=coding)
                    self.execute_run()

    # Control function to swipe TCP congestion avoidance algorithms
    def test_tcp_algos(self):
        hold = self.args.hold_time
        purge = self.args.purge_time

        for loop in self.loops:
            for algo in self.args.tcp_algos:
                for coding in self.codings:
                    self.set_run_info(loop=loop, hold=hold, purge=purge, coding=coding, tcp_algo=algo)
                    self.execute_run()

    # Control function to swipe different hold times
    def test_hold_times(self):
        purge = self.args.purge_time

        for loop in self.loops:
            for hold in self.hold_times:
                self.set_run_info(loop=loop, hold=hold, purge=purge, coding=True)
                self.execute_run()

    # Control the state of each node and execute a single test run
    def execute_run(self):
        while True:
            time.sleep(self.args.test_sleep)
            self.prepare_run()

            # Wait for run to finish and check the result
            if not self.exec_run():
                # Rerun run if an error occurred
                print("Test failed, retrying.")
                self.finish_run()
                continue

            # Let the nodes clean up and save data
            self.finish_run()
            self.save_results()
            self.save_samples()

            # Update time left
            self.eta = self.eta - self.args.test_time
            break

    # Setup various ranges based on configured profile
    def init_ranges(self):
        args = self.args
        self.loops = range(args.test_loops)

        if args.test_profile in ('udp_rates', 'power_meas'):
            self.codings = [True, False]
            self.rates = range(args.rate_start, args.rate_stop+1, args.rate_step)
            self.eta = len(self.rates) * args.test_loops * (args.test_time + args.test_sleep) * len(self.codings)
            self.protocol = 'udp'
            self.run_info_format = "\n#{loop:2d}/{loops:2d} | {rate:4d} kb/s | Coding: {coding:1b} | ETA: {eta:3d}m"
            self.result_format = "{:10s} {throughput:6.1f} kb/s | {lost:4d}/{total:4d} ({ratio:4.1f}%)"

        if args.test_profile == 'hold_times':
            self.rates = range(args.rate_start, args.rate_stop+1, args.rate_step)
            self.hold_times = range(args.hold_start, args.hold_stop+1, args.hold_step)
            self.eta = len(self.rates) * len(self.hold_times) * args.test_loops * (args.test_time + args.test_sleep)
            self.protocol = 'udp'
            self.run_info_format = "\n#{loop:2d}/{loops:2d} | {rate:4d} kb/s | ETA: {eta:3d}m"
            self.result_format = "{:10s} {throughput:6.1f} kb/s | {lost:4d}/{total:4d} ({ratio:4.1f}%)"

        if args.test_profile == 'tcp_algos':
            self.protocol = 'tcp'
            self.codings = [True, False]
            self.eta = len(self.args.tcp_algos) * args.test_loops * (args.test_time + args.test_sleep) * len(self.codings)
            self.result_format = "{:10s} {throughput:6.1f} kb/s | {transfered:6.1f} kB"
            self.run_info_format = "\n#{loop:2d} | {tcp_algo:10s} | Coding: {coding:1b} | ETA: {eta:3d}m"

    # Configure the next run_info to be sent to each node
    def set_run_info(self, loop=None, rate=None, hold=None, purge=None, coding=None, tcp_algo=None):
        self.run_info = {}
        self.run_info['test_time'] = self.args.test_time
        self.run_info['sample_interval'] = self.args.sample_interval
        self.run_info['protocol'] = self.protocol
        self.run_info['tcp_algo'] = tcp_algo
        self.run_info['loop'] = loop
        self.run_info['rate'] = rate
        self.run_info['hold'] = hold
        self.run_info['purge'] = purge
        self.run_info['coding'] = coding
        self.print_run_info(self.run_info)

        # Update the data storage with the new run info
        self.data.new_run(self.run_info)

    # Tell each node to prepare a new run and wait for them to become ready
    def prepare_run(self):
        for node in self.nodes:
            node.prepare_run(self.run_info)

        for node in self.nodes:
            node.wait_prepare()

    # Perform a run on each node
    def exec_run(self):
        ret = True

        # Start it
        for node in self.nodes:
            node.start_run()

        # Wait for it to finish
        for node in self.nodes:
            # Check if an error occurred in the run
            if node.wait_start():
                ret = False

        return ret

    # Tell the nodes to clean up and wait for them to report back
    def finish_run(self):
        for node in self.nodes:
            node.finish_run()

        for node in self.nodes:
            node.wait_finish()

    # Store measured data
    def save_results(self):
        for node in self.nodes:
            result = node.get_result()
            # Some nodes don't measure results
            if not result:
                continue
            self.data.save_result(node.name, result)
            self.print_result(node, result)

    # Save sample measurements received during the test
    def save_samples(self):
        for node in self.nodes:
            samples = node.get_samples()
            self.data.append_samples(node.name, samples)

    # Report the result to the user
    def print_result(self, node, result):
        print(self.result_format.format(node.name.title(), **result))

    # Print info on the current test run
    def print_run_info(self, run_info):
        print(self.run_info_format.format(eta=self.eta/60, loops=self.args.test_loops-1, **run_info))
