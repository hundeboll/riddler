#!/usr/bin/env python3

import os
import sys
import time
import socket

udp_port = 6349
length = int(sys.argv[1])
count  = int(sys.argv[2])
csv    = int(sys.argv[3])
ack = "ACK".encode("utf-8")
stop = "STOP"

if len(sys.argv) == 3:
    csv = True
else:
    csv = False

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('', udp_port))

if not csv:
    print("Receiving datagrams of length {} bytes".format(length))

i = 0
b = 0
t0 = 0
t1 = 0
end = False
while True:
    try:
        for j in range(count):
            d, a = s.recvfrom(length)
            if d == bytes(stop, 'UTF-8'):
                if not t1:
                    continue

                end = True
                break

            if not t0:
                if not csv:
                    print("Received first datagram", flush=True)
                t0 = time.time()

            t1 = time.time()
            b += len(d)
            i += 1

        if end:
            break

        s.sendto(ack, a)
    except KeyboardInterrupt:
        break

t = t1 - t0
r = round(b*8/1014/t)

if t > 60*60:
    time_str = "{}h {:2}m".format(int(t/60/60), int((t/60)%60))
else:
    time_str = "{}m {:2}s".format(int(t/60), int(t%60))

if csv:
    print("time: {}".format(round(t, 2)))
    print("bytes: {}".format(b))
    print("packets: {}".format(i))
    print("rate: {}".format(r))
else:
    print("Received {} datagrams of total length {} kB in {}".format(i, round(b/1024), time_str))
    print("Rate: {} kbit/s".format(r))
