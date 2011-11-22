import threading
import time
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
        self.timer = threading.Timer(run_info['test_time'], self.stop)
        self.daemon = True
        self.start()

    def run(self):
        h = self.dest_node['host']
        t = str(self.run_info['test_time'])
        p = str(self.dest_node['port'])
        r = str(self.run_info['rate']*1024)
        if self.run_info['test_protocol'] == 'tcp':
            cmd = ["iperf", "-c", h, "-t", t, "-yc", "-p", p]
        elif self.run_info['test_protocol'] == 'udp':
            cmd = ["iperf", "-c", h, "-u", "-b", r, "-t", t, "-yc", "-p", p]

        output = interface.exec_cmd(cmd)
        if output:
            self.parse_output(output)

    def parse_output(self, output):
        output = output.split("\n")
        if self.run_info['test_protocol'] == "udp":
            line = output[1]
        elif self.run_info['test_protocol'] == "tcp":
            line = output[0]
        vals = line.split(",")
        rate = int(vals[8])/1024
        self.report_result(rate)

    def stop(self):
        pass

    def report_result(self, rate):
        obj = interface.interface(interface.RUN_RESULT, {'throughput': rate, 'dest': self.dest_node['name']})
        if not self.controller.report(obj):
            self.stop()

    def report_error(self, error):
        obj = interface.interface(interface.RUN_ERROR, error)
        self.controller.report(obj)


class server(threading.Thread):
    def __init__(self, args, protocol):
        self.args = args
        self.protocol = protocol
        super(server, self).__init__(None)
        self.end = threading.Event()
        self.daemon = True
        self.start()

    def run(self):
        p =  str(self.args.mesh_port)
        if self.protocol == "tcp":
            cmd = ["iperf", "-s", "-p", p]
        elif self.protocol == "udp":
            cmd = ["iperf", "-s", "-u", "-p", p]

        output = interface.exec_cmd(cmd)

    def stop(self):
        pass
