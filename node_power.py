#!/usr/bin/env python2

import serial
import threading
import os
import time

class power(threading.Thread):
    def __init__(self, args):
        super(power, self).__init__(None)
        self.args = args

        # State control
        self.end = threading.Event()
        self.data_lock = threading.Lock()

        # Temporary data storages
        self.measure_amp = []
        self.measure_volt = []
        self.avg_amp = None
        self.avg_volt = None
        self.avg_pwr = None

        self.open_serial()

        # Configure and start thread
        self.name = 'power_meas'
        self.start()

    def stop(self):
        self.end.set()

    # Main function of thread
    def run(self):
        # Main loop while we are not told to end
        while not self.end.is_set():
            if not self.ser:
                time.sleep(1)
                continue

            # Read from arduino
            try:
                data = self.ser.readline()
                if not data:
                    continue
            except OSError as e:
                print(e)
                continue
            meas = data.split()

            # Save measurement for later processing
            self.data_lock.acquire()
            try:
                self.measure_amp.append(float(meas[0])/1000)
                #self.measure_volt.append(meas[1])
                self.measure_volt.append(5)
            except ValueError as e:
                print(e)
            self.data_lock.release()

    # Prepare configured serial device for measuring
    def open_serial(self):
        self.ser = None

        # Check if device exists
        if (os.name == "posix") and not os.path.exists(self.args.power_dev):
                self.error = "Power device '{0}' does not exist".format(self.args.power_dev)
                print(self.error)
                return False

        # Open device and wait for it to settle
        print("Open serial device: {}".format(self.args.power_dev))
        self.ser = serial.Serial(self.args.power_dev, 9600, timeout=1)
        time.sleep(5) # FIXME: Arduino need ~5sec to start serial
        self.ser.flushInput()
        return True

    # Process the data measured since last read
    def process_data(self):
        # Don't measure while processing data
        self.data_lock.acquire()
        f_amp = self.measure_amp
        f_volt = self.measure_volt
        self.measure_amp = []
        self.measure_volt = []
        self.data_lock.release()

        # Make sure we got some data
        if not f_amp or not f_volt:
            return

        # Calculate average values
        self.avg_amp = sum(f_amp)/len(f_amp)
        self.avg_volt = sum(f_volt)/len(f_volt)
        self.avg_pwr = self.avg_amp * self.avg_volt

    # Read the total power usage since last read
    def read_power(self):
        return self.avg_pwr

    # Read the average ampere level since last read
    def read_amp(self):
        return self.avg_amp

    # Read the average volt level since last read
    def read_volt(self):
        return self.avg_volt


if __name__ == "__main__":
    import node_defaults as args

    print("Start power")
    p = power(args)
    print("Wait 20 secs")
    time.sleep(20)
    p.process_data()
    print("Read Power")
    print(p.read_power())
    print("Read Volt")
    print(p.read_volt())
    print("Read Amp")
    print(p.read_amp())
    p.stop.set()
