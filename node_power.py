#!/usr/bin/env python2

import serial
import threading
import os
import time

class power(threading.Thread):
    def __init__(self, args):
        super(power, self).__init__(None)
        self.args = args

        self.name = 'power_meas'
        self.measure = threading.Event()
        self.end = threading.Event()
        self.daemon = True

        self.open_serial()

        self.start()


    def run(self):
        while not self.end.is_set():
            if not self.measure.wait(1):
                continue

            # This is where the reading of the serial link
            # should be done. Save the measurements into a
            # class variable ( e.g. self.measures.append(meas) ).

            time.sleep(1)

    def start_measure(self):
        self.measure.set()

    def stop_measure(self):
        self.measure.clear()

    def open_serial(self):
        if not os.path.exists(self.args.power_dev):
            self.error = "Power device '{0}' does not exist".format(self.args.power_dev)
            return False

        return True

    def read_power(self):
        # This is where the power measurements are returned to
        # the sampler class. Return only one value and reset the
        # stored data in this class ( e.g. self.measures = [] ).

        return 0;


if __name__ == "__main__":
    import node_defaults as args
    print args.power_dev
    p = power(args)
    p.start_measure()
    time.sleep(10)
    p.stop_measure()
