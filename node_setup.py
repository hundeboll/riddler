import os
import subprocess
import riddler_interface as interface

bat_path = "/sys/class/net/bat0/mesh/"
nc_file = "network_coding"
hold_file = "nc_hold"
purge_file = "nc_purge"

tcp_path = "/proc/sys/net/ipv4/"
current_algo = "tcp_congestion_control"
available_algos = "tcp_available_congestion_control"

class setup:
    def __init__(self):
        self.error = None

    def apply_setup(self, run_info):
        if not self.setup_batman(run_info):
            pass
            #return False

        if not self.setup_tcp(run_info):
            return False

        return True

    def setup_batman(self, run_info):
        if not os.path.exists(bat_path):
            self.error = "'{0}' does not exist".format(bat_path)
            return False

        nc = 1 if run_info['coding'] else 0
        self.write(bat_path + nc_file, nc)
        self.write(bat_path + hold_file, run_info['hold'])
        self.write(bat_path + purge_file, run_info['purge'])

        return True

    def setup_tcp(self, run_info):
        if not run_info['protocol'] == 'tcp':
            return True

        algo = run_info['tcp_algo']
        self.write(tcp_path + current_algo, algo)
        if algo not in self.read(tcp_path + current_algo):
            self.error = "Failed to set tcp algorithm: {0}".format(algo)
            return False

        return True

    def read(self, path):
        f = open(path, "r")
        ret = f.read()
        f.close()
        return ret

    def write(self, path, value):
        f = open(path, "w")
        f.write(str(value))
        f.close()
