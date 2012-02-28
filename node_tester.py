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
        self.timer = threading.Timer(run_info['test_time']*2, self.kill_client)
        self.end = threading.Event()
        self.daemon = True

    # Run the specified test in a separate thread
    def run(self):
        h = self.dest_node['host']
        t = str(self.run_info['test_time'])
        p = str(self.dest_node['port'])

        # Craft the iperf command depending on the given protocol
        if self.run_info['protocol'] == 'tcp':
            cmd = ["iperf", "-c", h, "-t", t, "-yc", "-p", p]
        elif self.run_info['protocol'] == 'udp':
            r = str(self.run_info['rate']*1024)
            cmd = ["iperf", "-c", h, "-u", "-b", r, "-t", t, "-p", p, "-yC"]

        # Start a little watchdog to make sure we don't hang here forever
        self.timer.start()

        # Start the client in a separate process and wait for it to finish
        print("Starting {0} client".format(self.run_info['protocol']))
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.running = True
        self.p.wait()
        self.running = False

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
            result = self.parse_udp_output(stdout)

        # Send back our result
        if result:
            self.report_result(result)

    # Brutally kill a running subprocesses
    def kill_client(self):
        # Make sure even have a running subprocess
        if not self.running:
            return

        try:
            # Ask politely first
            print("Terminating client (pid {0})".format(self.p.pid))
            self.p.terminate()

            # Ask again, if necessary
            if not self.p.poll():
                self.p.terminate()

            # No more patience, kill the damn thing
            if not self.p.poll():
                self.p.kill()
        except OSError as e:
            print("Killing client failed: {0}".format(e))

        # We are done
        self.running = False

    # Screen scrape the output from a iperf TCP client
    def parse_tcp_output(self, output):
        # Remove trailing newlines and get the comma separated values
        output = output.strip()
        vals = output.split(",")

        # Now convert and format the results
        try:
            return {
                    'dest':         self.dest_node['name'],
                    'transfered':   int(vals[7])/8/1024,    # kB
                    'throughput':   int(vals[8])/1024,      # kbit/s
                    }
        except IndexError as e:
            print("Failed to parse result: {0}".format(e))
            self.report_error(output)
            return None

    # Screen scrape the output from a iperf UDP client
    def parse_udp_output(self, output):
        t = self.run_info['test_time']

        # Select 2nd line and get the comma separated values
        output = output.split()[1]
        vals = output.split(",")

        # Convert and format the results
        try:
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
            print("Failed to parse result: {0}".format(e))
            self.report_error(output)
            return None

    # Send back a result to the controller
    def report_result(self, result):
        obj = interface.node(interface.RUN_RESULT, result=result)
        self.controller.report(obj)

    # Send back an error to the controller
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

    # Run a iperf server in a separate thread
    def run(self):
        h = self.args.mesh_host
        p =  str(self.args.mesh_port)

        # Craft the iperf command based on the protocol
        if self.protocol == "tcp":
            self.cmd = ["iperf", "-s", "-B", h, "-p", p]
        elif self.protocol == "udp":
            self.cmd = ["iperf", "-s", "-u", "-B", h, "-p", p]

        # Start the iperf server in a separate process and wait for it be killed
        print("Starting {0} server".format(self.protocol))
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
            print("Terminating server (pid {0})".format(self.p.pid))
            self.p.terminate()

            # Ask again if necessary
            if not self.p.poll():
                self.p.terminate()

            # No more patience, kill the damn thing
            if not self.p.poll():
                self.p.kill()
        except OSError as e:
            print("Killing server failed: {0}".format(e))

        # We are done here
        self.running = False
