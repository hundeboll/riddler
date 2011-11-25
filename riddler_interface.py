import pickle
import struct
import socket
import sys
import subprocess

PING_REQUEST, PING_REPLY, PREPARE_RUN, START_RUN, FINISH_RUN, RUN_RESULT, RUN_ERROR, SAMPLE, SAMPLE_ERROR = range(9)
CLIENT_NODES, CLIENT_RESULT, CLIENT_SAMPLE, CLIENT_RUN_INFO = range(4)

def tostruct(obj):
    return struct.pack("!L", len(obj))

def fromstruct(char):
    (l,) = struct.unpack("!L", char)
    return l

def send(sock, obj):
    if not sock:
        return False

    s = pickle.dumps(obj)
    l = tostruct(s)
    try:
        sock.send(l)
        sock.send(s)
        return True
    except KeyboardInterrupt:
        return False
    except socket.error as e:
        print("Connection lost: {0}".format(e))
        return False

def recv(sock):
    l = str()
    s = str()

    if not sock:
        return None

    while len(l) < 4:
        l += sock.recv(4)
        if not l:
            return None

    l = fromstruct(l)

    while len(s) < l:
        s += sock.recv(l)
        if not s:
            return None

    try:
        return pickle.loads(s)
    except KeyError as e:
        print("Unable to unpickle: {0}".format(e))
        return None

def send_cmd(sock, cmd, val=None):
    obj = interface(cmd, val)
    return send(sock, obj)

class interface:
    def __init__(self, cmd, val=None, run_info=None, node=None):
        self.cmd = cmd
        self.val = val
        self.run_info = run_info
        self.node = node


def exec_cmd(cmd):
    if sys.hexversion < 0x02070000:
        return compat_exec(cmd)

    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(e)
        return False

def compat_exec(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    if p.returncode:
        print(stderr)
        return False
    return stdout
