import threading
import subprocess
import time
import re
import riddler_interface as interface

class client(threading.Thread):
    def __init__(self, controller, dest_node, run_info):
        super(client, self).__init__(None)
        self.controller = controller
        self.dest_node = dest_node
        self.run_info = run_info
        self.running = False
        self.ping_p = None
        self.timer = threading.Timer(run_info['test_time']*2, self.kill_client)
        self.end = threading.Event()

    # Run the specified test in a separate thread
    def run(self):
        h = self.dest_node['host']
        t = str(self.run_info['test_time'])
        p = str(self.dest_node['port'])
        w = str(self.run_info['tcp_window'])

        # Craft the iperf command depending on the given protocol
        if self.run_info['protocol'] == 'tcp':
            cmd = ["iperf", "-c", h, "-t", t, "-yc", "-p", p, "-w", w]
        elif self.run_info['protocol'] == 'udp':
            r = str(self.run_info['rate']*1024)
            cmd = ["iperf", "-c", h, "-u", "-b", r, "-t", t, "-p", p, "-fk"]

        interval = str(int(t)/20.0)
        ping_cmd = ["/usr/bin/ping", "-i", interval, "-n", "-q", h]

        # Start a little watchdog to make sure we don't hang here forever
        self.timer.start()

        # Start the client in a separate process and wait for it to finish
        print("  Starting {0} client".format(self.run_info['protocol']))
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.ping_p = subprocess.Popen(ping_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.running = True
        self.p.wait()
        self.running = False

        # Stop ping and read output
        ping_result = self.kill_ping()

        # Read the output from iperf
        (stdout, stderr) = self.p.communicate()

        # Check and parse the output
        if stderr:
            self.report_error("Iperf client error: {0}".format(stderr))
            return
        elif not stdout:
            self.report_error("No output from command {0}".format(" ".join(cmd)))
            return
        elif self.run_info['protocol'] == 'tcp':
            result = self.parse_tcp_output(stdout)
        elif self.run_info['protocol'] == 'udp':
            result = self.parse_udp_human_output(stdout)

        # Send back our result
        if not ping_result or not result:
            e = "Missing result: ping:'{}' or iperf:'{}'".format(ping_result, result)
            print(e)
            self.report_error(e)
        else:
            result.update(ping_result)
            self.report_result(result)

    # Brutally kill a running subprocesses
    def kill_client(self):
        # Make sure even have a running subprocess
        if not self.running:
            return

        try:
            # Ask politely first
            print("  Terminating client (pid {0})".format(self.p.pid))
            self.p.terminate()

            # Ask again, if necessary
            if not self.p.poll():
                self.p.terminate()

            # No more patience, kill the damn thing
            if not self.p.poll():
                self.p.kill()
        except OSError as e:
            print("  Killing client failed: {0}".format(e))

        # We are done
        self.running = False

    def kill_ping(self, force=False):
        if not self.ping_p or self.ping_p.poll():
            print("  Ping not running")
            # Ping not running
            return

        if force:
            print("  Force ping to die")
            try:
                if not self.ping_p.poll():
                    self.ping_p.kill()
            except Exception as e:
                print("  Killing ping failed: {}".format(e))
            return

        self.ping_p.send_signal(2)
        (out,err) = self.ping_p.communicate()

        if err or not out:
            e = "Ping failed: {}".format(err)
            print(e)
            self.report_error(e)
            return None

        regex = re.compile("rtt min/avg/max/mdev = (?P<ping_min>\d*.?\d*)/(?P<ping_avg>\d*.?\d*)/(?P<ping_max>\d*.?\d*)/(?P<ping_mdev>\d*.?\d*) ms")
        stats = regex.search(out)

        regex = re.compile("(?P<ping_tx>\d+) packets transmitted, (?P<ping_rx>\d+) received,(?: \+(?P<ping_err>\d+) errors,)? (?P<ping_loss>\d+)% packet loss, time (?P<ping_time>\d+)ms")
        counts = regex.search(out)

        if counts and counts.group('ping_rx') == "0":
            # Ping didn't get anything through
            e = "  Ping failed to measure delay: {}".format(counts.groupdict)
            print(e)
            self.report_error(e)
            return None

        if not stats:
            e = "Parsing ping output failed: {}".format(out)
            print(e)
            self.report_error(e)
            return None

        s = stats.groupdict()
        c = counts.groupdict()
        return {
                'ping_min': float(s['ping_min']),
                'ping_avg': float(s['ping_avg']),
                'ping_max': float(s['ping_max']),
                'ping_mdev': float(s['ping_mdev']),
                'ping_tx': int(c['ping_tx']),
                'ping_rx': int(c['ping_rx']),
                'ping_loss': float(c['ping_loss']),
                'ping_time': float(c['ping_time']),
                'ping_err': int(0 if not d['ping_err'] else d['ping_err']),
                }

    # Screen scrape the output from a iperf TCP client
    def parse_tcp_output(self, output):
        # Now convert and format the results
        try:
            # Remove trailing newlines and get the comma separated values
            output = output.strip()
            vals = output.split(",")

            return {
                    'dest':         self.dest_node['name'],
                    'transfered':   int(vals[7])/8/1024,    # kB
                    'throughput':   int(vals[8])/1024,      # kbit/s
                    }
        except IndexError as e:
            print("  Failed to parse result: {0}".format(e))
            self.report_error(output)
            return None

    # Screen scrape the output from a iperf UDP client
    def parse_udp_output(self, output):
        t = self.run_info['test_time']

        # Convert and format the results
        try:
            # Select 2nd line and get the comma separated values
            output = output.split()[1]
            vals = output.split(",")

            return {
                    'dest':         self.dest_node['name'],
                    'transfered':   int(vals[7])/8/1024,    # kB
                    'throughput':   int(vals[7])*8/1024/t,  # kbit/s
                    'jitter':       float(vals[9]),         # seconds
                    'lost':         int(vals[10]),          # packets
                    'total':        int(vals[11]),          # packets
                    'ratio':        float(vals[12]),        # percent
                    }
        except IndexError as e:
            print("  Failed to parse result: {0}".format(e))
            self.report_error(output)
            return None

    # Screen scrape the output from a iperf UDP client
    def parse_udp_human_output(self, output):
        t = self.run_info['test_time']

        report = re.compile("\[\s*(?P<index>\d+)\].+sec\s+(?P<transfered>\d*.?\d+) KBytes +(?P<throughput>\d*.?\d+) Kbits/sec +(?P<jitter>\d+\.\d+) ms +(?P<lost>\d+)/ *(?P<packets>\d+) +\((?P<ratio>\d*\.?\d+)%\)")
        match = report.search(output)
        if not match:
            print("  Failed to parse result: {0}".format(output))
            self.report_error(output)
            return None

        try:
            vals = match.groupdict()
            return {
                    'dest':         self.dest_node['name'],
                    'transfered':   float(vals['transfered']),     # kB
                    'throughput':   float(vals['transfered'])*8/t, # Kbit/s
                    'jitter':       float(vals['jitter']),         # milliseconds
                    'lost':         int(vals['lost']),             # packets
                    'total':        int(vals['packets']),          # packets
                    'ratio':        float(vals['ratio']),          # percentage
                    }
        except Exception as e:
            err = "Failed to parse output: {}\n{}".format(e, output)
            print(err)
            self.report_error(err)
            return None

    # Send back a result to the controller
    def report_result(self, result):
        print("  Reporting result")
        obj = interface.node(interface.RUN_RESULT, result=result)
        self.controller.report(obj)

    # Send back an error to the controller
    def report_error(self, error):
        print("  Reporting error")
        obj = interface.node(interface.RUN_ERROR, error=error)
        self.controller.report(obj)


class server(threading.Thread):
    def __init__(self, args, run_info):
        super(server, self).__init__(None)
        self.args = args
        self.protocol = run_info['protocol']
        self.tcp_window = run_info['tcp_window']
        self.running = False
        self.end = threading.Event()
        self.start()

    # Run a iperf server in a separate thread
    def run(self):
        h = self.args.mesh_host
        p = str(self.args.mesh_port)
        w = str(self.tcp_window)

        # Craft the iperf command based on the protocol
        if self.protocol == "tcp":
            self.cmd = ["iperf", "-s", "-B", h, "-p", p, "-w", w]
        elif self.protocol == "udp":
            self.cmd = ["iperf", "-s", "-u", "-B", h, "-p", p]

        # Start the iperf server in a separate process and wait for it be killed
        print("  Starting {0} server".format(self.protocol))
        self.p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.running = True
        self.p.wait()

    # Kill a running iperf server
    def kill(self):
        # Check if process is running at all
        if not self.running:
            return

        try:
            # Politely ask server to quit
            print("  Terminating server (pid {0})".format(self.p.pid))
            self.p.terminate()

            # Ask again if necessary
            if not self.p.poll():
                self.p.terminate()

            # No more patience, kill the damn thing
            if not self.p.poll():
                self.p.kill()
        except OSError as e:
            print("  Killing server failed: {0}".format(e))

        # We are done here
        self.running = False
