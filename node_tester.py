import threading
import time
import re
import socket
import SocketServer
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
            cmd = ["iperf", "-c", h, "-u", "-b", r, "-t", t, "-yc", "-p", p, '-fk', "-xCDM"]

        output = interface.exec_cmd(cmd)

        if not output:
            self.report_error("No output received from command {0}".format(cmd))
            return
        elif "WARNING" in output:
            self.report_error(output)
            return
        elif self.run_info['protocol'] == 'tcp':
            result = self.parse_tcp_output(output)
        elif self.run_info['protocol'] == 'udp':
            result = self.parse_udp_output(output)

        if result:
            self.report_result(result)

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
            self.report_error(e)
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
            self.report_error(e)
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
        self.end = threading.Event()
        self.daemon = True
        self.start()
        time.sleep(1)

    def run(self):
        h = self.args.mesh_host
        p =  str(self.args.mesh_port)
        if self.protocol == "tcp":
            self.cmd = ["iperf", "-s", "-B", h, "-p", p]
        elif self.protocol == "udp":
            self.cmd = ["iperf", "-s", "-u", "-B", h, "-p", p]

        output = interface.exec_cmd(self.cmd)

    def kill(self):
        cmd = ["ps", "-ewo", "pid,cmd"]
        needle = " ".join(self.cmd)
        regex = "(\d+) {0}\n".format(needle)

        output = interface.exec_cmd(cmd)
        pids = re.findall(regex, output)

        for pid in pids:
            cmd = ["kill", pid]
            interface.exec_cmd(cmd)
