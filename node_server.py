import SocketServer
import pickle
import socket
import threading
import riddler_interface as interface
import node_tester as tester
import node_sampler as sampler
import node_setup as setup

class server:
    def __init__(self, args):
        self.args = args

    def create(self):
        self.server = SocketServer.TCPServer((self.args.host, self.args.port), tcp_handler, bind_and_activate=False)
        self.server.allow_reuse_address = True
        self.server.timeout = 1
        self.server.args = self.args
        self.server.server_bind()
        self.server.server_activate()

    def serve(self):
        try:
            self.server.serve_forever()
        except socket.error as e:
            print(e)
            pass

class tcp_handler(SocketServer.BaseRequestHandler):
    def setup(self):
        self.tester_server = None
        self.lock = threading.Lock()
        self.sampler = sampler.sampler(self, self.server.args)
        self.setup = setup.setup()

    def finish(self):
        if self.sampler:
            self.sampler.stop()

    def handle(self):
        while True:
            try:
                obj = interface.recv(self.request)
                if not obj:
                    break
                self.handle_cmd(obj)
            except socket.error as e:
                print("Connection to controller lost: {0}".format(e))
                break
            except KeyboardInterrupt:
                break

    def handle_cmd(self, obj):
        if obj.cmd is interface.PREPARE_RUN:
            print("Prepare run")
            if not self.tester_server:
                self.tester_server = tester.server(self.server.args, obj.protocol)

        elif obj.cmd is interface.START_RUN:
            print("Start run")
            run_info = obj.run_info
            self.setup.apply(run_info)
            self.sampler.start_sampling(run_info)
            self.tester_clients = []
            for node in run_info['dests']:
                self.tester_clients.append(tester.client(self, node, run_info))

        elif obj.cmd is interface.FINISH_RUN:
            print("Finish run")
            if self.sampler:
                self.sampler.stop_sampling()

        else:
            print("Received unknown command: {0}".format(obj.cmd))

    def report(self, obj):
        self.lock.acquire()
        ret = interface.send(self.request, obj)
        self.lock.release()
        return ret
