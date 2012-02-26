import threading
import socket
import pickle
import time
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
        self.sources = []
        self.samples = []
        self.run_result = None
        self.run_error = False
        nodes.append(self)

        self.end = threading.Event()
        self.reply = threading.Event()
        self.daemon = True

    # Tell the main loop to stop
    def stop(self):
        # Stop any loops
        self.end.set()

        # Free waiters
        self.reply.set()

        # Close socket for faster quit
        if self.socket:
            self.socket.shutdown(socket.SHUT_RDWR)

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
                return
            except socket.timeout:
                # Timed out during connect. Try again
                continue
            except socket.error as e:
                # Something happened to the socket
                if e.errno != 0:
                    # Error number 0 is self made, so don't print it
                    print("{0}: {1}".format(self.name.title(), e))
                if e.errno == 111:
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
            self.socket.shutdown(socket.SHUT_RDWR)

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

        elif obj.cmd is interface.NODE_READY:
            self.handle_node_ready(obj)

        elif obj.cmd is interface.NODE_DONE:
            self.handle_node_done(obj)

        elif obj.cmd is interface.RUN_RESULT:
            self.handle_run_result(obj)

        elif obj.cmd is interface.RUN_ERROR:
            self.handle_run_error(obj)

        elif obj.cmd is interface.SAMPLE:
            self.handle_sample(obj)

        elif obj.cmd is interface.SAMPLE_ERROR:
            self.handle_sample_error(obj)

        elif obj.cmd is interface.PREPARE_ERROR:
            self.handle_setup_error(obj)

        else:
            print("Received unknown command from {0}: {1}".format(self.name, obj.cmd))

    # Configure a destination node for tests
    def add_dest(self, node):
        self.dests.append(node)

    # Return nicely formatted dictionary with destinations of this node
    def get_dests(self):
        return map(lambda n: {'name': n.name, 'host': n.mesh_host, 'port': n.mesh_port}, self.dests)

    # Tell the node to prepare a new run
    def prepare_run(self, run_info):
        self.samples = []
        self.run_info = run_info
        self.run_error = False
        self.run_result = None
        self.reply.clear()

        interface.send_node(self.socket, interface.PREPARE_RUN, dests=self.get_dests(), run_info=run_info)

    # Tell node to start a test run
    def start_run(self):
        self.reply.clear()
        interface.send_node(self.socket, interface.START_RUN)

    # Wait for node to complete the test run
    def wait(self):
        while not self.end.is_set():
            if self.reply.wait(.1):
                break
        return self.run_error

    # Tell node to clean up after test run
    def finish_run(self):
        self.reply.clear()
        interface.send_node(self.socket, interface.FINISH_RUN)

    # Return result of current run
    def get_result(self):
        return self.run_result

    # Return received samples from current run
    def get_samples(self):
        return self.samples

    # Save information received from node
    def handle_node_info(self, obj):
        self.mesh_host = obj.mesh_host
        self.mesh_port = obj.mesh_port
        self.reply.set()

    # Set ready event to inform waiting callers
    def handle_node_ready(self, obj):
        self.reply.set()

    # Set done event to inform waiting callers
    def handle_node_done(self, obj):
        self.reply.set()

    # Save received result and set run event to inform waiting callers
    def handle_run_result(self, obj):
        if obj.result:
            self.run_result = obj.result
            self.client.export_result(self.name, self.run_info, obj.result)
        self.reply.set()

    # Save received error and set run event to inform waiting callers
    def handle_run_error(self, obj):
        self.run_error = True
        print("Run failed on {0}: {1}".format(self.name, obj.error))
        self.reply.set()

    # Save received measurement sample for later extraction
    def handle_sample(self, obj):
        self.samples.append(obj.sample)
        self.client.export_sample(self.name, obj.sample)

    # Be verbose about sampling errors that not necessarily ruins the run result
    def handle_sample_error(self, obj):
        print("Sampling failed at {0}: {1}".format(self.name, obj.error))

    # Be verbose about errors occurring during while configuring the node
    def handle_setup_error(self, obj):
        print("Setup failed at {0}: {1}".format(self.name, obj.error))
