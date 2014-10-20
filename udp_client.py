#!/usr/bin/env python

import os
import sys
import socket
import time

if len(sys.argv) < 4:
    print("Usage: {} <dest> <pkt-len> <rate> [time]".format(sys.argv[0]))
    sys.exit(0)

udp_port = 6349
dest = sys.argv[1]
length = int(sys.argv[2])
rate = int(sys.argv[3])
stop = "STOP"
interval = 1/(1024*rate/length/8)

if len(sys.argv) >= 5:
    timeout = int(sys.argv[4])
else:
    timeout = 0

if len(sys.argv) >= 6:
    csv = True
else:
    csv = False

message = os.urandom(length)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
i = 0

if not csv:
    print("Sending datagrams of length {} bytes to {}".format(length, dest))

t0 = time.time()
s = interval
while True:
    try:
        s0 = time.time()
        sock.sendto(message, (dest, udp_port))
        i += 1
        time.sleep(max(0, interval + s))
        s = interval - (time.time() - s0)

        if timeout and time.time() > t0 + timeout:
            break

    except KeyboardInterrupt:
        break

    except socket.gaierror as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)

t1 = time.time()

for j in range(10):
    sock.sendto(bytes(stop, 'UTF-8'), (dest, udp_port))


t = t1 - t0
b = i*length
r = round(i*length*8/1014/t)

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
    print("Sent {} datagrams of total length {} kB in {}".format(i, round(b/1024), time_str))
    print("Rate: {} kbit/s".format(r))
