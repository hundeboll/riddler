import threading
import SocketServer
import riddler_interface as interface
import socket

class client(threading.Thread):
    def __init__(self, args):
        super(client, self).__init__(None)
        self.daemon = True
        self.name = "exporter"
        self.args = args

        self.server = ThreadedTCPServer((args.client_host, args.client_port), tcp_handler, bind_and_activate=False)
        self.server.allow_reuse_address = True
        self.server.timeout = 1
        self.server.server_bind()
        self.server.server_activate()
        self.server.clients = []
        self.server.nodes = []
        self.start()

    def stop(self):
        if self.server:
            self.server.shutdown()

    def run(self):
        self.server.serve_forever()

    def export_sample(self, node, sample):
        for client in self.server.clients:
            client.lock.acquire()
            client.export_sample(node, sample)
            client.lock.release()

    def export_result(self, node, run_info, result):
        for client in self.server.clients:
            client.lock.acquire()
            client.export_result(node, run_info, result)
            client.lock.release()


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class tcp_handler(SocketServer.BaseRequestHandler):
    def setup(self):
        self.lock = threading.Lock()
        self.server.clients.append(self)
        self.export_nodes(self.server.nodes)

    def finish(self):
        self.server.clients.remove(self)
        self.request.close()

    def handle(self):
        # self.request is the TCP socket connected to the client
        while True:
            try:
                data = self.request.recv(1024).strip()
                if not data:
                    break
                print "{} wrote:".format(self.client_address[0])
                print data
                # just send back the same data, but upper-cased
                self.request.send(data.upper())
            except socket.timeout:
                continue
            except socket.error as e:
                print("Export socket closed: {0}".format(e))
                break

    def export_sample(self, node, sample):
        interface.send_client(self.request, interface.CLIENT_SAMPLE, node=node, sample=sample)

    def export_result(self, node, run_info, result):
        interface.send_client(self.request, interface.CLIENT_RESULT, result=result, node=node, run_info=run_info)

    def export_nodes(self, nodes):
        nodes = [node.name for node in nodes]
        interface.send_client(self.request, interface.CLIENT_NODES, nodes=nodes)
