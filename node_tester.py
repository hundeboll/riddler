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
        self.end = threading.Event()
        self.daemon = True

    def run(self):
        h = self.dest_node['host']
        t = str(self.run_info['test_time'])
        p = str(self.dest_node['port'])

        if self.run_info['protocol'] == 'tcp':
            cmd = ["iperf", "-c", h, "-t", t, "-yc", "-p", p, '-fk']
        elif self.run_info['protocol'] == 'udp':
            r = str(self.run_info['rate']*1024)
            cmd = ["iperf", "-c", h, "-u", "-b", r, "-t", t, "-yc", "-p", p, '-fk', "-xDC"]

        print("Starting {0} client".format(self.run_info['protocol']))
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.running = True
        threading.Timer(self.kill_client, self.run_info['test_time'] + 5)
        self.p.wait()
        self.running = False
        (stdout, stderr) = self.p.communicate()

        if stderr:
            self.report_error("Iperf client error: {0}".format(stderr))
            return
        elif not stdout:
            self.report_error("No output received from command {0}".format(cmd))
            return
        elif self.run_info['protocol'] == 'tcp':
            result = self.parse_tcp_output(stdout)
        elif self.run_info['protocol'] == 'udp':
            result = self.parse_udp_output(stdout)

        if result:
            self.report_result(result)

    def kill_client(self):
        if not self.running:
            return
        print("Terminating client (pid {0}".format(self.p.pid))
        self.p.terminate()

        if not self.p.poll():
            self.p.terminate()

        self.running = False

    def parse_tcp_output(self, output):
        output = output.strip()
        vals = output.split(",")
        try:
            return {
                    'dest':         self.dest_node['name'],
                    'transfered':   int(vals[7]),           # bits
                    'throughput':   int(vals[8])/1024,      # kbit/s
                    }
        except IndexError as e:
            print("Failed to parse result: {0}".format(e))
            self.report_error(output)
            return None

    def parse_udp_output(self, output):
        output = output.strip()
        vals = output.split(",")
        try:
            return {
                    'dest':         self.dest_node['name'],
                    'transfered':   int(vals[7]),           # bits
                    'throughput':   int(vals[8])/1024,      # kbit/s
                    'jitter':       float(vals[9]),         # seconds
                    'lost':         int(vals[10]),          # packets
                    }
        except IndexError as e:
            print("Failed to parse result: {0}".format(e))
            self.report_error(output)
            return None

    def report_result(self, result):
        obj = interface.node(interface.RUN_RESULT, result=result)
        self.controller.report(obj)

    def report_error(self, error):
        obj = interface.node(interface.RUN_ERROR, error=error)
        self.controller.report(obj)


class server(threading.Thread):
    def __init__(self, args, protocol):
        super(server, self).__init__(None)
        self.args = args
        self.protocol = protocol
        self.running = False
        self.end = threading.Event()
        self.daemon = True
        self.start()

    def run(self):
        h = self.args.mesh_host
        p =  str(self.args.mesh_port)
        if self.protocol == "tcp":
            self.cmd = ["iperf", "-s", "-B", h, "-p", p]
        elif self.protocol == "udp":
            self.cmd = ["iperf", "-s", "-u", "-B", h, "-p", p]

        print("Starting {0} server".format(self.protocol))
        self.p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.running = True
        self.p.wait()

    def kill(self):
        try:
            # Check if process is running at all
            if not self.running:
                return

            # Politely ask server to quit
            print("Terminating server (pid {0})".format(self.p.pid))
            self.p.terminate()
            self.running = False

        except OSError as e:
            print("Killing server failed: {0}".format(e))
