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
        self.pings = {}
        self.dests = []
        self.sources = []
        self.samples = []
        self.run_result = None
        self.run_error = False
        nodes.append(self)

        self.end = threading.Event()
        self.run_finished = threading.Event()
        self.daemon = True

    def stop(self):
        self.end.clear()

    def run(self):
        while not self.end.is_set():
            try:
                obj = interface.recv(self.socket)
                if obj:
                    self.handle(obj)
                else:
                    print("None from {0}".format(self.name))
                    break
            except KeyboardInterrupt:
                return
            except socket.timeout:
                continue
            except socket.error as e:
                print("Connection to {0} lost: {1}".format(self.name, e))
                self.socket = None
                return


        self.socket.close()

    def handle(self, obj):
        if obj.cmd is interface.PING_REPLY:
            self.handle_ping_reply(obj)

        elif obj.cmd is interface.RUN_RESULT:
            self.handle_run_result(obj)

        elif obj.cmd is interface.RUN_ERROR:
            self.handle_run_error(obj)

        elif obj.cmd is interface.SAMPLE:
            self.handle_sample(obj)

        elif obj.cmd is interface.SAMPLE_ERROR:
            self.handle_sample_error(obj)

        else:
            print("Received unknown command from {0}: {1}".format(self.name, obj.cmd))

    def add_dest(self, node):
        self.dests.append(node)
        node.add_source(self)

    def add_source(self, node):
        self.sources.append(node)

    def set_mesh(self, host, port=8877):
        self.mesh_host = host
        self.mesh_port = port

    def get_dests(self):
        return map(lambda n: {'name': n.name, 'host': n.mesh_host, 'port': n.mesh_port}, self.dests)

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1)
        self.socket.connect((self.host, self.port))
        self.start()

    def ping(self):
        t = time.time()
        self.pings[t] = t
        obj = interface.interface(interface.PING_REQUEST, t)
        interface.send(self.socket, obj)

    def prepare_run(self, protocol):
        if not self.sources:
            return
        interface.send_cmd(self.socket, interface.PREPARE_RUN, protocol)

    def start_run(self, run_info):
        self.samples = []
        self.run_error = False
        self.run_result = None
        self.run_finished.clear()
        run_info['dests'] = self.get_dests()
        interface.send_cmd(self.socket, interface.START_RUN, run_info)

    def wait_run(self):
        if not self.dests:
            return False

        while True:
            if self.run_finished.wait(1):
                break

        return self.run_error

    def finish_run(self):
        obj = interface.interface(interface.FINISH_RUN)
        interface.send(self.socket, obj)

    def get_result(self):
        return self.run_result

    def get_samples(self):
        return self.samples

    def handle_run_result(self, obj):
        print obj.val
        self.run_result = obj.val
        self.run_finished.set()

    def handle_run_error(self, obj):
        self.run_error = True
        print("Run failed on {0}: {1}".format(self.name, obj.val))
        self.run_finished.set()

    def handle_sample(self, obj):
        self.samples.append(obj.val)
        obj.val['node'] = self.name
        self.client.export_sample(obj.val)

    def handle_sample_error(self, obj):
        print("Sampling failed at {0}: {1}".format(self.name, obj.val))

    def handle_ping_reply(self, obj):
        now = time.time()
        t = obj.val
        if not self.pings.has_key(t):
            return

        print("Received ping from {0}: {1:5.3f}".format(self.name, now - t))
