import pylab
import matplotlib.gridspec as gridspec
import numpy

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

class graph:
    def __init__(self):
        self.throughput_plots = {}
        self.aggregated_throughput_plot = None
        self.tcp_window_throughput_plot = None
        self.tcp_throughput_plot = None
        self.tcp_throughput_data = {}
        self.cpu_plots = {}
        self.power_plots = {}

    def show(self):
        pylab.show()

    def setup_fig(self, title, xlabel, ylabel):
        fig = pylab.figure()
        ax = fig.add_subplot(111)
        ax.grid(True)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        return ax

    def finish_fig(self, ax):
        ax.legend(loc='upper left', shadow=True)

    def plot_fig(self, fig, x, y, label):
        fig.plot(x, y, linewidth=2, label=label)

    def plot_coded(self, node, data):
        fig = self.setup_fig(
                title="Coded vs. Forwarded Packets for {}".format(node.title()),
                xlabel="Total Offered Load [kbit/s]",
                ylabel="Ratio [packets/sum]"
                )

        coded_packets = numpy.divide(data['coded'], 2)
        coded_ratio = numpy.divide(coded_packets, data['fwd_coded'])
        fwd_ratio = numpy.divide(data['fwd'], data['fwd_coded'])
        total_ratio = coded_ratio + fwd_ratio

        self.plot_fig(fig, data['rates'], coded_ratio, "Coded")
        self.plot_fig(fig, data['rates'], fwd_ratio, "Forwarded")
        self.plot_fig(fig, data['rates'], total_ratio, "Total")
        self.finish_fig(fig)

    def plot_udp_aggregated_throughput(self, data, coding):
        if self.aggregated_throughput_plot:
            fig = self.aggregated_throughput_plot
        else:
            fig = self.setup_fig(
                    title="Aggregated Throughput",
                    xlabel="Total Offered Load [kbit/s]",
                    ylabel="Measured Throughput [kbit/s]")
            self.aggregated_throughput_plot = fig

        label = "With Coding" if coding else "Without Coding"
        self.plot_fig(fig, data['rates'], data['throughput'], label)
        self.finish_fig(fig)

    def plot_throughput(self, node, data, coding):
        if node in self.throughput_plots:
            fig = self.throughput_plots[node]
        else:
            fig = self.setup_fig(
                    title="Throughput for {0}".format(node.title()),
                    xlabel="Total Offered Load [kbit/s]",
                    ylabel="Measured Throughput")
            self.throughput_plots[node] = fig

        label = "With Coding" if coding else "Without Coding"
        self.plot_fig(fig, data['rates'], data['throughput'], label)
        self.finish_fig(fig)

    def plot_cpu(self, node, data, coding):
        if node in self.cpu_plots:
            fig = self.cpu_plots[node]
        else:
            fig = self.setup_fig(
                    title="CPU Usage for {}".format(node.title()),
                    xlabel="Total offered load [kbit/s]",
                    ylabel="CPU Usage [%]"
                    )
            fig.set_ylim(0,100)
            self.cpu_plots[node] = fig

        label = "With Coding" if coding else "Without Coding"
        self.plot_fig(fig, data['rates'], data['cpu'], label)
        self.finish_fig(fig)

    def plot_power(self, node, data, coding):
        if node in self.power_plots:
            fig = self.power_plots[node]
        else:
            fig = self.setup_fig(
                    title="Power for {}".format(node.title()),
                    xlabel="Total offered load [kbit/s]",
                    ylabel="Consumption [W]"
                    )
            self.power_plots[node] = fig

        label = "With Coding" if coding else "Without Coding"
        self.plot_fig(fig, data['rates'], data['power'], label)
        self.finish_fig(fig)

    def plot_tcp_throughput(self, node, data, coding):
        if not self.tcp_throughput_plot:
            fig = self.setup_fig(
                    title="TCP Throughput",
                    xlabel="Congestion Avoidance Algorithm",
                    ylabel="Measured Throughput [kbit/s]")
            label_pos = numpy.array(range(len(data['algos'])))+.2
            fig.set_xticks(label_pos)
            fig.set_xticklabels(data['algos'])
            self.tcp_throughput_plot = fig
            self.tcp_throughput_data[coding] = numpy.array([0]*len(data['algos']))
            top = self.tcp_throughput_data[coding]
            self.tcp_throughput_data[not coding] = top
        else:
            fig = self.tcp_throughput_plot
            top = self.tcp_throughput_data[coding]

        width = .2
        positions = range(len(data['algos']))
        if coding:
            color = c['skyblue2']
            positions = numpy.array(positions)+width
            label = "{} with Coding".format(node.title())
        else:
            label = "{} without Coding".format(node.title())
            color = c['chameleon2']

        fig.bar(positions, data['throughput'], width, top, color=color, ecolor='black', label=label)
        fig.legend(prop=dict(size=12), numpoints=1, loc='lower right')

        # Save top values for each bar
        self.tcp_throughput_data[coding] = numpy.sum([top, data['throughput']], axis=0)

    def plot_tcp_window_throughput(self, node, data, coding):
        if not self.tcp_throughput_plot:
            fig = self.setup_fig(
                    title="TCP Throughput",
                    xlabel="Window size [bytes]",
                    ylabel="Measured Throughput [kbit/s]")
            label_pos = numpy.array(range(len(data['tcp_windows'])))+.2
            fig.set_xticks(label_pos)
            fig.set_xticklabels(data['tcp_windows'])
            self.tcp_throughput_plot = fig
            self.tcp_throughput_data[coding] = numpy.array([0]*len(data['tcp_windows']))
            top = self.tcp_throughput_data[coding]
            self.tcp_throughput_data[not coding] = top
        else:
            fig = self.tcp_throughput_plot
            top = self.tcp_throughput_data[coding]

        width = .2
        positions = range(len(data['tcp_windows']))
        if coding:
            color = c['skyblue2']
            positions = numpy.array(positions)+width
            label = "{} with Coding".format(node.title())
        else:
            label = "{} without Coding".format(node.title())
            color = c['chameleon2']

        fig.bar(positions, data['throughput'], width, top, color=color, ecolor='black', label=label)
        fig.legend(prop=dict(size=12), numpoints=1, loc='lower right')

        # Save top values for each bar
        self.tcp_throughput_data[coding] = numpy.sum([top, data['throughput']], axis=0)
