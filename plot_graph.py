import os
import time
import pylab
import numpy
import threading
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_pdf import PdfPages
import riddler_interface as interface


c = {
    "aluminium1":   "#eeeeec",
    "aluminium2":   "#d3d7cf",
    "aluminium3":   "#babdb6",
    "aluminium4":   "#888a85",
    "aluminium5":   "#555753",
    "aluminium6":   "#2e3436",
    "butter1":      "#fce94f",
    "butter2":      "#edd400",
    "butter3":      "#c4a000",
    "chameleon1":   "#8ae234",
    "chameleon2":   "#73d216",
    "chameleon3":   "#4e9a06",
    "chocolate1":   "#e9b96e",
    "chocolate2":   "#c17d11",
    "chocolate3":   "#8f5902",
    "orange1":      "#fcaf3e",
    "orange2":      "#f57900",
    "orange3":      "#ce5c00",
    "plum1":        "#ad7fa8",
    "plum2":        "#75507b",
    "plum3":        "#5c3566",
    "scarletred1":  "#ef2929",
    "scarletred2":  "#cc0000",
    "scarletred3":  "#a40000",
    "skyblue1":     "#729fcf",
    "skyblue2":     "#3465a4",
    "skyblue3":     "#204a87",
}

bar_colors = {
        True:  [c["chameleon1"], c["chameleon3"], c["chameleon2"]],
        False: [c["skyblue1"], c["skyblue2"], c["skyblue3"]],
        }
label = {True: "With Coding", False: "Without Coding"}
color = {True: c["chameleon2"], False: c["skyblue2"]}

class graph:
    def __init__(self):
        self.figs = {}
        self.axes = {}
        self.bar_tops = {}
        self.bar_colors = {True: {}, False: {}}

    def show(self, plots):
        self.t = threading.Thread(None, self.hide)
        self.t.start()
        pylab.show()
        print("Show done")

    def hide(self):
        ch = interface.get_keypress()
        pylab.close('all')
        time.sleep(1)
        print("Closed")

    def save_figs(self, path):
        if not os.path.exists(path):
            print("Creating directory: {}".format(path))
            try:
                os.mkdir(path)
            except OSError as e:
                print("Unable to create direcoty: {}".format(e.strerror))
                return

        # Prepare for a single file with all plots
        p = "{}/all_plots.pdf".format(path)
        pdf_pages = PdfPages(p)

        for title in self.figs:
            for name,fig in self.figs[title].items():
                # Save plot to its own file
                filename = "{}/{}.pdf".format(path, title.lower().replace(' ', '_'))
                fig.savefig(filename, transparent=True, bbox_inches='tight', pad_inches=0)

                # Add plot to the one and only pdf
                pdf_pages.savefig(fig, transparent=True)

        # Save the teh single file
        pdf_pages.close()

    def setup_fig(self, name, title, xlabel, ylabel, projection=None):
        if title in self.figs and name in self.figs[title]:
            self.fig = self.figs[title][name]
            self.ax = self.axes[title][name]
            return self.fig

        self.fig = pylab.figure()
        if projection:
            self.ax = self.fig.add_subplot(111, projection=projection)
        else:
            self.ax = self.fig.add_subplot(111)
        self.ax.grid(True)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)

        if title in self.figs:
            self.figs[title][name] = self.fig
            self.axes[title][name] = self.ax
        else:
            self.figs[title] = {name: self.fig}
            self.axes[title] = {name: self.ax}

        return self.fig,self.ax

    def finish_fig(self, loc='upper left'):
        self.fig.gca().legend(loc=loc, shadow=True)

    def plot(self, x, y, l):
        self.fig.gca().plot(x, y, linewidth=2, label=l)

    def get_bar_tops(self, name, title, data, coding):
        if title not in self.bar_tops:
            self.bar_tops[title] = {}

        if name not in self.bar_tops[title]:
            l = len(data)
            self.bar_tops[title][name] = {True: numpy.zeros(l), False: numpy.zeros(l)}

        return self.bar_tops[title][name][coding]

    def update_bar_tops(self, name, title, data, coding):
        self.bar_tops[title][name][coding] += data

    def get_bar_args(self, node, coding, data):
        # Get next bar color
        if node not in self.bar_colors[coding]:
            self.bar_colors[coding][node] = bar_colors[coding].pop(0)
            self.bar_colors[not coding][node] = bar_colors[not coding].pop(0)

        width = .2
        color = self.bar_colors[coding][node]
        positions = range(len(data))
        if coding:
            positions = numpy.array(positions)+width
            label = "{} with Coding".format(node.title())
        else:
            label = "{} without Coding".format(node.title())

        return positions,data,width,color,label

    def plot_coded(self, node, data):
        if not len(data['coded']) or not len(data[fwd]):
            return

        self.setup_fig(
                name=node,
                title="Coded vs. Forwarded Packets for {}".format(node.title()),
                xlabel="Total Offered Load [kbit/s]",
                ylabel="Packets")

        self.plot(data['rates'], data['coded']/2, "Coded")
        self.plot(data['rates'], data['fwd'],   "Forwarded")
        self.plot(data['rates'], data['fwd'] + data['coded']/2, "Total")
        self.finish_fig()

    def plot_udp_system_throughput(self, data, coding):
        if not len(data['throughput']):
            return

        self.setup_fig(
                name='system',
                title="System Throughput",
                xlabel="Total Offered Load [kbit/s]",
                ylabel="Measured Throughput [kbit/s]")

        self.plot(data['rates'], data['throughput'], label[coding])
        self.finish_fig()

    def plot_throughput(self, node, data, coding):
        if not len(data['throughput']):
            return

        self.setup_fig(
                name=node,
                title="Throughput for {0}".format(node.title()),
                xlabel="Total Offered Load [kbit/s]",
                ylabel="Measured Throughput")

        self.plot(data['rates'], data['throughput'], label[coding])
        self.finish_fig()

    def plot_tx_packets(self, data, node):
        if not len(data['iw_tx_pkts']):
            return

        self.setup_fig(
                name='system',
                title="Packets Transmitted",
                xlabel="Total Offered Load [kbit/s]",
                ylabel="Packets")

        self.plot(data['rates'], data['iw_tx_pkts'], node.title())
        self.finish_fig()

    def plot_udp_ratio_throughput(self, node, data, coding):
        if not len(data['throughput']):
            return

        self.setup_fig(
                name=node,
                title="Throughput for {0}".format(node.title()),
                xlabel="Ratio [%]",
                ylabel="Offered Load [kbit/s]",
                projection='3d')

        x = data['throughput']['x']
        y = data['throughput']['y']
        z = data['throughput']['z']
        self.ax.set_zlabel('Throughput [kbit/s]')
        self.ax.plot_surface(x, y, z, rstride=1, cstride=1, color=color[coding])
        print label[coding]
        self.ax.legend((label[coding]))

    def plot_udp_ratio_power(self, node, data, coding):
        if not len(data['power']):
            return

        self.setup_fig(
                name=node,
                title="Power for {0}".format(node.title()),
                xlabel="Ratio [%]",
                ylabel="Offered Load [kbit/s]",
                projection='3d')

        x = data['power']['x']
        y = data['power']['y']
        z = data['power']['z']
        self.ax.set_zlabel('Power [W]')
        self.ax.plot_surface(x, y, z, rstride=1, cstride=1, color=color[coding])
        print label[coding]
        self.ax.legend((label[coding]))

    def plot_udp_ratio_coded(self, node, data):
        if not len(data['coded']):
            return

        self.setup_fig(
                name=node,
                title="Coded for {0}".format(node.title()),
                xlabel="Ratio [%]",
                ylabel="Offered Load [kbit/s]",
                projection='3d')

        x = data['coded']['x']
        y = data['coded']['y']
        z = data['coded']['z']
        self.ax.set_zlabel('Coded [packets]')
        self.ax.plot_surface(x, y, z, rstride=1, cstride=1, color=color[True])

    def plot_cpu(self, node, data, coding):
        if not len(data['cpu']):
            return

        self.setup_fig(
                name=node,
                title="CPU Usage for {}".format(node.title()),
                xlabel="Total offered load [kbit/s]",
                ylabel="CPU Usage [%]")
        self.ax.set_ylim(0,100)

        self.plot(data['rates'], data['cpu'], label[coding])
        self.finish_fig()

    def plot_power(self, node, data, coding):
        if not len(data['power']):
            return

        self.setup_fig(
                name=node,
                title="Power for {}".format(node.title()),
                xlabel="Offered load [kbit/s]",
                ylabel="Consumed Energy [W]")

        self.plot(data['rates'], data['power'], label[coding])
        self.finish_fig()

    def plot_udp_system_power(self, source_data, relay_data, coding):
        if not len(relay_data['power']) or not len(source_data['power']):
            return

        self.setup_fig(
                name='system',
                title="System Energy Consumption",
                xlabel="Total Offered Load [kbit/s]",
                ylabel="Consumed Energy [W]")
        x = source_data['rates'] + relay_data['rates']
        y = source_data['power'] + relay_data['power']
        self.plot(x, y, label[coding])
        self.finish_fig()

    def plot_udp_system_power_per_bit(self, source_data, relay_data, coding):
        if not source_data['power'].any() or not source_data['throughput'].any():
            return
        if not relay_data['power'].any() or not source_data['throughput'].any():
            return

        self.setup_fig(
                name='system',
                title="System Energy per Bit",
                xlabel="Total offered load",
                ylabel="Energy per Bit [J/b]")

        x = source_data['rates']
        w = source_data['power'] + relay_data['power']
        tp = source_data['throughput']
        tp *= 8 # From bytes to bits
        y = w/tp

        self.ax.set_yscale('log')
        self.plot(x, y, label[coding])
        self.finish_fig(loc="upper right")

    def plot_udp_mac_capture(self, data, coding):
        if not len(data['diffs']):
            return

        self.setup_fig(
                name='system',
                title="MAC Capture between Alice and Bob",
                xlabel="Offered Load [kbps]",
                ylabel="TX Difference [packets]")

        self.plot(data['rates'], data['diffs'], label[coding])
        self.finish_fig()

    def plot_udp_mac_capture_rx(self, node, data, coding):
        if not len(data['capture_rx']):
            return

        self.setup_fig(
                name=node,
                title="RX difference between Alice and Bob on {}".format(node.title()),
                xlabel="Offered Load [kbps]",
                ylabel="Difference [packets]")

        self.plot(data['rates'], data['capture_rx'], label[coding])
        self.finish_fig()

    def plot_udp_rx_coded_diff(self, node, data):
        if not len(data['coded_diff']):
            return

        self.setup_fig(
                name=node,
                title="Difference between RX and coded on {}".format(node.title()),
                xlabel="Offered Load [kbps]",
                ylabel="Difference [packets]")

        self.plot(data['rates'], data['coded_diff'], "With coding")
        self.finish_fig()

    def plot_tcp_throughput(self, node, data, coding):
        if not len(data['algos']) or not len(data['throughput']):
            return

        self.setup_fig(
                name= 'system',
                title="TCP Throughput",
                xlabel="Congestion Avoidance Algorithm",
                ylabel="Measured Throughput [kbit/s]")
        label_pos = numpy.array(range(len(data['algos'])))+.2
        self.ax.set_xticks(label_pos)
        self.ax.set_xticklabels(data['algos'])

        # Get values for bar plot
        bottoms = self.get_bar_tops('system', "TCP Throughput", data['throughput'], coding)
        left,height,width,color,label = self.get_bar_args(node, coding, data['throughput'])

        # Plot values and update the y-offset for next plot
        self.ax.bar(left, height, width, bottoms, ecolor='black', color=color, label=label)
        self.ax.legend(prop=dict(size=12), numpoints=1, loc='lower right')
        self.update_bar_tops('system', "TCP Throughput", data['throughput'], coding)

    def plot_tcp_window_throughput(self, node, data, coding):
        if not len(data['tcp_windows']) or not len(data['throughput']):
            return

        self.setup_fig(
                name='system',
                title="TCP Throughput",
                xlabel="Window size [bytes]",
                ylabel="Measured Throughput [kbit/s]")
        label_pos = numpy.array(range(len(data['tcp_windows'])))+.2
        self.ax.set_xticks(label_pos)
        self.ax.set_xticklabels(data['tcp_windows'])

        # Get values for bar plot
        bottoms = self.get_bar_tops('system', "TCP Throughput", data['throughput'], coding)
        left,height,width,color,label = self.get_bar_args(node, coding, data['throughput'])

        # Plot values and update the y-offset for next plot
        self.ax.bar(left, height, width, bottoms, ecolor='black', color=color, label=label)
        self.ax.legend(prop=dict(size=12), numpoints=1, loc='lower right')
        self.update_bar_tops('system', "TCP Throughput", data['throughput'], coding)
