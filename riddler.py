#!/usr/bin/env python2

import sys
import argparse
import time
import riddler_interface as interface
import riddler_controller as controller
import riddler_client as client

parser = argparse.ArgumentParser(description="Riddler Controller Application")
parser.add_argument("--config", default="riddler_defaults")
(args,dummy) = parser.parse_known_args()

try:
    c = __import__(args.config)
    defaults = dict((k, v) for k,v in c.__dict__.iteritems() if not k.startswith('__'))
except ImportError:
    print("Unable to load config file: {0}".format(args.config))
    sys.exit(1)

parser.add_argument("--rate_start", type=int)
parser.add_argument("--rate_stop", type=int)
parser.add_argument("--rate_step", type=int)
parser.add_argument("--hold_time", type=int)
parser.add_argument("--hold_start", type=int)
parser.add_argument("--hold_stop", type=int)
parser.add_argument("--hold_step", type=int)
parser.add_argument("--purge_time", type=int)
parser.add_argument("--test_profile")
parser.add_argument("--test_time", type=int)
parser.add_argument("--test_sleep", type=int)
parser.add_argument("--test_loops", type=int)
parser.add_argument("--tcp_algos")
parser.add_argument("--sample_interval", type=int)
parser.add_argument("--nodes_file")
parser.add_argument("--data_file")
parser.add_argument("--client_port", type=int)
parser.add_argument("--client_host")
parser.set_defaults(**defaults)
args = parser.parse_args()


class riddler:
    def __init__(self, args):
        self.args = args
        self.client = client.client(self.args)
        self.load_nodes()
        self.connect_nodes()
        self.controller = controller.controller(self.args, self.nodes)
        self.controller.start()

    def stop(self):
        self.controller.stop()
        for node in self.nodes:
            node.stop()
        self.client.stop()

    def load_nodes(self):
        try:
            c = __import__(self.args.nodes_file)
            self.nodes = c.node.nodes
        except ImportError:
            print("Unable to load nodes file: {0}".format(nodes_file))

        # Add client object to each node
        for node in self.nodes:
            node.client = self.client

        # Add node objects to client server
        for node in self.nodes:
            self.client.server.nodes.append(node)

    def connect_nodes(self):
        for node in self.nodes:
            node.connect()

            # Wait for node to send back info
            node.wait_node_info()


if __name__ == "__main__":
    try:
        r = riddler(args)
        while True:
            if r.controller.test_finished.wait(1):
                break
    except KeyboardInterrupt:
        print("Quit")
    r.stop()
