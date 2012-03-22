#!/usr/bin/env python2

import sys
import argparse
import time
import riddler_interface as interface
import riddler_controller as controller
import riddler_client as client
import riddler_data as data

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
parser.add_argument("--ratio_start", type=int)
parser.add_argument("--ratio_stop", type=int)
parser.add_argument("--ratio_step", type=int)
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
parser.add_argument("--tcp_window", type=int)
parser.add_argument("--tcp_algo")
parser.add_argument("--window_start", type=int)
parser.add_argument("--window_stop", type=int)
parser.add_argument("--window_step", type=int)
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
        self.controller = None
        self.data = None

        # Start server thread to wait for clients
        self.client = client.client(self.args)
        self.client.set_riddler(self)

        # Load node objects from network config
        self.load_nodes()

        # Connect to nodes
        self.start_nodes()

    def start(self):
        # Create a data object for results and samples
        self.data = data.data(self.args)
        self.data.add_nodes(self.nodes)

        # Inform clients
        self.client.export_event(interface.STARTED)

        # Start test controller
        print("Starting test controller")
        self.controller = controller.controller(self.args)
        self.controller.nodes = self.nodes
        self.controller.data = self.data
        self.controller.start()

    # Tell the controller to stop and wait for it
    def stop_controller(self):
        if self.controller:
            self.controller.stop()
            self.controller.join()

    # Disconnect clients and wait for it
    def stop_client(self):
        if self.client:
            self.client.stop()
            self.client.join()

    # Disconnect nodes
    def stop_nodes(self):
        # End nodes threads
        for node in self.nodes:
            node.stop()

        # Wait for them to finish
        for node in self.nodes:
            node.join()

    # Stop a running test
    def stop_test(self):
        if not self.controller:
            return

        # Tell controller to stop
        print("Stopping test")
        self.controller.stop()

        # Inform clients
        self.client.export_event(interface.STOPPED)

        # Reconnect nodes to free controller
        for node in self.nodes:
            node.reconnect()

        # Wait for controller to finish
        self.controller.join()

    # Stop everything and quit program
    def quit(self):
        print("Quitting. Please wait...")
        print("Stopping nodes")
        self.stop_nodes()
        print("Stopping controller")
        self.stop_controller()
        print("Stopping client")
        self.stop_client()
        sys.exit(0)

    # Load the nodes configuration and distribute node references
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
            self.client.export_node(node)

    # Start node thread and wait for information from each node
    def start_nodes(self):
        for node in self.nodes:
            node.start()

        try:
            for node in self.nodes:
                node.wait()
        except KeyboardInterrupt:
            print("Quit")
            self.quit()

    def set_pause(self, pause):
        if not self.controller:
            return

        self.controller.set_pause(pause)
        for node in self.nodes:
            node.pause()
        if pause:
            self.client.export_event(interface.PAUSED)
        else:
            self.client.export_event(interface.UNPAUSED)

    # Clear the pause event in controller to pause current run
    def toggle_pause(self):
        if not self.controller:
            return

        print("Toggling pause")
        if self.controller.toggle_pause():
            self.client.export_event(interface.PAUSED)
        else:
            self.client.export_event(interface.UNPAUSED)
        for node in self.nodes:
            node.pause()

    # Recover by reconnecting nodes
    def recover(self):
        if not self.controller:
            return
        print("Recovering")
        self.controller.recover()

    def save_data(self):
        if not self.data:
            return
        # Read filename form console
        path = raw_input("Filename: (Hit enter for '{0}')\n".format(self.args.data_file))

        # If no name was entered, we use the configured one
        if not path:
            path = self.args.data_file

        # Dump data to pickle file
        data.dump_data(self.data, path)
        print("Data saved to '{0}'".format(path))

    def set_args(self, args):
        self.args = args
        self.controller.args = args


def print_help():
    print("")
    print("  t      Start test")
    print("  p      Toggle pause")
    print("  s      Stop test")
    print("  r      Recover")
    print("  d      Save data")
    print("  q      Quit")
    print("  h      Help")
    print("")


if __name__ == "__main__":
    r = riddler(args)

    try:
        print_help()
        while r:

            # Get a key from user
            c = interface.get_keypress()

            # Select action based on key pressed
            if c == 't':
                r.start()
            elif c == 'p':
                r.toggle_pause()
            elif c == 's':
                r.stop_test()
            elif c == 'r':
                r.recover()
            elif c == 'd':
                r.save_data()
            elif c == 'q':
                r.quit()
            else:
                print_help()

    except KeyboardInterrupt:
        print("Quitting")
        r.quit()
