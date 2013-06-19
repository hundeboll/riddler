import os
import subprocess
import riddler_interface as interface

bat_path = "/sys/class/net/bat0/mesh/"
nc_file = "network_coding"
hold_file = "nc_hold"
purge_file = "nc_purge"

ipv4_path = "/proc/sys/net/ipv4/"
current_algo = "tcp_congestion_control"
available_algos = "tcp_available_congestion_control"
window_read = "tcp_rmem"
window_write = "tcp_wmem"

class setup:
    def __init__(self, args):
        self.error = None
        self.fox_process = None
        self.args = args

    # Call the different setup functions
    def apply_setup(self, run_info):
        if not self.setup_batman(run_info):
            return False

        if not self.setup_tcp(run_info):
            return False

        if not self.setup_iface(run_info):
            return False

        if not self.setup_fox(run_info):
            return False

        return True

    def setup_fox(self, run_info):
        if run_info['profile'] not in 'rlnc':
            return True

        if not os.path.exists(self.args.fox_path):
            self.error = "'{}' does not exist".format(self.args.fox_path)
            return False

        if self.fox_process and not self.fox_process.poll():
            self.fox_process.kill()

        if run_info['coding'] is 'noloss':
            e1 = 0
            e2 = 0
            e3 = 0
        else:
            e1 = run_info["errors"][0]
            e2 = run_info["errors"][1]
            e3 = run_info["errors"][2]

        cmd = [self.args.fox_path]
        cmd += ["-generation_size", str(run_info["gen_size"])]
        cmd += ["-packet_size", str(run_info["packet_size"])]
        cmd += ["-e1", str(e1)]
        cmd += ["-e2", str(e2)]
        cmd += ["-e3", str(e3)]
        cmd += ["-logtostderr", "0"];
        cmd += ["-colorlogtostderr", "1"];

        print(cmd)
        self.fox_process = subprocess.Popen(cmd)

        if run_info['coding'] in ('loss', 'noloss'):
            self.fox_process.kill()

        return True

    # Apply the received configuration for batman-adv
    def setup_batman(self, run_info):
        if run_info['profile'] not in ('udp_rates', 'udp_ratios', 'tcp_algos', 'tcp_windows', 'hold_times', 'power_meas'):
            return True

        nc = 1 if run_info['coding'] else 0

        # Make sure batman-adv is enabled
        if not os.path.exists(bat_path):
            self.error = "'{0}' does not exist".format(bat_path)
            return False

        # Write the configuration
        if os.path.exists(bat_path + nc_file):
            self.write(bat_path + nc_file, nc)
        if os.path.exists(bat_path + hold_file):
            self.write(bat_path + hold_file, run_info['hold'])
        if os.path.exists(bat_path + purge_file):
            self.write(bat_path + purge_file, run_info['purge'])

        return True

    # Load and enable a TCP congestion avoidance algorithm
    def setup_tcp(self, run_info):
        if run_info['profile'] not in ('tcp_algos', 'tcp_windows'):
            return True

        # Make sure we actually need to do this
        if not run_info['protocol'] == 'tcp':
            return True

        # Write TCP window sizes
        window = run_info['tcp_window']
        self.write(ipv4_path + window_write, window)

        # Write and enable the selected algorithm
        algo = run_info['tcp_algo']
        self.write(ipv4_path + current_algo, algo)

        # Check if we succeeded
        if algo not in self.read(ipv4_path + current_algo):
            self.error = "Failed to set tcp algorithm: {0}".format(algo)
            return False

        return True

    def setup_iface(self, run_info):
        if run_info['profile'] not in ('udp_rates', 'udp_ratios', 'tcp_algos', 'tcp_windows', 'hold_times', 'power_meas'):
            return True
        iface = self.args.wifi_iface
        state = "on" if run_info['promisc'] else "off"
        cmd = ['ip', 'link', 'set', 'dev', iface, 'promisc', state]
        r = subprocess.call(cmd)
        if r:
            return False

        cmd = ['iw', 'phy0', 'set', 'rts', str(run_info['rts'])]
        r = subprocess.call(cmd)
        if r:
            return False

        if state == "on" and os.path.exists("/sys/class/net/mesh0"):
            if not os.path.exists("/sys/class/net/mon0"):
                cmd = ["iw", "phy0", "interface", "add", "mon0", "type", "monitor", "flags", "none"]
                if interface.exec_cmd(cmd) == False:
                    self.error = "Failed to create mon0: {}".format(cmd)
                    return False

            cmd = ["ip", "link", "set", "dev", "mon0", "up"]
            if interface.exec_cmd(cmd) == False:
                self.error = "Failed to up mon0: {}".format(cmd)
                return False

            cmd = ["iw", "mon0", "del"]
            if interface.exec_cmd(cmd) == False:
                self.error = "Failed to del mon0: {}".format(cmd)
                return False

        return True

    # Read data from file
    def read(self, path):
        f = open(path, "r")
        ret = f.read()
        f.close()
        return ret

    # Write data to file
    def write(self, path, value):
        f = open(path, "w")
        f.write(str(value))
        f.close()
