import subprocess

bat_path = "/sys/class/net/bat0/mesh/"
nc_file = "network_coding"
hold_file = "nc_hold"
purge_file = "nc_purge"

class setup:
    def apply(self, run_info):
        nc = 1 if run_info['coding'] else 0
        self.write(bat_path + nc_file, nc)
        self.write(bat_path + hold_file, run_info['hold'])
        self.write(bat_path + purge_file, run_info['purge'])

    def write(self, path, value):
        f = open(path, "w")
        f.write(str(value))
        f.close()

    def exec_cmd(self, cmd):
        if sys.hexversion < 0x02070000:
            return self.compat_exec(cmd)

        try:
            return subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            self.report_error(e.output)
            return False

    def compat_exec(self, cmd):
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = p.communicate()
        if p.returncode:
            self.report_error(stderr)
            return False
        return stdout
