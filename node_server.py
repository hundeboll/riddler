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
        self.tester_clients = []
        self.tester_server = None
        self.lock = threading.Lock()
        self.sampler = sampler.sampler(self, self.server.args)
        self.setup = setup.setup()
        self.send_node_info()

    def finish(self):
        if self.sampler:
            self.sampler.stop()

        if self.tester_server:
            self.tester_server.kill()

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
            self.prepare_run(obj)

        elif obj.cmd is interface.START_RUN:
            print("Start run")
            self.sampler.start_sampling()
            for client in self.tester_clients:
                client.start()

        elif obj.cmd is interface.FINISH_RUN:
            print("Finish run")
            if self.sampler:
                self.sampler.stop_sampling()
            if self.tester_server:
                self.tester_server.kill()

            # Report back to controller that we are done
            self.report(interface.node(interface.NODE_DONE))

        else:
            print("Received unknown command: {0}".format(obj.cmd))

    def prepare_run(self, obj):
        print("Prepare run")
        if not self.setup.apply_setup(obj.run_info):
            self.report(interface.node(interface.PREPARE_ERROR, error=self.setup.error))

        if not self.sampler.set_run_info(obj.run_info):
            self.report(interface.node(interface.PREPARE_ERROR, error=self.sampler.error))

        # (Re)start iperf server
        if self.tester_server:
            self.tester_server.kill()
        self.tester_server = tester.server(self.server.args, obj.run_info['protocol'])

        # Wait for previous iperf clients to finish
        for client in self.tester_clients:
            client.join()

        # Prepare new client threads
        self.tester_clients = []
        for node in obj.dests:
            self.tester_clients.append(tester.client(self, node, obj.run_info))

        # Report back to controller that we are ready
        self.report(interface.node(interface.NODE_READY))

    def report(self, obj):
        self.lock.acquire()
        ret = interface.send(self.request, obj)
        self.lock.release()
        return ret

    def send_node_info(self):
        args = self.server.args
        obj = interface.node(interface.NODE_INFO, mesh_host=args.mesh_host, mesh_port=args.mesh_port)
        self.report(obj)
