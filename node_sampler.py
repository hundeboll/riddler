import os
import threading
import time
import re
import subprocess
import riddler_interface as interface
#import node_power as power

nc_path = "/sys/kernel/debug/batman_adv/bat0/bat_stats"
orig_path = "/sys/kernel/debug/batman_adv/bat0/originators"

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
        #self.power = power.power(args)

        self.end = threading.Event()
        self.start()

    # Start the sampling in a separate thread
    def run(self):
        while not self.end.is_set():
            interval = self.run_info['sample_interval']
            # Do the sampling
            start = time.time()
            self.sample_nc()
            nc = time.time()
            self.sample_iw()
            iw = time.time()
            #self.sample_ip()
            #ip = time.time()
            self.sample_cpu()
            cpu = time.time()
            #self.sample_power()
            #self.sample_originators()
            #orig = time.time()
            self.report_samples()
            report = time.time()
            delay = interval - (time.time() - start)
            if delay > 0:
                time.sleep(delay)
            else:
                self.report_error("Missed deadline with {} seconds".format(delay*-interval))
                print("nc:     {}".format(nc - start))
                print("iw:     {}".format(iw - start))
                #print("ip:     {}".format(ip - start))
                print("cpu:    {}".format(cpu - start))
                #print("orig:   {}".format(orig - start))
                print("report: {}".format(report - start))

    # Stop the sampler thread
    def stop(self):
        self.end.set()
        #self.power.stop()
        #self.power.join()

    def run_cmd(self, cmd):
        self.cmd = cmd
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.recover_timer = threading.Timer(1, self.timeout_cmd)
        self.process.wait()
        (out,err) = self.process.communicate()
        if err:
            raise IOError(err)
        return out

    def timeout_cmd(self):
        if not self.process.poll():
            self.process.kill()
        self.report_error("Sample command timed out: {}".forma(self.cmd))

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

        # Read the file (why don't we just open() the file?)
        cmd = ["ethtool", "-S", "bat0"]
        try:
            output = self.run_cmd(cmd)
        except IOError as e:
            self.report_error(e)
            return

        # Parse the contents of the file
        for line in output.split("\n"):
            match = re.findall("\s+([a-z_]+):\s+(\d+)", line)
            if match:
                key = "bat_" + match[0][0]
                sample[key] = int(match[0][1])

        # Add some extra numbers
        sample['bat_nc_fwd_coded'] = sample['bat_nc_code'] + sample['bat_forward']

        # Add the sample to the set
        self.append_sample(sample)

    # Read stats from the wireless subsystem
    def sample_iw(self):
        sample = {}

        # Run the command
        cmd = ["iw", "dev", self.args.wifi_iface, "station", "dump"]
        try:
            output = self.run_cmd(cmd)
        except IOError as e:
            self.report_error(e)
            return

        # Parse the output
        for line in output.split('\n'):
            # Find the mac address for the next set of counters
            match = re.findall("((?:[0-9a-f]{2}:){5}[0-9a-f]{2})", line)
            if match:
                mac = "iw " + match[0]
                continue

            # Read out the counter for this line (for this mac)
            match = re.findall("\s+(.+):\s+(.+)", line)
            if not match:
                continue

            # Generate a key specific to this mac and counter
            mac_key = mac + " " + match[0][0]

            # We want integers to be integers
            try:
                # Try to convert
                val = int(match[0][1])

                # Okay, the convert did not fail, so compose the key
                key = "iw " + match[0][0]

                # Update or set the value for this counter
                if key in sample:
                    sample[key] += val
                else:
                    sample[key] = val
            except ValueError:
                # The convert failed, so just use the string version
                val = match[0][1]
            finally:
                # Set the value for this mac
                sample[mac_key] = val

        # Add the sample to the set
        self.append_sample(sample)

    # Sample stats from the IP subsystem
    def sample_ip(self):
        # Run the command
        cmd = ["ip", "-s", "-s", "link", "show", self.args.wifi_iface]
        try:
            output = self.run_cmd(cmd)
        except IOError as e:
            self.report_error(e)
            return

        # Remove first to lines
        for line in output.split("\n", 2):
            o = line

        # Parse the output
        n = re.findall("\s+(\d+)", o)
        sample = {
                'ip_rx_bytes':          int(n[0]),
                'ip_rx_packets':        int(n[1]),
                'ip_rx_errors':         int(n[2]),
                'ip_rx_dropped':        int(n[3]),
                'ip_rx_overrun':        int(n[4]),
                'ip_rx_errors_length':  int(n[6]),
                'ip_rx_errors_crc':     int(n[7]),
                'ip_rx_errors_frame':   int(n[8]),
                'ip_rx_errors_fifo':    int(n[9]),
                'ip_rx_errors_missed':  int(n[10]),
                'ip_tx_bytes':          int(n[11]),
                'ip_tx_packets':        int(n[12]),
                'ip_tx_errors':         int(n[13]),
                'ip_tx_dropped':        int(n[14]),
                'ip_tx_carrier':        int(n[15]),
                'ip_tx_collsns':        int(n[16]),
                'ip_tx_errors_aborted': int(n[17]),
                'ip_tx_errors_fifo':    int(n[18]),
                'ip_tx_errors_window':  int(n[19]),
                'ip_tx_errors_heartbeat': int(n[20]),
                }

        # Add the sample to the set
        self.append_sample(sample)

    # Sample CPU utilization
    def sample_cpu(self):
        # Run the command
        cpu = open("/proc/stat").read()
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

    def sample_originators(self):
        sample = {'nexthops': {}}
        if not os.path.exists(orig_path):
            return

        # Read the file (why don't we just open() the file?)
        output = open(orig_path).read()
        if not output:
            return

        sample['mac'] = re.findall("/([0-9a-f:]{17})", output)[0]
        nexthops = re.findall("(?P<orig>[0-9a-f:]{17}) +\d.\d{3}s +\((?P<tq>\d+)\) (?P=orig)", output)
        for nexthop in nexthops:
            sample['nexthops'][nexthop[0]] = nexthop[1]

        self.append_sample(sample)
