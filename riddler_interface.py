import cPickle as pickle
import struct
import socket
import sys
import subprocess
import termios
import tty

NODE_INFO, PREPARE_RUN, PREPARE_DONE, PREPARE_ERROR, START_RUN, RUN_RESULT, RUN_ERROR, FINISH_RUN, FINISH_DONE, SAMPLE, SAMPLE_ERROR = range(11)
CLIENT_ARGS, CLIENT_EVENT, CLIENT_NODES, CLIENT_RESULT, CLIENT_SAMPLE, CLIENT_RUN_INFO = range(6)
CONNECTDED, DISCONNECTED, STOPPED, STARTED, PAUSED, UNPAUSED, RECOVERING, COMPLETED = range(8)

class node:
    def __init__(self, cmd, **vals):
        self.cmd = cmd
        for val in vals:
            setattr(self, val, vals[val])

class client:
    def __init__(self, cmd, **vals):
        self.cmd = cmd
        for val in vals:
            setattr(self, val, vals[val])

def send_node(sock, cmd, **vals):
    obj = node(cmd, **vals)
    return send(sock, obj)

def send_client(sock, cmd, **vals):
    obj = client(cmd, **vals)
    return send(sock, obj)

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

    try:
        while len(s) < l:
            s += sock.recv(l)
            if not s:
                return None
    except MemoryError as e:
        raise socket.error(1, "Invalid length: {} ({})".format(l, e))

    try:
        return pickle.loads(s)
    except KeyError as e:
        print("Unable to unpickle: {0}".format(e))
        return None

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

def get_keypress():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(sys.stdin.fileno())
    ch = sys.stdin.read(1)
    termios.tcsetattr(fd, termios.TCSANOW, old_settings)
    return ch
