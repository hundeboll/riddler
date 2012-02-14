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
        self.info = threading.Event()
        self.ready = threading.Event()
        self.done = threading.Event()
        self.run_finished = threading.Event()
        self.daemon = True

    # Tell the main loop to stop
    def stop(self):
        self.end.clear()

    def run(self):
        while not self.end.is_set():
            try:
                # Wait for data from the node
                obj = interface.recv(self.socket)
                if obj:
                    self.handle(obj)
                else:
                    print("None from {0}".format(self.name))
                    break
            except KeyboardInterrupt:
                break
            except socket.timeout:
                continue
            except socket.error as e:
                print("Connection to {0} lost: {1}".format(self.name, e))
                self.socket = None
                return

        self.socket.close()

    # Connect to configured node and start main loop
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1)
        try:
            self.socket.connect((self.host, self.port))
        except socket.error as e:
            print("Connection to {0} failed: {1}".format(self.name, e))

        # Start main loop
        self.start()

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

    # Wait for information about connected node
    def wait_node_info(self):
        self.info.wait()

    # Tell the node to prepare a new run
    def prepare_run(self, run_info):
        self.samples = []
        self.run_info = run_info
        self.run_error = False
        self.run_result = None
        self.run_finished.clear()
        self.ready.clear()
        self.done.clear()

        interface.send_node(self.socket, interface.PREPARE_RUN, dests=self.get_dests(), run_info=run_info)

    # Wait for node to report back
    def wait_prepare(self):
        while True:
            if self.ready.wait(1):
                break;

    # Tell node to start a test run
    def start_run(self):
        interface.send_node(self.socket, interface.START_RUN)

    # Wait for node to complete the test run
    def wait_start(self):
        # Only nodes with destinations execute test runs
        if not self.dests:
            return False

        while True:
            if self.run_finished.wait(1):
                break

        return self.run_error

    # Tell node to clean up after test run
    def finish_run(self):
        interface.send_node(self.socket, interface.FINISH_RUN)

    # Wait for node to clean up
    def wait_finish(self):
        while True:
            if self.ready.wait(1):
                break;

    # Return result of current run
    def get_result(self):
        return self.run_result

    # Return received samples from current run
    def get_samples(self):
        return self.samples

    # Save information received from node
    def handle_node_info(self, obj):
        print("Received node info from {}".format(self.name))
        self.mesh_host = obj.mesh_host
        self.mesh_port = obj.mesh_port
        self.info.set()

    # Set ready event to inform waiting callers
    def handle_node_ready(self, obj):
        self.ready.set()

    # Set done event to inform waiting callers
    def handle_node_done(self, obj):
        self.done.set()

    # Save received result and set run event to inform waiting callers
    def handle_run_result(self, obj):
        self.run_result = obj.result
        self.run_finished.set()
        self.client.export_result(self.name, self.run_info, obj.result)

    # Save received error and set run event to inform waiting callers
    def handle_run_error(self, obj):
        self.run_error = True
        print("Run failed on {0}: {1}".format(self.name, obj.error))
        self.run_finished.set()

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
