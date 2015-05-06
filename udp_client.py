#!/usr/bin/env python3

import os
import sys
import socket
import time

if len(sys.argv) < 5:
    print("Usage: {} <dest> <pkt-len> <rate> <time> <csv> <count>".format(sys.argv[0]))
    sys.exit(0)

udp_port = 6349
dest    = sys.argv[1]
length  = int(sys.argv[2])
rate    = int(sys.argv[3])
timeout = int(sys.argv[4])
csv     = int(sys.argv[5])
count   = int(sys.argv[6])
ack = "ACK"
stop = "STOP"
interval = 1/(1024*rate/length/8)
message = os.urandom(length)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
i = 0

if not csv:
    print("Sending datagrams of length {} bytes to {}".format(length, dest))

t0 = time.time()
s = interval
end = False
while True:
    try:
        for j in range(count):
            s0 = time.time()
            sock.sendto(message, (dest, udp_port))
            i += 1
            time.sleep(max(0, interval + s))
            s = interval - (time.time() - s0)

            if timeout and time.time() > t0 + timeout:
                end = True
                break

        if end:
            break

        d,a = sock.recvfrom(length)
        if d != bytes(ack, 'UTF-8'):
            raise Exception("unexpected ack: '{}'".format(d))

    except KeyboardInterrupt:
        break

    except socket.gaierror as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)

t1 = time.time()

for j in range(20):
    time.sleep(.2)
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
