import threading
import socket
import riddler_interface as interface

class sock(threading.Thread):
    def __init__(self):
        super(sock, self).__init__(None)
        self.socket = None

        # Allow other classes to subscribe to incoming data
        self.subscriptions = {}
        self.subscribers = []

        # State handling
        self.end = threading.Event()
        self.connected = threading.Event()
        self.name = "sock"
        self.lock = threading.Lock()
        self.start()

    def subscribe(self, caller, data_type, callback):
        if not data_type in self.subscriptions:
            self.subscriptions[data_type] = [callback]
        else:
            self.subscriptions[data_type].append(callback)

        if caller not in self.subscribers:
            self.subscribers.append(caller)

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((host, int(port)))
            self.socket.settimeout(.5)
        except socket.error as e:
            self.error = e
            self.socket = None
            return False
        else:
            self.connected.set()
            self.publish_connect()
            return True

    def disconnect(self):
        if self.socket:
            self.connected.clear()
            self.socket.close()
            self.socket = None
        self.publish_disconnect()

    def run(self):
        while not self.end.is_set():
            try:
                # Wait for GUI to start connection
                if not self.connected.wait(.5):
                    continue

                # Read data from controller
                obj = interface.recv(self.socket)
                if obj:
                    self.handle_obj(obj)
                else:
                    # Connected closed by remote, clean up
                    self.disconnect()
            except socket.timeout:
                continue
            except socket.error as e:
                self.disconnect()

    def stop(self):
        self.disconnect()
        self.end.set()

    def handle_obj(self, obj):
        self.publish_data(obj)

    def send(self, cmd, **vals):
        if not self.socket:
            return

        self.lock.acquire()
        interface.send_client(self.socket, cmd, **vals)
        self.lock.release()

    def publish_data(self, obj):
        if not obj.cmd in self.subscriptions:
            # No one is interested in the data
            return

        # Deliver the object to interested receivers
        for subscriber in self.subscriptions[obj.cmd]:
            subscriber(obj)

    def publish_disconnect(self):
        for subscriber in self.subscribers:
            subscriber.controller_disconnected()

    def publish_connect(self):
        for subscriber in self.subscribers:
            subscriber.controller_connected()

    def get_error(self):
        return self.error
