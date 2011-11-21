import threading
import time
import socket
import SocketServer
import riddler_interface as interface

class client(threading.Thread):
    def __init__(self, controller, node, run_info):
        super(client, self).__init__(None)
        self.controller = controller
        self.node = node
        self.run_info = run_info
        self.end = threading.Event()
        self.timer = threading.Timer(run_info['test_time'], self.stop)
        self.daemon = True
        self.start()

    def run(self):
        if self.run_info['test_protocol'] == 'tcp':
            self.tcp_client()
        elif self.run_info['test_protocol'] == 'udp':
            self.udp_client()

    def tcp_client(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.node['host'], self.node['port']))
            self.socket.settimeout(1)
        except socket.error as e:
            print("Connecting to node failed: {0}".format(e))
            self.report_error(e)

        i = 0
        data = 'x' * (1500 - 40) # 802.1 payload minus IP/TCP headers
        self.timer.start()
        while not self.end.is_set():
            try:
                i += self.socket.send(data)
            except socket.timeout:
                print("TCP Test Timed Out")
                self.report_error("Node connection timed out")
                return
            except socket.error as e:
                print("TCP connection to node server lost: {0}".format(e))
                self.report_error(e)
                return

        self.socket.shutdown(socket.SHUT_WR)
        data = self.socket.recv(len("OK\n"))
        throughput = i*1500/1024/self.run_info['test_time']
        self.report_result(i)

    def udp_client(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect((self.node['host'], self.node['port']))

        # Calculate packets per second
        count = (self.run_info['rate'] * 1024.0)    # kbit/s to bits/s
        count /= 8.0                                # bits/s to bytes/s
        count /= (1500.0 - 28.0)                    # bytes/s to packets/s
        sleep = 1.0/count                           # packets/s to packet interval

        # 802.1 payload minus IP/UDP headers
        data = 'x' * (1500 - 28)

        # Transmit packets until stopped by timer
        self.timer.start()
        while not self.end.is_set():
            try:
                start = time.time()
                self.socket.send(data)
                time.sleep(sleep - (time.time() - start))
            except socket.error as e:
                print("Connection to node server lost: {0}".format(e))
                self.report_error(e)
                return
            except IOError as e:
                print("IOError: {0}".format(e))
                self.report_error(e)
                return

        self.udp_finish()

    def udp_finish(self):
        for x in range(10):
            try:
                self.socket.settimeout(.25)
                self.socket.send("\n")
                count = self.socket.recv(1024)
                result = int(count)*1500*8/1024/self.run_info['test_time']
                self.report_result(result)
                break
            except socket.timeout:
                continue
            except socket.error as e:
                self.report_error(e)
                break

    def stop(self):
        self.end.set()

    def report_result(self, rate):
        obj = interface.interface(interface.RUN_RESULT, {'throughput': rate, 'dest': self.node['name']})
        if not self.controller.report(obj):
            self.stop()

    def report_error(self, error):
        obj = interface.interface(interface.RUN_ERROR, error)
        self.controller.report(obj)


class server(threading.Thread):
    def __init__(self, args, protocol):
        self.args = args
        self.protocol = protocol
        super(server, self).__init__(None)
        self.end = threading.Event()
        self.daemon = True
        self.start()

    def run(self):
        if self.protocol == 'tcp':
            self.server = ThreadedTCPServer((self.args.mesh_host, self.args.mesh_port), tcp_handler, bind_and_activate=False)
        elif self.protocol == 'udp':
            self.server = SocketServer.UDPServer((self.args.mesh_host, self.args.mesh_port), udp_handler, bind_and_activate=False)

        self.server.allow_reuse_address = True
        self.server.timeout = 1
        self.server.server_bind()
        self.server.server_activate()
        try:
            self.server.serve_forever()
        except socket.error as e:
            pass

    def stop(self):
        try:
            if self.server:
                self.server.server_close()
        except KeyboardInterrupt:
            pass


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class tcp_handler(SocketServer.BaseRequestHandler):
    def handle(self):
        while True:
            try:
                data = self.request.recv(1024)
                if not data:
                    break
                del data
            except socket.timeout:
                continue
            except socket.error as e:
                print("Connection to node lost: {0}".format(e))
                return
            except KeyboardInterrupt:
                self.server.server_close()
                return

            self.request.send("OK\n")
            self.request.close()


class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    pass

class udp_handler(SocketServer.BaseRequestHandler):
    def handle(self):
        i = 0
        while True:
            try:
                data, address = self.request[1].recvfrom(1500)
                if not data:
                    break
                i += 1
                if data == "\n":
                    self.handle_finish(address, i)
                    break
                del data
            except socket.timeout:
                continue
            except socket.error as e:
                print("Connection to node lost: {0}".format(e))
                break

    def handle_finish(self, address, i):
        # If another newline is received, client did not receive our report
        for x in range(10):
            try:
                self.request[1].sendto(str(i), address)
                data = self.request[1].recvfrom(1024)
                if not data:
                    break
            except socket.timeout:
                # No new report was requested, so assume it was received
                break
            except socket.error as e:
                #print("Connection to node lost: {0}".format(e))
                break
