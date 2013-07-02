import os
import subprocess
import time
import riddler_interface as interface

bat_path = "/sys/class/net/bat0/mesh/"
nc_file = "network_coding"
hold_file = "nc_hold"
purge_file = "nc_purge"
loss_file = "packet_loss"

ipv4_path = "/proc/sys/net/ipv4/"
current_algo = "tcp_congestion_control"
available_algos = "tcp_available_congestion_control"
window_read = "tcp_rmem"
window_write = "tcp_wmem"

class setup:
    def __init__(self, args):
        self.error = None
        self.args = args

    def __del__(self):
        if hasattr(self, 'fox_process') and self.fox_process:
            print("  Killing current instance of fox")
            self.fox_process.terminate()
            del self.fox_process

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

    def check_fox(self):
        print("  Check fox")
        if not hasattr(self, "fox_process"):
            print("  no fox process")
            return False

        if not self.fox_process:
            print("  empty fox process")
            return False

        if self.fox_process.poll():
            print("  bad return value from fox process")
            del self.fox_process
            return False

        print("  fox is running")
        self.fox_process.terminate()
        del self.fox_process
        return True

    def setup_fox(self, run_info):
        if run_info['profile'] not in 'rlnc':
            return True

        if not os.path.exists(self.args.fox_path):
            self.error = "'{}' does not exist".format(self.args.fox_path)
            return False

        if hasattr(self, 'fox_process'):
            print("  Killing previous instance of fox")
            self.fox_process.terminate()
            del self.fox_process
            time.sleep(1)

        if run_info['coding'] == 'noloss':
            if os.path.exists(bat_path + loss_file):
                self.write(bat_path + loss_file, 0)
            e1 = 0
            e2 = 0
            e3 = 0
        elif run_info['coding'] == 'nohelper':
            e1 = 99
            e2 = 99
            e3 = run_info["errors"][2]
        else:
            if os.path.exists(bat_path + loss_file):
                self.write(bat_path + loss_file, 1)
            e1 = run_info["errors"][0]
            e2 = run_info["errors"][1]
            e3 = run_info["errors"][2]

        if run_info['coding'] == 'helper' and run_info['role'] == 'helper':
            run_info['fixed_overshoot'] = run_info['helper_overshoot']

        cmd = [self.args.fox_path]
        cmd += ["-generation_size", str(run_info["gen_size"])]
        cmd += ["-packet_size", str(run_info["packet_size"])]
        cmd += ["-e1", str(e1)]
        cmd += ["-e2", str(e2)]
        cmd += ["-e3", str(e3)]
        cmd += ["-encoders", str(run_info['encoders'])]
        cmd += ["-encoder_timeout", str(run_info['encoder_timeout'])]
        cmd += ["-decoder_timeout", str(run_info['decoder_timeout'])]
        cmd += ["-recoder_timeout", str(run_info['recoder_timeout'])]
        cmd += ["-helper_timeout", str(run_info['helper_timeout'])]
        cmd += ["-fixed_overshoot", str(run_info['fixed_overshoot'])]
        cmd += ["-ack_interval", str(run_info['ack_interval'])]
        cmd += ["-helper_threshold", str(run_info['helper_threshold'])]
        cmd += ["-packet_timeout_factor", str(run_info['packet_timeout_factor'])]
        cmd += ["-v", str(run_info['fox_verbose'])]
        cmd += ["-logtostderr", "0"];
        cmd += ["-colorlogtostderr", "0"];

        if run_info['coding'] == 'helper' and run_info['role'] == 'source':
            cmd += ["-systematic", str(run_info['systematic'])]

        print("  starting fox")
        self.fox_process = subprocess.Popen(cmd)
        time.sleep(1)

        if run_info['coding'] in ('loss', 'noloss'):
            print("  killing fox due to (no)loss")
            self.fox_process.terminate()
            del self.fox_process

        if run_info['coding'] == 'nohelper' and run_info['role'] == 'helper':
            print("  killing fox due to nohelper")
            self.fox_process.terminate()
            del self.fox_process

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
