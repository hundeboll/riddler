#!/usr/bin/env python2

import sys
import argparse
import node_server as server

parser = argparse.ArgumentParser(description="Riddler Node Application")
parser.add_argument("--config", default="node_defaults")
(args,dummy) = parser.parse_known_args()

try:
    c = __import__(args.config)
    defaults = dict((k, v) for k,v in c.__dict__.iteritems() if not k.startswith('__'))
except ImportError:
    print("Unable to load config file: {0}".format(args.config))
    sys.exit(1)

parser.add_argument("--wifi_iface")
parser.add_argument("--host", help="IP Address of interface to bind")
parser.add_argument("--port", type=int, help="Port number to listen on")
parser.add_argument("--mesh_host")
parser.add_argument("--mesh_port", type=int)
parser.add_argument("--fox_path", type=str)
parser.set_defaults(**defaults)
args = parser.parse_args()


class node:
    def __init__(self):
        self.server = server.server(args)
        self.server.create()
        self.server.serve()

if __name__ == "__main__":
    try:
        n = node()
    except KeyboardInterrupt:
        print("Quit")
