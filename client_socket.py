import threading
import socket
import riddler_interface as interface
import client_gui as gui

class sock(threading.Thread):
    def __init__(self, args):
        super(sock, self).__init__(None)
        self.daemon = True
        self.name = "sock"
        self.args = args

        self.gui = gui.main_window()

        self.socket = None
        self.end = threading.Event()
        self.connect()
        self.start()

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(('localhost', 6677))

    def run(self):
        while not self.end.is_set():
            try:
                obj = interface.recv(self.socket)
                if obj:
                    self.handle_obj(obj)
                else:
                    break
            except socket.timeout:
                continue
            except socket.error as e:
                print("Connection to riddler lost: {0}".format(e))
                return

    def stop(self):
        self.end.set()

    def handle_obj(self, obj):
        if obj.cmd is interface.CLIENT_NODES:
            self.handle_nodes(obj)

        elif obj.cmd is interface.CLIENT_RESULT:
            self.handle_result(obj)

        elif obj.cmd is interface.CLIENT_SAMPLE:
            self.handle_sample(obj)

        else:
            print("Received unknown command: {0}".format(obj.cmd))

    def handle_nodes(self, obj):
        for node in obj.val:
            self.gui.live_monitor.add_node(node)
            self.gui.test_monitor.add_node(node)

    def handle_sample(self, obj):
        node = obj.val['node']
        self.gui.live_monitor.add_sample(node, obj.val)

    def handle_result(self, obj):
        self.gui.test_monitor.add_result(obj.node, obj.run_info, obj.val)

    def handle_run_info(self, obj):
        node = obj.val['node']
        self.gui.test_monitor.add_run_info(node, obj.val)
