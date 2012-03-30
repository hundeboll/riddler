from PySide.QtCore import *
from PySide.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import threading
import networkx as nx

import riddler_interface as interface

class NetworkGraph(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.graph = nx.Graph()
        self.axes = None
        self.nodelist = {}
        self.node_size = 100

    def add_node(self, node, mac):
        self.lock.acquire()
        self.nodelist[mac] = node
        self.graph.add_node(mac)
        self.pos = nx.circular_layout(self.graph)
        if len(node)*250 > self.node_size:
            self.node_size = len(node)*250
        self.lock.release()

    def add_path(self, src, dst, tq):
        # Add packet to graph
        self.lock.acquire()
        if not self.graph.has_edge(src, dst):
            self.graph.add_edge(src, dst, weight=int(tq))
        else:
            self.graph[src][dst]['weight'] = int(tq)
        self.lock.release()

    def del_path(self, src, dst):
        self.lock.acquire()
        if self.graph.has_edge(src, dst):
            print("Remove edge {} -> {}".format(src, dst))
            self.graph.remove_edge(src, dst)
        self.lock.release()

    def paths_from(self, src):
        self.lock.acquire()
        edges = self.graph.edges([src])
        self.lock.release()
        return edges

    def _draw(self, filename=None):
        self.lock.acquire()
        colors = []
        labels = {}
        nodes = {}

        # Map mac to node
        for mac in self.graph.nodes():
            if mac not in self.nodelist:
                nodes[mac] = mac
            else:
                nodes[mac] = self.nodelist[mac]

        for (u,v,d) in self.graph.edges(data=True):
            colors.append(d['weight'])
            labels[(u,v)] = "{0}".format(d['weight'])


        nx.draw(self.graph, self.pos, self.axes, width=4, edge_cmap=plt.cm.Blues, with_labels=False, node_size=self.node_size)
        nx.draw_networkx_labels(self.graph, self.pos, nodes, ax=self.axes)
        nx.draw_networkx_edge_labels(self.graph, self.pos, edge_labels=labels, ax=self.axes)
        self.draw()

        self.lock.release()


class GuiGraph(FigureCanvas, NetworkGraph):
    def __init__(self, parent=None):
        NetworkGraph.__init__(self)
        self.fig = Figure(facecolor='w')
        self.axes = self.fig.add_subplot(111, frame_on=False, axisbg='w')
        self.axes.hold(False)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        self.startTimer(1000)

    def timerEvent(self, event):
        self._draw()

class topology(QWidget):
    def __init__(self, parent=None):
        super(topology, self).__init__(parent)
        self.topology_graph = GuiGraph(self)
        self.do_layout()

    def do_layout(self):
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.topology_graph)
        self.setLayout(self.layout)

    def set_socket(self, socket):
        self.socket = socket
        socket.subscribe(self, interface.CLIENT_NODES, self.add_nodes)
        socket.subscribe(self, interface.CLIENT_SAMPLE, self.add_sample)

    def controller_connected(self):
        pass

    def controller_disconnected(self):
        pass

    def add_nodes(self, obj):
        for node in obj.nodes:
            self.topology_graph.add_node(node['name'], node['mac'])

    def add_sample(self, obj):
        src = obj.sample['mac']
        dsts = obj.sample['nexthops']
        for dst,tq in dsts.items():
            self.topology_graph.add_path(src, dst, tq)

        for dst in self.topology_graph.paths_from(src):
            if dst[1] not in dsts.keys():
                print("Deleting path {} -> {}".format(src, dst))
                self.topology_graph.del_path(src, dst[1])
