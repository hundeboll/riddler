#!/usr/bin/env python2

import threading
import socket
import riddler_interface as interface

class client:
    def __init__(self):
        self.socket = None
        self.end = threading.Event()
        self.connect()
        self.run()

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
        print obj.val

if __name__ == "__main__":
    try:
        c = client()
    except KeyboardInterrupt:
        pass
