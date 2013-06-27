import threading
import socket
import time
import copy
import re
import riddler_interface as interface

nodes = []

class node(threading.Thread):
    def __init__(self, name, host, port=8899):
        super(node, self).__init__(None)
        self.name = name
        self.host = host
        self.port = port
        self.mesh_host = ""
        self.mesh_port = 8877
        self.dests = []
        self.enable_ratio = False
        self.sources = []
        self.samples = []
        self.store_samples = False
        self.total_cpu = None
        self.total_idle = None
        self.run_result = None
        self.run_error = False
        nodes.append(self)

        self.end = threading.Event()
        self.reply = threading.Event()

    # Tell the main loop to stop
    def stop(self):
        # Stop any loops
        self.end.set()

        # Free waiters
        self.reply.set()

        # Close socket for faster quit
        if self.socket:
            self.socket.close()

    # Free waiters
    def pause(self):
        # Tell the controller that this run should be discarded
        self.run_error = True

        # Free the controller from waiting
        self.reply.set()

    # Thread main function
    def run(self):
        # Thread main loop
        while not self.end.is_set():
            try:
                # Try to connect this node
                self.connect()

                # Read data from node
                self.recv()
            except KeyboardInterrupt:
                # Someone pressed Ctrl-C
                self.stop()
                return
            except socket.timeout:
                # Timed out during connect. Try again
                continue
            except socket.error as e:
                # Something happened to the socket
                if e.errno != 0:
                    # Error number 0 is self made, so don't print it
                    print("{0}: {1}".format(self.name.title(), e))
                if e.errno in (1, 113, 111):
                    # Connection refused. Wait a bit
                    time.sleep(5)

                # Tell controller that something went wrong
                self.run_error = True
                self.socket = None
                self.reply.set()

    # Connect to configured node and start main loop
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Set timeout to 5 seconds to avoid too many reconnects.
        # (See exception handler in self.run()
        self.socket.settimeout(5)

        # Do the connect
        self.socket.connect((self.host, self.port))

        # Reduce timeout to avoid hanging in socket.read() while quitting
        self.socket.settimeout(.1)

    # Reconnect to node
    def reconnect(self):
        # Free waiting processes
        self.reply.set()

        if self.socket:
            # Closing the socket causes exception and reconnect in self.recv()
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except socket.error as e:
                if e.errno not in (107,9):
                    # We tried to close a non-connected socket
                    # Don't be too noisy
                    raise e

    # Keep receiving objects from the node until connection is closed
    def recv(self):
        # Loop while we are not told otherwise
        while not self.end.is_set():
            try:
                # Wait for data from the node
                obj = interface.recv(self.socket)
                if obj:
                    # Pass received object to the handler
                    self.handle(obj)
                else:
                    # Connection was closed.
                    # Raise an exception to cause reconnect in self.run()
                    raise socket.error(0, "Connection closed")
            except socket.timeout:
                # This happens all the time. Just try again
                continue

    # Handle objects received from the node
    def handle(self, obj):
        if obj.cmd is interface.NODE_INFO:
            self.handle_node_info(obj)

        elif obj.cmd is interface.PREPARE_DONE:
            self.handle_prepare_done(obj)

        elif obj.cmd is interface.PREPARE_ERROR:
            self.handle_prepare_error(obj)

        elif obj.cmd is interface.RUN_RESULT:
            self.handle_run_result(obj)

        elif obj.cmd is interface.RUN_ERROR:
            self.handle_run_error(obj)

        elif obj.cmd is interface.FINISH_DONE:
            self.handle_finish_done(obj)

        elif obj.cmd is interface.SAMPLE:
            self.handle_sample(obj)

        elif obj.cmd is interface.SAMPLE_ERROR:
            self.handle_sample_error(obj)

        else:
            print("Received unknown command from {0}: {1}".format(self.name, obj.cmd))

    # Configure a destination node for tests
    def add_dest(self, node):
        self.dests.append(node)

    def add_source(self, node):
        self.sources.append(node)

    # Return nicely formatted dictionary with destinations of this node
    def get_dests(self):
        return map(lambda n: {'name': n.name, 'host': n.mesh_host, 'port': n.mesh_port}, self.dests)

    # Set if this node should apply the ratio given by a run_info
    def set_enable_ratio(self, b):
        self.enable_ratio = b

    # Return result of current run
    def get_result(self):
        return self.run_result

    # Return received samples from current run
    def get_samples(self):
        if self.run_error:
            print("Sample error from {}".format(self.name))
            return None
        return self.samples

    # Wait for node to answer last command
    def wait(self):
        while not self.end.is_set():
            if self.reply.wait(.1):
                break
        if self.run_error:
            print("Wait error from {}".format(self.name))
        return self.run_error

    # Save information received from node
    def handle_node_info(self, obj):
        self.mesh_host = obj.mesh_host
        self.mesh_port = obj.mesh_port
        self.mesh_mac  = obj.mesh_mac
        self.reply.set()

    # Tell the node to prepare a new run
    def prepare_run(self, run_info):
        # Adjust rate according to ratio, if enabled
        run_info = copy.deepcopy(run_info)
        if self.enable_ratio and run_info['ratio']:
            run_info['rate'] = run_info['rate'] * run_info['ratio']/100

        if not self.sources and not self.dests:
            # Tell helpers that they are helpers
            run_info['role'] = 'helper'
        elif not self.sources and self.dests:
            run_info['role'] = 'destination'
        elif self.sources and not self.dests:
            run_info['role'] = 'source'

        self.samples = []
        self.run_info = run_info
        self.run_error = False
        self.run_result = None
        self.total_cpu = None
        self.total_idle = None
        self.reply.clear()

        interface.send_node(self.socket, interface.PREPARE_RUN, dests=self.get_dests(), run_info=run_info)

    # Set event to inform waiting callers
    def handle_prepare_done(self, obj):
        self.run_error = False
        self.reply.set()

    # Be verbose about errors occurring during while configuring the node
    def handle_prepare_error(self, obj):
        self.run_error = True
        print("Setup failed at {0}: {1}".format(self.name, obj.error))

    # Tell node to start a test run
    def start_run(self):
        self.reply.clear()
        self.store_samples = True
        interface.send_node(self.socket, interface.START_RUN)

    # Save received result and set event to inform waiting callers
    def handle_run_result(self, obj):
        if obj.result:
            self.run_result = obj.result

            # Send result to connected clients
            self.client.export_result(self.name, self.run_info, obj.result)
        self.reply.set()

    # Save received error and set event to inform waiting callers
    def handle_run_error(self, obj):
        self.run_error = True
        print("Run failed on {0}: {1}".format(self.name, obj.error))
        self.reply.set()

    # Tell node to clean up after test run
    def finish_run(self):
        self.reply.clear()
        interface.send_node(self.socket, interface.FINISH_RUN)

    # Set event to inform waiting callers
    def handle_finish_done(self, obj):
        self.store_samples = False
        self.reply.set()

    # Save received measurement sample for later extraction
    def handle_sample(self, obj):
        # Add name to sample
        obj.sample['node'] = self.name

        obj = self.parse_nc(obj)
        obj = self.parse_iw(obj)
        obj = self.parse_cpu(obj)
        obj = self.parse_fox(obj)

        # Only store sample if a test is running
        if self.store_samples:
            self.samples.append(obj.sample)

        # Send sample to connected clients
        self.client.export_sample(self.name, obj.sample)

    # Be verbose about sampling errors that not necessarily ruins the run result
    def handle_sample_error(self, obj):
        self.run_error = True
        print("Sampling failed at {0}: {1}".format(self.name, obj.error))

    def parse_nc(self, obj):
        if not hasattr(obj, 'nc'):
            return obj

        for line in obj.nc.splitlines():
            t = line.split(": ")
            key = "bat_" + t[0].lstrip()
            val = int(t[1])
            obj.sample[key] = val

        return obj

    def parse_iw(self, obj):
        if not hasattr(obj, 'iw'):
            return obj

        for line in obj.iw.splitlines():
            match = re.findall("\s+(.+):\s+(.+)", line)
            if not match:
                continue

            # We want integers to be integers
            try:
                # Try to convert
                val = int(match[0][1])

                # Okay, the convert did not fail, so compose the key
                key = "iw " + match[0][0]

                # Update or set the value for this counter
                if key in obj.sample:
                    obj.sample[key] += val
                else:
                    obj.sample[key] = val
            except ValueError:
                # The convert failed, so just use the string version
                pass

        return obj

    def parse_cpu(self, obj):
        if not hasattr(obj, 'cpu'):
            return obj

        # Save temporary values for later calculations
        last_cpu = self.total_cpu
        last_idle = self.total_idle

        # Parse the output
        line = obj.cpu.split("\n")[0]
        self.total_cpu = sum(map(lambda x: float(x), line.split()[1:]))
        self.total_idle = float(line.split()[4])
        if not last_cpu:
            obj.sample['cpu'] = 0
            return obj

        # Calculate the utilization since last sample
        total = self.total_cpu - last_cpu
        idle = self.total_idle - last_idle
        obj.sample['cpu'] = int(100*(total - idle)/total)

        return obj

    def parse_fox(self, obj):
        if not hasattr(obj, 'fox'):
            return obj

        for line in obj.fox.splitlines():
            t = line.split(": ")
            key = "rlnc " + t[0]
            val = int(t[1])
            if "recoder" in key:
                self.run_error = True
                print("Sample error on {}: Started acting as recoder".format(self.name))
            obj.sample[key] = val

        return obj
