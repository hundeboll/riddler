import SocketServer
import socket
import threading
import time
import riddler_interface as interface
import node_tester as tester
#import node_sampler as sampler
import node_setup as setup
import subprocess
import os.path

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
        print("# Waiting for controller connection")
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
        print("  Connected to controller: {}".format(self.client_address))
        self.end = threading.Event()
        self.tester_clients = []
        self.tester_server = None
        self.lock = threading.Lock()
        #self.sampler = sampler.sampler(self, self.server.args)
        self.setup = setup.setup(self.server.args)
        self.send_node_info()

    # Stop running threads before connection closes
    def finish(self):
        print("# Disconnect from controller")
        for client in self.tester_clients:
            print("  Killing client")
            client.kill_client()
            #client.kill_ping(force=True)
            if client.is_alive():
                client.join()

        if self.tester_server:
            print("  Killing server")
            self.tester_server.kill()
            if self.tester_server.is_alive():
                self.tester_server.join()

        #if self.sampler:
        #    print("  Killing sampler")
        #    self.sampler.stop()
        #    if self.sampler.is_alive():
        #        self.sampler.join(1)
        #    if self.sampler.is_alive():
        #        print("  Sampler wouldn't die")

        print("  Closing connection")

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
        print("# Prepare run")
        self.run_info = obj.run_info
        # Apply received configurations
        if not self.setup.apply_setup(obj.run_info):
            self.report(interface.node(interface.PREPARE_ERROR, error=self.setup.error))

        # Inform the sampler about the new run
        #if not self.sampler.set_run_info(obj.run_info):
        #    print(self.sampler.error)
        #    self.report(interface.node(interface.PREPARE_ERROR, error=self.sampler.error))

        # (Re)start iperf server
        if self.tester_server:
            self.tester_server.kill()
        self.tester_server = tester.server(self.server.args, obj.run_info)

        # Wait for previous iperf clients to finish
        for client in self.tester_clients:
            print("  Waiting for clients")
            client.join()

        # Prepare new iperf client threads
        self.tester_clients = []
        for node in obj.dests:
            client = tester.client(self, node, obj.run_info)
            self.tester_clients.append(client)


        # Report back to controller that we are ready
        time.sleep(1)
        self.report(interface.node(interface.PREPARE_DONE))
        print("  Prepare done")

    def start_run(self, obj):
        print("# Start run")
        self.send_sample()

        for client in self.tester_clients:
            client.start()

        # If no clients exists, we don't want the controller to
        # wait for us, so we send an empty result immediately.
        if not self.tester_clients:
            print("  Sending dummy result")
            time.sleep(1)
            obj = interface.node(interface.RUN_RESULT, result=None)
            self.report(obj)
        print("  Run done")

    def finish_run(self, obj):
        print("# Finish run")
        self.send_sample(finish=True)

        for client in self.tester_clients:
            print("  Killing client")
            client.kill_client()

        if self.tester_server:
            print("  Killing server")
            self.tester_server.kill()

        # Report back to controller that we are done
        time.sleep(1)
        self.report(interface.node(interface.FINISH_DONE))
        print("  Finish done")

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
        mac = open("/sys/class/net/{}/address".format(args.wifi_iface)).read()
        obj = interface.node(interface.NODE_INFO, mesh_host=args.mesh_host, mesh_port=args.mesh_port, mesh_mac=mac)
        self.report(obj)

    def send_sample(self, finish=False):
        try:
            sample = {'timestamp': time.time()}

            # Sample bat stats
            print("  Sample bat stats")
            cmd = ["batctl", "s"]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
            p.wait()
            nc,d = p.communicate()

            # Sample iw
            print("  Sample iw")
            cmd = ["iw", "dev", self.server.args.wifi_iface, "station", "dump"]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
            p.wait()
            iw,d = p.communicate()

            # Sample cpu
            print("  Sample cpu")
            cpu = open("/proc/stat").read()

            # Sample fox
            if finish:
                fox = self.sample_fox()
            else:
                fox = ""

            print("  Send sample")
            sample = interface.node(interface.SAMPLE, sample=sample, nc=nc, iw=iw, cpu=cpu, fox=fox)
            self.report(sample)
        except Exception as e:
            err = interface.node(interface.SAMPLE_ERROR, error=e)
            self.report(err)

    def sample_fox(self):
        if self.run_info['role'] == 'helper' and self.run_info['coding'] == 'nohelper':
            return ""

        if self.run_info['coding'] in ("loss", "noloss"):
            return ""

        print(" Sample fox")
        cmd = ["{}/tools/counters".format(os.path.dirname(self.server.args.fox_path))]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        p.wait()
        fox,d = p.communicate()

        if d:
            print("Failed to sample fox")
            raise Exception("fox counters returned error")

        return fox
