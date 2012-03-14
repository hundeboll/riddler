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
        self.server.running = True
        self.server.args = self.args
        self.server.server_bind()
        self.server.server_activate()

    def serve(self):
        while self.server.running:
            try:
                self.server.handle_request()
            except socket.error as e:
                print(e)
                continue
            except KeyboardInterrupt:
                print("Quit")
                return

    def stop(self):
        if self.server:
            self.server.running = False

class tcp_handler(SocketServer.BaseRequestHandler):
    # Prepare objects upon a new connection
    def setup(self):
        print("Connected to controller: {}".format(self.client_address))
        self.end = threading.Event()
        self.tester_clients = []
        self.tester_server = None
        self.lock = threading.Lock()
        self.sampler = sampler.sampler(self, self.server.args)
        self.setup = setup.setup()
        self.send_node_info()

    # Stop running threads before connection closes
    def finish(self):
        for client in self.tester_clients:
            print("Killing client")
            client.kill_client()
            if client.is_alive():
                client.join()

        if self.tester_server:
            print("Killing server")
            self.tester_server.kill()
            if self.tester_server.is_alive():
                self.tester_server.join()

        if self.sampler:
            print("Killing sampler")
            self.sampler.stop()
            if self.sampler.is_alive():
                self.sampler.join()

    # Read data from controller
    def handle(self):
        while not self.end.is_set():
            try:
                obj = interface.recv(self.request)
                if not obj:
                    break
                self.handle_cmd(obj)
            except socket.error as e:
                print("Connection to controller lost: {0}".format(e))
                break
            except KeyboardInterrupt:
                self.server.running = False
                break

    # Handle commands/data from controller
    def handle_cmd(self, obj):
        if obj.cmd is interface.PREPARE_RUN:
            self.prepare_run(obj)
        elif obj.cmd is interface.START_RUN:
            self.start_run(obj)
        elif obj.cmd is interface.FINISH_RUN:
            self.finish_run(obj)
        else:
            print("Received unknown command: {0}".format(obj.cmd))

    # Prepare this node for a new test run
    def prepare_run(self, obj):
        print("Prepare run")
        # Apply received configurations
        if not self.setup.apply_setup(obj.run_info):
            self.report(interface.node(interface.PREPARE_ERROR, error=self.setup.error))

        # Inform the sampler about the new run
        if not self.sampler.set_run_info(obj.run_info):
            self.report(interface.node(interface.PREPARE_ERROR, error=self.sampler.error))

        # (Re)start iperf server
        if self.tester_server:
            self.tester_server.kill()
        self.tester_server = tester.server(self.server.args, obj.run_info)

        # Wait for previous iperf clients to finish
        for client in self.tester_clients:
            client.join()

        # Prepare new iperf client threads
        self.tester_clients = []
        for node in obj.dests:
            client = tester.client(self, node, obj.run_info)
            self.tester_clients.append(client)

        # Report back to controller that we are ready
        self.report(interface.node(interface.PREPARE_DONE))

    def start_run(self, obj):
        print("Start run")
        for client in self.tester_clients:
            client.start()

        # If no clients exists, we don't want the controller to
        # wait for us, so we send an empty result immediately.
        if not self.tester_clients:
            obj = interface.node(interface.RUN_RESULT, result=None)
            self.report(obj)

    def finish_run(self, obj):
        print("Finish run")
        for client in self.tester_clients:
            client.kill_client()

        if self.tester_server:
            self.tester_server.kill()

        # Report back to controller that we are done
        self.report(interface.node(interface.FINISH_DONE))


    # Thread safe sender function
    def report(self, obj):
        self.lock.acquire()
        ret = interface.send(self.request, obj)
        self.lock.release()
        if not ret:
            self.end.set()
        return ret

    # Send our own information to the controller
    def send_node_info(self):
        args = self.server.args
        obj = interface.node(interface.NODE_INFO, mesh_host=args.mesh_host, mesh_port=args.mesh_port)
        self.report(obj)
