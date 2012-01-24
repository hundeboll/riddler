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
        self.run_info = None
        self.daemon = True
        self.controller = controller
        self.args = args

        self.total_cpu = None
        self.total_idle = None
        self.samples = {}

        self.power = power.power(args)

        self.end = threading.Event()
        self.sampling = threading.Event()
        self.start()

    def run(self):
        while not self.end.is_set():
            if not self.sampling.wait(1):
                continue

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

    def stop(self):
        self.end.set()

    def set_run_info(self, run_info):
        self.run_info = run_info
        return True

    def start_sampling(self):
        self.power.start_measure()
        self.sampling.set()

    def stop_sampling(self):
        self.power.stop_measure()
        self.sampling.clear()

    def report_samples(self):
        self.samples['timestamp'] = time.time()
        obj = interface.node(interface.SAMPLE, sample=self.samples)
        if not self.controller.report(obj):
            self.stop_sampling()
        self.samples = {}

    def report_error(self, error):
        obj = interface.node(interface.SAMPLE_ERROR, error = error)
        if not self.controller.report(obj):
            self.stop_sampling()

    def append_sample(self, sample):
        self.samples.update(sample)

    def sample_nc(self):
        sample = {}
        if not os.path.exists(nc_path):
            return

        cmd = ["cat", nc_path]
        output = interface.exec_cmd(cmd)
        if not output:
            return

        for line in output.split("\n"):
            match = re.findall("(.+):\s+(\d+)", line)
            if match:
                key = "nc " + match[0][0]
                sample[key] = int(match[0][1])

        self.append_sample(sample)

    def sample_iw(self):
        sample = {}
        cmd = ["iw", "dev", self.args.wifi_iface, "station", "dump"]
        output = interface.exec_cmd(cmd)
        if not output:
            return

        for line in output.split("\n"):
            match = re.findall("\s+(.+):\s+(\d+)", line)
            if match:
                key = "iw " + match[0][0]
                sample[key] = int(match[0][1])

        self.append_sample(sample)

    def sample_ip(self):
        cmd = ["ip", "-s", "-s", "link", "show", self.args.wifi_iface]
        output = interface.exec_cmd(cmd)
        if not output:
            return
        n = re.findall("\s+(\d+)", output)
        sample = {
                'ip_rx_bytes':         int(n[3]),
                'ip_rx_packets':       int(n[4]),
                'ip_rx_errors':        int(n[5]),
                'ip_rx_dropped':       int(n[6]),
                'ip_rx_overrun':       int(n[7]),
                'ip_rx_errors_length': int(n[9]),
                'ip_rx_errors_crc':    int(n[10]),
                'ip_rx_errors_frame':  int(n[11]),
                'ip_rx_errors_fifo':   int(n[12]),
                'ip_rx_errors_missed': int(n[13]),
                'ip_rx_bytes':         int(n[14]),
                'ip_rx_packets':       int(n[15]),
                'ip_rx_errors':        int(n[16]),
                'ip_rx_dropped':       int(n[17]),
                'ip_rx_carrier':       int(n[18]),
                'ip_rx_collsns':       int(n[19]),
                'ip_rx_errors_aborted':int(n[20]),
                'ip_rx_errors_fifo':   int(n[21]),
                'ip_rx_errors_window': int(n[22]),
                'ip_rx_errors_heartbeat': int(n[23])
                }
        self.append_sample(sample)

    def sample_cpu(self):
        cmd = ["cat", "/proc/stat"]
        cpu = interface.exec_cmd(cmd)
        if not cpu:
            return

        last_cpu = self.total_cpu
        last_idle = self.total_idle
        line = cpu.split("\n")[0]
        self.total_cpu = sum(map(lambda x: float(x), line.split()[1:]))
        self.total_idle = float(line.split()[4])
        if not last_cpu:
            return

        total = self.total_cpu - last_cpu
        idle = self.total_idle - last_idle
        sample = {'cpu': int(100*(total - idle)/total)}
        self.append_sample(sample)

    def sample_power(self):
        sample = {}
        sample['power'] = self.power.read_power()
        self.append_sample(sample)
