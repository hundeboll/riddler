import os
import time
import numpy
import threading
from matplotlib import pyplot
from matplotlib.mlab import griddata
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
        'noloss':   [c["chameleon1"], c["chameleon3"], c["chameleon2"]],
        'loss':     [c["skyblue1"], c["skyblue2"], c["skyblue3"]],
        'helper':   [c["scarletred1"], c["scarletred2"], c["scarletred3"], "#750000"],
        'nohelper': [c["orange1"], c["orange2"], c["orange3"]],
        }
bar_legends = {
        True:       "{} with Coding",
        False:      "{} without Coding",
        'noloss':   "PLAIN without Loss",
        'loss':     "PLAIN with Loss",
        'helper':   "RLNC with Helper",
        'nohelper': "RLNC without Helper",
        }
bar_pos = {
    True:       0,
    False:      1,
    'noloss':   0,
    'loss':     1,
    'helper':   2,
    'nohelper': 3,
    }
label = {
        True: "With Coding",
        False: "Without Coding",
        'helper': "Helper",
        'nohelper': "No Helper",
        'ack_timeout': "ACK Timeout",
        'req_timeout': "REQ Timeout",
        1: "1 Encoder",
        2: "2 Encoders",
        4: "4 Encoders",
        8: "8 Encoders",
        }

color = {
        True: c["chameleon2"],
        False: c["skyblue2"],
        'helper': c["scarletred1"],
        'nohelper': c["orange1"],
        'ack_timeout': c["chameleon2"],
        'req_timeout': c["skyblue2"],
        1: c["chameleon1"],
        2: c["skyblue1"],
        4: c["scarletred1"],
        8: c["orange1"],
        }

marker = {
        True: 'o',
        False: 'v',
        "helper": 'o',
        "nohelper": 'v',
        'ack_timeout': 'o',
        'req_timeout': 'v',
        1: 'o',
        2: 'v',
        4: '+',
        8: 's',
        }

class graph:
    def __init__(self):
        self.figs = {}
        self.axes = {}
        self.bar_tops = {}
        self.bar_colors = {}

    def show(self, plots):
        self.t = threading.Thread(None, self.hide)
        self.t.start()
        pyplot.show()
        print("Show done")

    def hide(self):
        ch = interface.get_keypress()
        pyplot.close('all')
        #time.sleep(.1)
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

        self.fig = pyplot.figure(title)
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

    def plot(self, x, y, l, c=None):
        if c:
            self.fig.gca().plot(x, y, linewidth=2, label=l, color=c)
        else:
            self.fig.gca().plot(x, y, linewidth=2, label=l)

    def plot_coding(self, x, y, coding):
            self.fig.gca().plot(x, y, linewidth=2, label=label[coding], color=color[coding], marker=marker[coding])

    def get_bar_tops(self, name, title, data, coding):
        if title not in self.bar_tops:
            self.bar_tops[title] = {}

        if name not in self.bar_tops[title]:
            self.bar_tops[title][name] = {}

        if coding not in self.bar_tops[title][name]:
            l = len(data)
            self.bar_tops[title][name][coding] = numpy.zeros(l)

        return self.bar_tops[title][name][coding]

    def update_bar_tops(self, name, title, data, coding):
        self.bar_tops[title][name][coding] += data

    def get_bar_args(self, node, coding, data):
        if coding not in self.bar_colors:
            self.bar_colors[coding] = {}

        # Get next bar color
        if node not in self.bar_colors[coding]:
            self.bar_colors[coding][node] = bar_colors[coding].pop(0)

        width = .1
        color = self.bar_colors[coding][node]
        positions = range(len(data))
        label = bar_legends[coding]
        positions = numpy.array(positions) + bar_pos[coding]*width

        return positions,data,width,color,label

    def plot_coded(self, node, data):
        if not len(data['coded']) or not len(data['fwd']):
            return

        self.setup_fig(
                name=node,
                title="Packet counts for {}".format(node.title()),
                xlabel="Total Offered Load [kbit/s]",
                ylabel="Packets")

        rates = numpy.array(data['rates'])*2
        self.plot(rates, data['coded']/2, "Coded")
        self.plot(rates, data['recoded']/2, "Recoded")
        self.plot(rates, data['decoded'], "Decoded")
        self.plot(rates, data['decode_failed'], "Decode failed")
        self.plot(rates, data['overheard'], "Overheard")
        self.plot(rates, data['fwd'],   "Forwarded")
        self.plot(rates, data['fwd'] + data['coded']/2 + data['recoded']/2, "Total")
        self.finish_fig()

    def plot_udp_system_throughput(self, data, coding):
        if not len(data['throughput']):
            return

        self.setup_fig(
                name='system',
                title="System Throughput",
                xlabel="Total Offered Load [kbit/s]",
                ylabel="Measured Throughput [kbit/s]")

        self.plot_coding(data['rates'], data['throughput'], coding)
        self.finish_fig()

    def plot_throughput(self, node, data, coding):
        if not len(data['throughput']):
            return

        self.setup_fig(
                name=node,
                title="Throughput for {0}".format(node.title()),
                xlabel="Total Offered Load [kbit/s]",
                ylabel="Measured Throughput")

        self.plot_coding(data['rates'], data['throughput'], coding)
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

    def plot_system_tx(self, source, relay, coding, run_info):
        if not len(source['iw_tx_pkts']) or not len(relay['iw_tx_pkts']):
            return

        self.setup_fig(
                name='system',
                title="Total System Packet TX",
                xlabel="Total Offered Load [kbit/s]",
                ylabel="Packets/s")

        rates = source['rates']
        tx = (source['iw_tx_pkts'] + relay['iw_tx_pkts'])/run_info['test_time']

        self.plot_coding(rates, tx, coding)
        self.finish_fig()

    def plot_tx_retries(self, node, data, coding):
        if not len(data['iw_tx_retries']):
            return

        self.setup_fig(
                name=node,
                title="Packet Retries for {}".format(node.title()),
                xlabel="Total Offered Load [kbit/s]",
                ylabel="Packets")

        self.plot_coding(data['rates'], data['iw_tx_retries'], coding)
        self.finish_fig()

    def plot_udp_system_retries(self, source_avg, relay_avg, coding):
        if not len(source_avg['iw_tx_retries']) or not len(relay_avg['iw_tx_retries']):
            return

        self.setup_fig(
                name='system',
                title="Average System TX Retries",
                xlabel="Total Offered Load [kbit/s]",
                ylabel="Average Retry Count Per Node [packets]")

        retries = source_avg['iw_tx_retries'] + relay_avg['iw_tx_retries']
        rates = source_avg['rates'] + relay_avg['rates']

        self.plot_coding(rates, retries, coding)
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

        self.plot_coding(data['rates'], data['cpu'], coding)
        self.finish_fig()

    def plot_system_cpu(self, avg_source, avg_relay, coding):
        if not len(avg_source['cpu']) or not len(avg_relay['cpu']):
            return

        self.setup_fig(
                name="system",
                title="Average Relay CPU Usage",
                xlabel="Offered load [kbit/s]",
                ylabel="CPU Usage [%]")

        self.ax.set_ylim(0,100)
        self.plot_coding(avg_relay['rates'], avg_relay['cpu'], coding)
        self.finish_fig()

        self.setup_fig(
                name="system",
                title="Average Source CPU Source",
                xlabel="Total Offered load [kbit/s]",
                ylabel="CPU Usage [%]")

        self.ax.set_ylim(0,100)
        self.plot_coding(avg_source['rates'], avg_source['cpu'], coding)
        self.finish_fig()

    def plot_delay(self, node, data, coding):
        if not len(data['ping_avg']):
            return

        self.setup_fig(
                name=node,
                title="Delay for {}".format(node.title()),
                xlabel="Offered load [kbit/s]",
                ylabel="End-to-end delay [ms]")

        self.plot_coding(data['rates'], data['ping_avg'], coding)
        self.finish_fig()

    def plot_udp_system_delay(self, avg_data, coding):
        if not len(avg_data['ping_avg']):
            return

        self.setup_fig(
                name="system",
                title="System delay",
                xlabel="Total Offered load [kbit/s]",
                ylabel="Average end-to-end delay [ms]")

        self.plot_coding(avg_data['rates']*2, avg_data['ping_avg'], coding)
        self.finish_fig()

    def plot_power(self, node, data, coding):
        if not len(data['power']):
            return

        self.setup_fig(
                name=node,
                title="Power for {}".format(node.title()),
                xlabel="Offered load [kbit/s]",
                ylabel="Consumed Energy [W]")

        self.plot_coding(data['rates'], data['power'], coding)
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
        self.plot_coding(x, y, coding)
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
        self.plot_coding(x, y, coding)
        self.finish_fig(loc="upper right")

    def plot_udp_mac_capture(self, data, coding):
        if not len(data['diffs']):
            return

        self.setup_fig(
                name='system',
                title="MAC Capture between Alice and Bob",
                xlabel="Offered Load [kbps]",
                ylabel="TX Difference [packets]")

        self.plot_coding(data['rates'], data['diffs'], coding)
        self.finish_fig()

    def plot_udp_mac_capture_rx(self, node, data, coding):
        if not len(data['capture_rx']):
            return

        self.setup_fig(
                name=node,
                title="RX difference between Alice and Bob on {}".format(node.title()),
                xlabel="Offered Load [kbps]",
                ylabel="Difference [packets]")

        self.plot_coding(data['rates'], data['capture_rx'], coding)
        self.finish_fig()

    def plot_udp_rx_coded_diff(self, node, data):
        if not len(data['coded_diff']):
            return

        self.setup_fig(
                name=node,
                title="Difference between RX and coded on {}".format(node.title()),
                xlabel="Offered Load [kbps]",
                ylabel="Difference [packets]")

        self.plot(data['rates'], data['coded_diff'], "With coding", color[coding])
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

    def plot_rlnc_throughput(self, s_data, d_data, coding, gs):
        if not len(s_data['errors']) or not len(d_data['rate']):
            return

        title = "Throughput (G{})".format(gs)
        ident = 'rlnc'

        self.setup_fig(
                name=ident,
                title=title,
                xlabel="Errors (e1, e2, e3) [%]",
                ylabel="Measured Throughput [kbit/s]")
        label_pos = numpy.array(range(len(s_data['errors'])))+.2
        self.ax.set_xticks(label_pos)
        self.ax.set_xticklabels(s_data['errors'])

        #y = d_data['bytes']*8/s_data['time']/1024
        y = d_data['rate']

        # Get values for bar plot
        bottoms = self.get_bar_tops(ident, title, y, coding)
        left,height,width,color,label = self.get_bar_args(0, coding, y)

        # Plot values and update the y-offset for next plot
        self.ax.bar(left, height, width, bottoms, ecolor='black', color=color, label=label)
        self.ax.legend(prop=dict(size=12), numpoints=1, loc='upper right')
        self.update_bar_tops(ident, title, y, coding)

    def plot_rlnc_transmissions(self, s_data, h_data, d_data, coding, gs):
        if not len(s_data['errors']):
            return

        title = "Transmissions (G{})".format(gs)
        ident = 'rlnc'

        self.setup_fig(
                name=ident,
                title=title,
                xlabel="Errors (e1, e2, e3) [%]",
                ylabel="Transmitted Packets [#]")
        label_pos = numpy.array(range(len(s_data['errors'])))+.2
        self.ax.set_xticks(label_pos)
        self.ax.set_xticklabels(s_data['errors'])

        #
        # Source packets
        #

        if coding in ('helper', 'nohelper'):
            scale = 1 - s_data['errors'][0][2]/100.0
            r = (d_data['redundant']/s_data['generations'])/scale
            i = d_data['non-innovative']/s_data['generations']/scale
            y = s_data['transmissions']/s_data['generations'] - r
            if i:
                y -= i
        else:
            rx = d_data['packets']
            g = rx/gs
            y = s_data['send']/g

        # Get values for bar plot
        bottoms = self.get_bar_tops(ident, title, y, coding)
        left,height,width,color,label = self.get_bar_args(0, coding, y)

        if coding == "helper":
            label = "Source Transmissions"

        # Plot values and update the y-offset for next plot
        self.ax.bar(left, height, width, bottoms, ecolor='black', color=color, label=label)
        self.ax.legend(loc='best')
        self.update_bar_tops(ident, title, y, coding)

        if coding not in ('helper', 'nohelper'):
            return

        #
        # Helper packers
        #

        if h_data and coding == "helper":
            y = (h_data['transmissions'])/s_data['generations']

            # Get values for bar plot
            bottoms = self.get_bar_tops(ident, title, y, coding)
            left,height,width,color,label = self.get_bar_args(1, coding, y)
            label = "Helper Transmissions"

            # Plot values and update the y-offset for next plot
            self.ax.bar(left, height, width, bottoms, ecolor='black', color=color, label=label)
            self.ax.legend(prop=dict(size=12), numpoints=1, loc='lower right')
            self.update_bar_tops(ident, title, y, coding)

        #
        # Non-innovative packets
        #
        if i:
            # Get values for bar plot
            bottoms = self.get_bar_tops(ident, title, i, coding)
            left,height,width,color,label = self.get_bar_args(2, coding, i)
            label = "Non-Innovative"

            # Plot values and update the y-offset for next plot
            self.ax.bar(left, height, width, bottoms, ecolor='black', color=color, label=label)
            self.ax.legend(prop=dict(size=12), numpoints=1, loc='lower right')
            self.update_bar_tops(ident, title, i, coding)


        #
        # Redundant packets
        #

        # Get values for bar plot
        bottoms = self.get_bar_tops(ident, title, r, coding)
        left,height,width,color,label = self.get_bar_args(3, coding, r)
        label = "Redundant Packets"

        # Plot values and update the y-offset for next plot
        self.ax.bar(left, height, width, bottoms, ecolor='black', color=color, label=label)
        self.ax.legend(prop=dict(size=12), numpoints=1, loc='lower right')
        self.update_bar_tops(ident, title, r, coding)

    def plot_rlnc_requests(self, node, data, coding, gs):
        if not len(data['errors']) or not len(data['requests']):
            return

        title = "Requests (G{})".format(gs)
        ident = 'rlnc'

        self.setup_fig(
                name=ident,
                title=title,
                xlabel="Errors (e1, e2, e3) [%]",
                ylabel="Number of requests [#]")
        label_pos = numpy.array(range(len(data['errors'])))+.2
        self.ax.set_xticks(label_pos)
        self.ax.set_xticklabels(data['errors'])

        y = data['requests']/gs

        # Get values for bar plot
        bottoms = self.get_bar_tops(ident, title, y, coding)
        left,height,width,color,label = self.get_bar_args(0, coding, y)
        label += ", " + node

        # Plot values and update the y-offset for next plot
        self.ax.bar(left, height, width, bottoms, ecolor='black', color=color, label=label)
        self.ax.legend(prop=dict(size=12), numpoints=1, loc='upper right')
        self.update_bar_tops(ident, title, y, coding)

    def plot_rlnc_timeout(self, s_data, d_data, key, error, encs):
        title = "Throughput vs. {} (e: {})".format(key, error)
        ident = "rlnc"

        self.setup_fig(
                name=ident,
                title=title,
                xlabel="Timeout [s]",
                ylabel="Throughput [kbps]")

        self.plot_coding(d_data[key], d_data['rate'], encs)
        self.ax.legend(prop=dict(size=12), numpoints=1, loc='lower right')
        self.finish_fig()

    def plot_rlnc_to_3d(self, data, error, encs):
        title = "Throughput vs. timeout (e: {})".format(error)
        ident = "rlnc"

        self.setup_fig(
                name=ident,
                title=title,
                xlabel="ACK Timeout",
                ylabel="REQ Timeout",
                projection='3d')

        x = data['rate']['x']
        y = data['rate']['y']
        z = data['rate']['z']
        self.ax.set_zlabel('Throughput [kbit/s]')
        self.ax.plot_surface(x, y, z, rstride=1, cstride=1, color=color[encs])
        self.ax.legend((label[encs]))

    def plot_rlnc_to_scatter(self, data, error, encs):
        title = "Encoder Top (e: {})".format(error)
        ident = "rlnc"

        self.setup_fig(
                name=ident,
                title=title,
                xlabel="ACK Timeout",
                ylabel="REQ Timeout")

        x,y,z = zip(*data['points'])
        w = ((numpy.array(z)-data['min'])/100)**2
        self.ax.scatter(x, y, s=w, color=color[encs])

    def plot_rlnc_to_contour(self, data, error):
        title = "Best #encoders (e: {})".format(error)
        ident = "contour"

        self.setup_fig(
                name=ident,
                title=title,
                xlabel="ACK Timeout [s]",
                ylabel="REQ Timeout [s]")

        X,Y,Z = zip(*data)
        extra = []
        for point in data:
            if point[0] == min(X):
                extra.append((0, point[1], point[2]))
            if point[1] == min(Y):
                extra.append((point[0], 0, point[2]))
            if point[0] == max(X):
                extra.append((point[0] + .1, point[1], point[2]))
            if point[0] == max(Y):
                extra.append((point[0], point[1] + .1, point[2]))
            if point[0] == min(X) and point[1] == min(Y):
                extra.append((0, 0, point[2]))
            if point[0] == max(X) and point[1] == max(Y):
                extra.append((max(X) + .1, max(Y) + .1, point[2]))
            if point[0] == max(X) and point[1] == min(Y):
                extra.append((point[0] + .1, 0, point[2]))
            if point[0] == min(Y) and point[1] == max(Y):
                extra.append((0, point[1] + .1, point[2]))

        data += extra

        X,Y,Z = zip(*data)
        xi = numpy.linspace(min(X), max(X))
        yi = numpy.linspace(min(Y), max(Y))
        zi = griddata(X, Y, Z, xi, yi)
        colors = [color[1], color[2], color[4], color[8]]
        cs = self.ax.contourf(xi, yi, zi, [.5,1.5,3,6,9], colors=colors, extend='both')
        cs.cmap.set_under(color[1])
        cs.cmap.set_over(color[8])
        d = self.ax.contour(xi, yi, zi,  [.5, 1.5, 3, 6, 9], colors='k')
        proxy = [pyplot.Rectangle((0,0), 1, 1, fc=c) for c in colors]
        pyplot.legend(proxy, [label[1], label[2], label[4], label[8]], loc="lower right")

    def plot_rlnc_to_throughput(self, data, encs, error):
        title = "Throughput (e: {})".format(error)
        ident = "throughput_contour"

        self.setup_fig(
                name=ident,
                title=title,
                xlabel="ACK Timeout [s]",
                ylabel="REQ Timeout [s]")

        X,Y,Z = zip(*data)
        xi = numpy.linspace(min(X), max(X))
        yi = numpy.linspace(min(Y), max(Y))
        zi = griddata(X, Y, Z, xi, yi)
        cs = self.ax.contourf(xi, yi, zi)
        cb = pyplot.colorbar(cs, extend='both')

        X,Y,Z = zip(*encs)
        xi = numpy.linspace(min(X), max(X))
        yi = numpy.linspace(min(Y), max(Y))
        zi = griddata(X, Y, Z, xi, yi)
        d = self.ax.contour(xi, yi, zi,  [.5, 1.5, 3, 6, 9], colors='k')
        #cs.cmap.set_under(color[1])
        #cs.cmap.set_over(color[8])
        #d = self.ax.contour(xi, yi, zi,  [.5, 1.5, 3, 6, 9], colors='k')
        #proxy = [pyplot.Rectangle((0,0), 1, 1, fc=c) for c in colors]
        #pyplot.legend(proxy, [label[1], label[2], label[4], label[8]], loc="lower right")
