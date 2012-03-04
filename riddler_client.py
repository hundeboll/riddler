import threading
import SocketServer
import riddler_interface as interface
import socket

class client(threading.Thread):
    def __init__(self, args):
        super(client, self).__init__(None)
        self.name = "exporter"

        # Start listening threaded TCP server and wait for clients
        self.server = ThreadedTCPServer((args.client_host, args.client_port), tcp_handler, bind_and_activate=False)
        self.server.allow_reuse_address = True
        self.server.timeout = .1
        self.server.server_bind()
        self.server.server_activate()
        self.server.args = args
        self.server.last_event = interface.STOPPED
        self.server.clients = []
        self.server.nodes = []
        self.server.riddler = None
        self.start()

    # Stop the TCP server
    def stop(self):
        if self.server:
            self.server.shutdown()

    # Start the server in a separate thread
    def run(self):
        self.server.serve_forever()

    def set_riddler(self, r):
        self.server.riddler = r

    def export_node(self, node):
        self.server.nodes.append(node)
        for client in self.server.clients:
            client.export_nodes([node])

    def export_event(self, event):
        self.server.last_event = event
        for client in self.server.clients:
            client.export_event(event)

    # Send a sample to each connected client
    def export_sample(self, node, sample):
        for client in self.server.clients:
            client.export_sample(node, sample)

    # Send a result to each connected client
    def export_result(self, node, run_info, result):
        for client in self.server.clients:
            client.export_result(node, run_info, result)


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class tcp_handler(SocketServer.BaseRequestHandler):
    # Prepare the class for a new connection
    def setup(self):
        self.lock = threading.Lock()
        self.server.clients.append(self)
        self.export_args(self.server.args)
        self.export_event(self.server.last_event)
        self.export_nodes(self.server.nodes)

    # Remove self from the list of connected clients on closed connection
    def finish(self):
        self.server.clients.remove(self)
        self.request.close()

    def handle(self):
        # self.request is the TCP socket connected to the client
        while True:
            try:
                # We currently don't expect anything from the client
                obj = interface.recv(self.request)
                if not obj:
                    break
                self.handle_obj(obj)
            except socket.timeout:
                continue
            except socket.error as e:
                print("Export socket closed: {0}".format(e))
                break

    def handle_obj(self, obj):
        if obj.cmd == interface.CLIENT_EVENT:
            self.handle_event(obj.event)
        else:
            print("Received unknown command")

    def handle_event(self, event):
        print("Received event: {}".format(event))
        if event == interface.STARTED:
            self.server.riddler.start()
        elif event == interface.STOPPED:
            self.server.riddler.stop_test()
        elif event == interface.PAUSED:
            self.server.riddler.set_pause(True)
        elif event == interface.UNPAUSED:
            self.server.riddler.set_pause(False)
        elif event == interface.RECOVERING:
            self.server.riddler.recover()
        else:
            print("Received unknown event")


    def send(self, cmd, **vals):
        self.lock.acquire()
        interface.send_client(self.request, cmd, **vals)
        self.lock.release()

    # Send sample to client
    def export_sample(self, node, sample):
        self.send(interface.CLIENT_SAMPLE, node=node, sample=sample)

    # Send result to client
    def export_result(self, node, run_info, result):
        self.send(interface.CLIENT_RESULT, result=result, node=node, run_info=run_info)

    # Send list of nodes to client
    def export_nodes(self, nodes):
        nodes = [node.name for node in nodes]
        self.send(interface.CLIENT_NODES, nodes=nodes)

    def export_args(self, args):
        self.send(interface.CLIENT_ARGS, args=args)

    def export_event(self, event):
        self.send(interface.CLIENT_EVENT, event=event)
        print("Sent event: {}".format(event))
