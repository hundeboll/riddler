import time
import threading
import riddler_interface as interface

class controller(threading.Thread):
    def __init__(self, args):
        super(controller, self).__init__(None)
        self.name = "controller"
        self.args = args
        self.run_info = {}

        self.error = False
        self.redo = False
        self.recover_timer = None
        self.end = threading.Event()
        self.pause = threading.Event()

    # Stop the controller
    def stop(self):
        # Tell thread to stop
        self.end.set()

    def set_pause(self, pause):
        if pause:
            self.pause.clear()
        else:
            self.pause.set()

    # Toggle the pause event to pause tests
    def toggle_pause(self):
        if self.pause.is_set():
            # Pause: on
            self.pause.clear()
            return True
        else:
            # Pause: off
            self.pause.set()
            return False

    # Sleep function that breaks, if controller is stopped
    def sleep(self, secs):
        for i in range(secs):
            time.sleep(1)
            if self.end.is_set():
                return True
        return False

    def run(self):
        # Disable pause
        self.pause.set()

        try:
            self.control()
        except KeyboardInterrupt:
            return

    def control(self):
        self.start_time = time.time()
        self.init_ranges()
        self.initial_eta = self.test_time * self.test_count
        profile = self.args.test_profile

        # Select control function based on configured profile
        if profile in ("udp_rates","power_meas"):
            self.test_rates()

        elif profile == "udp_ratios":
            self.test_ratios()

        elif profile == "tcp_algos":
            self.test_tcp_algos()

        elif profile == "tcp_windows":
            self.test_tcp_windows()

        elif profile == "hold_times":
            self.test_hold_times()

        else:
            print("Profile '{0}' not supported.".format(profile))
            return

        # Yeah, the test actually completed by itself
        if not self.end.is_set():
            total_time = time.time() - self.start_time
            print("Original ETA was {}".format(self.format_time(self.initial_eta)))
            print("Test completed in {}".format(self.format_time(total_time)))

    # Control function to swipe UDP rates
    def test_rates(self):
        hold = self.args.hold_time
        purge = self.args.purge_time

        for loop in self.loops:
            for rate in self.rates:
                for coding in self.codings:
                    self.set_run_info(loop=loop, rate=rate, hold=hold, purge=purge, coding=coding)
                    self.execute_run()

                    # Quit if we are told to
                    if self.end.is_set():
                        return

    # Control function to swipe ratios between
    def test_ratios(self):
        hold = self.args.hold_time
        purge = self.args.purge_time

        for loop in self.loops:
            for rate in self.rates:
                for ratio in self.ratios:
                    for coding in self.codings:
                        self.set_run_info(loop=loop, rate=rate, ratio=ratio, hold=hold, purge=purge, coding=coding)
                        self.execute_run()

                    if self.end.is_set():
                        return

    # Control function to swipe TCP congestion avoidance algorithms
    def test_tcp_algos(self):
        hold = self.args.hold_time
        purge = self.args.purge_time
        window = self.args.tcp_window

        for loop in self.loops:
            for algo in self.args.tcp_algos:
                for coding in self.codings:
                    self.set_run_info(loop=loop, hold=hold, purge=purge, coding=coding, tcp_algo=algo, tcp_window=window)
                    self.execute_run()

                    # Quit if we are told to
                    if self.end.is_set():
                        return

    # Control function to swipe TCP windows sizes
    def test_tcp_windows(self):
        hold = self.args.hold_time
        purge = self.args.purge_time
        tcp_algo = self.args.tcp_algo

        for loop in self.loops:
            for window in self.tcp_windows:
                for coding in self.codings:
                    self.set_run_info(loop=loop, hold=hold, purge=purge, coding=coding, tcp_window=window, tcp_algo=tcp_algo)
                    self.execute_run()

                    # Quit if we are told to
                    if self.end.is_set():
                        return

    # Control function to swipe different hold times
    def test_hold_times(self):
        purge = self.args.purge_time

        for loop in self.loops:
            for hold in self.hold_times:
                self.set_run_info(loop=loop, hold=hold, purge=purge, coding=True)
                self.execute_run()

                # Quit if we are told to
                if self.end.is_set():
                    return

    # Control the state of each node and execute a single test run
    def execute_run(self):
        while not self.end.is_set():
            # Make time stamp for use in ETA
            start = time.time()

            # Check if we should pause and rerun
            self.wait_pause()

            self.prepare_run()

            # Let the network settle before next test
            self.sleep(self.args.test_sleep)

            # Wait for run to finish and check the result
            self.print_run_info(self.run_info)
            self.exec_node()

            # Let the nodes clean up and save data
            self.finish_run()

            # Check if we should pause and rerun
            self.wait_pause()

            # Decide on the next action
            if self.end.is_set():
                # Quit
                return

            elif not self.error:
                # We always discard the first result after an error
                if self.redo:
                    print("Discarding result because of previous error")
                    self.redo = False
                    #continue

                # Successful test
                self.save_results()
                self.save_samples()

                # Update test count
                self.test_count -= 1
                self.test_time = int(time.time() - start)
                break

            else:
                # Test failed, run it again
                print("Redoing test")
                self.redo = True

    # Check if pause is requested and pause if so
    def wait_pause(self):
        # Check the user setting
        if self.pause.is_set():
            # Nope, we don't pause
            return False

        # Invalidate current run
        print("Error from pause")
        self.error = True

        # Pause until told otherwise
        print("Pausing")
        while not self.end.is_set():
            if self.pause.wait(.1):
                print("Continuing")
                break

    def restart_timer(self):
        # Start timer to recover from broken code!
        if self.recover_timer:
            self.recover_timer.cancel()
        self.recover_timer = threading.Timer(self.test_time*2, self.timeout)
        self.recover_timer.start()

    def timeout(self):
        print("Time out occurred. Recovering")
        self.recover()

    # Called by user or timer to recover
    def recover(self):
        # Invalidate the current run
        print("Error from recover")
        self.error = True

        # Restart timer to keep recovering
        self.restart_timer()

        # Reconnect nodes
        for node in self.nodes:
            node.reconnect()

    # Setup various ranges based on configured profile
    def init_ranges(self):
        args = self.args
        self.loops = range(args.test_loops)
        self.test_time = args.test_time + args.test_sleep

        if args.test_profile in ('udp_rates', 'power_meas'):
            self.codings = [True, False]
            self.rates = range(args.rate_start, args.rate_stop+1, args.rate_step)
            self.test_count = len(self.rates) * args.test_loops * len(self.codings)
            self.protocol = 'udp'
            self.run_info_format = "\n# Loop: {loop:2d}/{loops:<2d} | Rate: {rate:4d} kb/s | Coding: {coding:1b} | ETA: {eta:s}"
            self.result_format = "{:10s} {throughput:6.1f} kb/s {lost:4d}/{total:<4d} {ratio:4.1f}% {ping_avg:4.1f}ms"

        if args.test_profile == "udp_ratios":
            self.codings = [True, False]
            self.rates = range(args.rate_start, args.rate_stop+1, args.rate_step)
            self.ratios = range(args.ratio_start, args.ratio_stop+1, args.ratio_step)
            self.test_count = len(self.rates) * len(self.ratios) * args.test_loops * len(self.codings)
            self.protocol = 'udp'
            self.run_info_format = "\n# Loop: {loop:2d}/{loops:<2d} | Ratio: {ratio:02d}% | Rate: {rate:4d} kb/s | Coding: {coding:1b} | ETA: {eta:s}"
            self.result_format = "{:10s} {throughput:6.1f} kb/s {lost:4d}/{total:<4d} {ratio:4.1f}%"

        if args.test_profile == 'hold_times':
            self.rates = range(args.rate_start, args.rate_stop+1, args.rate_step)
            self.hold_times = range(args.hold_start, args.hold_stop+1, args.hold_step)
            self.test_count = len(self.rates) * len(self.hold_times) * args.test_loops
            self.protocol = 'udp'
            self.run_info_format = "\n#{loop:2d}/{loops:2d} | {rate:4d} kb/s | ETA: {eta:s}"
            self.result_format = "{:10s} {throughput:6.1f} kb/s | {lost:4d}/{total:4d} ({ratio:4.1f}%)"

        if args.test_profile == 'tcp_algos':
            self.protocol = 'tcp'
            self.codings = [True, False]
            self.test_count = len(self.args.tcp_algos) * args.test_loops * len(self.codings)
            self.result_format = "{:10s} {throughput:6.1f} kb/s | {transfered:6.1f} kB"
            self.run_info_format = "\n#{loop:2d} | {tcp_algo:8s} | Coding: {coding:1b} | ETA: {eta:s}"

        if args.test_profile == 'tcp_windows':
            self.protocol = 'tcp'
            self.codings = [True, False]
            self.tcp_windows = range(args.window_start, args.window_stop+1, args.window_step)
            self.test_count = len(self.codings) * len(self.tcp_windows) * args.test_loops
            self.result_format = "{:10s} {throughput:6.1f} kb/s | {transfered:6.1f} kB"
            self.run_info_format = "\n#{loop:2d} | Window {tcp_window:5} | Coding: {coding:1b} | ETA: {eta:s}"

    # Configure the next run_info to be sent to each node
    def set_run_info(self, loop=None, rate=None, hold=None, purge=None, coding=None, tcp_algo=None, tcp_window=None, ratio=None):
        self.update_run_no(loop)
        self.run_info['test_time'] = self.args.test_time
        self.run_info['sample_interval'] = self.args.sample_interval
        self.run_info['protocol'] = self.protocol
        self.run_info['tcp_algo'] = tcp_algo
        self.run_info['loop'] = loop
        self.run_info['rate'] = rate
        self.run_info['hold'] = hold
        self.run_info['purge'] = purge
        self.run_info['coding'] = coding
        self.run_info['tcp_window'] = tcp_window
        self.run_info['promisc'] = coding
        self.run_info['ratio'] = ratio
        self.run_info['rts'] = self.args.rts_threshold

        # Update the data storage with the new run info
        self.data.add_run_info(self.run_info)

    # Reset counter if new loop is entered, increment otherwise
    def update_run_no(self, loop):
        if not self.run_info or loop != self.run_info['loop']:
            # We are in a new loop
            self.run_info['run_no'] = 0
        else:
            # Same loop as before
            self.run_info['run_no'] += 1

    # Tell each node to prepare a new run and wait for them to become ready
    def prepare_run(self):
        # We start from a clean sheet
        self.error = False

        # Start timer to recover in case of failure
        self.restart_timer()

        for node in self.nodes:
            node.prepare_run(self.run_info)

        for node in self.nodes:
            node.wait()

    # Perform a run on each node
    def exec_node(self):
        # Start it
        for node in self.nodes:
            node.start_run()

        # Wait for it to finish
        for node in self.nodes:
            # Check if an error occurred in the run
            if node.wait():
                print("controller wait error from {}".format(node.name))
                self.error = True

        if self.error and not self.end.is_set():
            for node in self.nodes:
                node.reconnect()

    # Tell the nodes to clean up and wait for them to report back
    def finish_run(self):
        for node in self.nodes:
            node.finish_run()

        for node in self.nodes:
            node.wait()

        self.recover_timer.cancel()

    # Store measured data
    def save_results(self):
        for node in self.nodes:
            result = node.get_result()
            # Some nodes don't measure results
            if not result:
                continue
            self.data.add_result(node.name, result)
            self.print_result(node, result)

    # Save sample measurements received during the test
    def save_samples(self):
        for node in self.nodes:
            samples = node.get_samples()
            self.data.add_samples(node.name, samples)

    def format_time(self, total_time):
        if total_time > 60*60:
            time_str = "{}h {:2}m".format(int(total_time/60/60), int((total_time/60)%60))
        else:
            time_str = "{}m {:2}s".format(int(total_time/60), int(total_time%60))
        return time_str

    # Report the result to the user
    def print_result(self, node, result):
        print(self.result_format.format(node.name.title(), **result))

    # Print info on the current test run
    def print_run_info(self, run_info):
        if self.end.is_set():
            return

        eta = self.test_count * self.test_time
        if eta > 60*60:
            # Print ETA with hours
            eta = "{:d}h {:02d}m".format(eta/60/60, (eta/60)%60)
        else:
            # Print ETA with minutes
            eta = "{:d}m {:02d}s".format(eta/60, eta%60)

        print(self.run_info_format.format(eta=eta, loops=self.args.test_loops-1, **run_info))
