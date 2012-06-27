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
        self.args = args

    # Call the different setup functions
    def apply_setup(self, run_info):
        if not self.setup_batman(run_info):
            return False

        if not self.setup_tcp(run_info):
            return False

        if not self.setup_iface(run_info):
            return False

        return True

    # Apply the received configuration for batman-adv
    def setup_batman(self, run_info):
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
        # Make sure we actually need to do this
        if not run_info['protocol'] == 'tcp':
            return True

        # Write TCP window sizes
        window = run_info['tcp_window']
        self.write(ipv4_path)

        # Write and enable the selected algorithm
        algo = run_info['tcp_algo']
        self.write(ipv4_path + current_algo, algo)

        # Check if we succeeded
        if algo not in self.read(ipv4_path + current_algo):
            self.error = "Failed to set tcp algorithm: {0}".format(algo)
            return False

        return True

    def setup_iface(self, run_info):
        iface = self.args.wifi_iface
        state = "on" if run_info['promisc'] else "off"
        cmd = ['ip', 'link', 'set', 'dev', iface, 'promisc', state]
        r = subprocess.call(cmd)
        if r:
            return False

        if state == "on":
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
