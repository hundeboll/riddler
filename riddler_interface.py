import pickle
import struct
import socket
import sys
import subprocess

PING_REQUEST, PING_REPLY, PREPARE_RUN, START_RUN, FINISH_RUN, RUN_RESULT, RUN_ERROR, SAMPLE, SAMPLE_ERROR = range(9)
CLIENT_NODES, CLIENT_RESULT, CLIENT_SAMPLE, CLIENT_RUN_INFO = range(4)

class node:
    def __init__(self, cmd, protocol=None, result=None, run_info=None, node=None, error=None, sample=None):
        self.protocol = protocol
        self.cmd = cmd
        self.result = result
        self.node = node
        self.run_info = run_info
        self.sample = sample
        self.error = error

class client:
    def __init__(self, cmd, run_info=None, node=None, nodes=None, result=None, sample=None):
        self.cmd = cmd
        self.run_info = run_info
        self.node = node
        self.nodes = nodes
        self.result = result
        self.sample = sample

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

def send_node(sock, cmd, protocol=None, result=None, run_info=None, _node=None, sample=None):
    obj = node(cmd, protocol=protocol, result=result, run_info=run_info, node=_node, sample=sample)
    return send(sock, obj)

def send_client(sock, cmd, result=None, run_info=None, node=None, nodes=None, sample=None):
    obj = client(cmd, result=result, run_info=run_info, node=node, nodes=nodes, sample=sample)
    return send(sock, obj)

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
