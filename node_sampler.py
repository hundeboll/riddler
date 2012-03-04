import sys
import os
import threading
import time
import subprocess
import riddler_interface as interface
import node_power as power
import re

nc_path = "/sys/kernel/debug/batman_adv/bat0/bat_stats"

class sampler(threading.Thread):
    def __init__(self, controller, args):
        super(sampler, self).__init__(None)
        self.run_info = {'sample_interval': 1}
        self.controller = controller
        self.args = args

        self.total_cpu = None
        self.total_idle = None
        self.samples = {}

        # The power sampler needs it own thread
        self.power = power.power(args)
        self.power.start_measure()

        self.end = threading.Event()
        self.start()

    # Start the sampling in a separate thread
    def run(self):
        while not self.end.is_set():
            # Do the sampling
            start = time.time()
            self.sample_nc()
            self.sample_iw()
            self.sample_ip()
            self.sample_cpu()
            self.sample_power()
            self.report_samples()
            delay = self.run_info['sample_interval'] - (time.time() - start)
            if delay > 0:
                time.sleep(delay)
            else:
                self.report_error("Missed deadline with {} seconds".format(delay*-1))

    # Stop the sampler thread
    def stop(self):
        self.end.set()

    # Get a new configuration
    def set_run_info(self, run_info):
        self.run_info = run_info
        return True

    # Send our samples to the controller
    def report_samples(self):
        self.samples['timestamp'] = time.time()
        obj = interface.node(interface.SAMPLE, sample=self.samples)
        self.controller.report(obj)

        # Reset our samples before a new run
        self.samples = {}

    # Send an error to the controller
    def report_error(self, error):
        print(error)
        obj = interface.node(interface.SAMPLE_ERROR, error = error)
        self.controller.report(obj)

    # Save a new set of samples
    def append_sample(self, sample):
        self.samples.update(sample)

    # Read stats from the batman-adv module
    def sample_nc(self):
        sample = {}
        if not os.path.exists(nc_path):
            return

        # Read the file (why don't we just open() the file?)
        cmd = ["cat", nc_path]
        output = interface.exec_cmd(cmd)
        if not output:
            return

        # Parse the contents of the file
        for line in output.split("\n"):
            match = re.findall("(.+):\s+(\d+)", line)
            if match:
                key = "nc " + match[0][0]
                sample[key] = int(match[0][1])

        # Add some extra numbers
        sample['nc FwdCoded'] = sample['nc Coded'] + sample['nc Forwarded']

        # Add the sample to the set
        self.append_sample(sample)

    # Read stats from the wireless subsystem
    def sample_iw(self):
        sample = {}

        # Run the command
        cmd = ["iw", "dev", self.args.wifi_iface, "station", "dump"]
        output = interface.exec_cmd(cmd)
        if not output:
            return

        # Parse the output
        # (implement support for multiple stations)
        for line in output.split("\n"):
            match = re.findall("\s+(.+):\s+(\d+)", line)
            if not match:
                continue

            key = "iw " + match[0][0]

            # Initialize fields to zero
            if not sample.has_key(key):
                sample[key] = 0

            # Sum fields from all stations
            # Should be saved individually, but then we must
            # now the names for each mac address.
            sample[key] += int(match[0][1])

        # Add the sample to the set
        self.append_sample(sample)

    # Sample stats from the IP subsystem
    def sample_ip(self):
        # Run the command
        cmd = ["ip", "-s", "-s", "link", "show", self.args.wifi_iface]
        output = interface.exec_cmd(cmd)
        if not output:
            return

        # Parse the output
        n = re.findall("\s+(\d+)", output)
        sample = {
                'ip_rx_bytes':          int(n[3]),
                'ip_rx_packets':        int(n[4]),
                'ip_rx_errors':         int(n[5]),
                'ip_rx_dropped':        int(n[6]),
                'ip_rx_overrun':        int(n[7]),
                'ip_rx_errors_length':  int(n[9]),
                'ip_rx_errors_crc':     int(n[10]),
                'ip_rx_errors_frame':   int(n[11]),
                'ip_rx_errors_fifo':    int(n[12]),
                'ip_rx_errors_missed':  int(n[13]),
                'ip_tx_bytes':          int(n[14]),
                'ip_tx_packets':        int(n[15]),
                'ip_tx_errors':         int(n[16]),
                'ip_tx_dropped':        int(n[17]),
                'ip_tx_carrier':        int(n[18]),
                'ip_tx_collsns':        int(n[19]),
                'ip_tx_errors_aborted': int(n[20]),
                'ip_tx_errors_fifo':    int(n[21]),
                'ip_tx_errors_window':  int(n[22]),
                'ip_tx_errors_heartbeat': int(n[23]),
                }

        # Add the sample to the set
        self.append_sample(sample)

    # Sample CPU utilization
    def sample_cpu(self):
        # Run the command
        cmd = ["cat", "/proc/stat"]
        cpu = interface.exec_cmd(cmd)
        if not cpu:
            return

        # Save temporary values for later calculations
        last_cpu = self.total_cpu
        last_idle = self.total_idle

        # Parse the output
        line = cpu.split("\n")[0]
        self.total_cpu = sum(map(lambda x: float(x), line.split()[1:]))
        self.total_idle = float(line.split()[4])
        if not last_cpu:
            return

        # Calculate the utilization since last sample
        total = self.total_cpu - last_cpu
        idle = self.total_idle - last_idle
        sample = {'cpu': int(100*(total - idle)/total)}

        # Add the sample to the set
        self.append_sample(sample)

    # Read power measurements from the separate thread
    def sample_power(self):
        sample = {}
        self.power.process_data()
        sample['power_watt'] = self.power.read_power()
        sample['power_amp'] = self.power.read_amp()
        sample['power_volt'] = self.power.read_volt()
        self.append_sample(sample)
