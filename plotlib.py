#!/usr/bin/env python

import os
import sys
import inspect
import numpy as np
import pandas as pd
import argparse as ap
from scipy import stats
from itertools import cycle
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

try:
    import seaborn as sns
except ImportError:
    print("no seaborn colors")
else:
    print("using seaborn colors")
    sns.set_palette('Set2', n_colors=8)

list_choices = ['plots', 'samples', 'results', 'info', 'args', 'all', 'other']
markers = 'o^s<'

plot_args = {'linewidth': 2, 'legend': False}
generate_legend = lambda ax: ax.legend(ax.get_lines(), [line.get_label() for line in ax.get_lines()], loc='best')
generate_marker = (lambda ax: (lambda ax, m: [line.set_marker(next(m)) for line in ax.get_lines()])(ax, cycle(markers)))
plt.rc('legend',**{'fontsize': 10})

class plotlib(object):
    parser = ap.ArgumentParser(description="Core Plotting Tools")
    parser.add_argument("--plots", default=None, type=str, required=False)
    parser.add_argument("--out", default=None, type=str, required=False)
    parser.add_argument("--out_only", default=None, type=str, required=False)
    parser.add_argument("--list", default=None, choices=list_choices, required=False)
    parser.add_argument("--args", action='store_true', default=False, required=False)
    parser.add_argument("data", default=None, type=str)

    def __init__(self, groups, index, plot_funcs):
        self.groups = groups
        self.index = index
        self.plot_funcs = plot_funcs
        self.args = self.parser.parse_args()
        self.read_data()
        self.parse_ranges()
        self.list_plots()
        self.list_args()
        self.list_keys()
        self.prepare_data()
        self.do_plotting()
        self.show_plots()
        self.save_plots()

    def do_plotting(self):
        print("generating plots")
        for i in range(len(self.plot_funcs)):
            if self.plots and i not in self.plots:
                continue

            try:
                self.plot_funcs[i](self.data, self.means)
            except KeyError as e:
                self.handle_keyerror(e, i)

    def show_plots(self):
        if not self.args.out_only:
            print("showing plots")
            plt.show()

    def read_data(self):
        # read filename or fall back to default name
        data_file = self.args.data

        # test file existence
        if not os.path.exists(data_file):
            print("no such file: " + data_file)
            sys.exit(1)

        # read data into pandas dataframe
        print("loading data")
        try:
            self.data = pd.read_json(data_file)
        except ValueError as e:
            print("failed to load data file ({}): {}".format(data_file, e))
            sys.exit(1)

    def prepare_data(self):
        print("preparing data")
        groups = self.data.groupby(self.groups + [self.index]);
        means = groups.aggregate(np.mean)

        # move coding and node groups from row index to columns
        for g in self.groups:
            means = means.unstack(g)

        self.means = means

    def parse_ranges(self):
        if not self.args.plots:
            self.plots = None
            return

        try:
            tokens = self.args.plots.split(',')
            ranges = [t.split('-') for t in tokens]
            lists  = [list(range(int(r[0]), int(r[-1]) + 1)) for r in ranges]
            ints = sum(lists, [])
        except Exception as e:
            print(e)
            print("unable to parse ranges: " + self.args.plots)
            sys.exit(1)

        self.plots = ints

    def list_plots(self):
        if self.args.list == 'plots':
            print("available plots:")
            for i,func in enumerate(self.plot_funcs):
                print("{}: {}".format(i, func.__name__))
            sys.exit(0)

    def get_args(self):
        keys = list(self.get_keys('args'))

        if not keys:
            return []

        data = self.data[keys].astype(str).drop_duplicates()

        return data.T[0].to_dict().items()

    def list_args(self):
        # list arguments if requested
        if self.args.args:
            print("printing arguments")
            for arg,val in sorted(self.get_args()):
                print("{}: {}".format(arg[len('args_'):], val))
            sys.exit(0)

    def get_keys(self, key_type):
        prefix_map = {'samples': 'smpl_', 'results': 'rslt_', 'info': 'info_', 'args': 'args_'}
        prefix_vals = tuple(prefix_map.values())
        prefix = prefix_map.get(key_type)

        if prefix:
            keys = filter(lambda x: x.startswith(prefix), self.data.columns)

        if key_type == 'all':
            keys = self.data.columns

        if key_type == 'other':
            keys = filter(lambda x: not x.startswith(prefix_vals), self.data.columns)

        return keys

    def list_keys(self):
        # list keys if requested
        if self.args.list in ('samples', 'results', 'info', 'args', 'all', 'other'):
            print("printing keys: {}".format(self.args.list))
            for key in self.get_keys(self.args.list):
                print(key)
            sys.exit(0)

    def handle_keyerror(self, e, i):
        # loop until last stack trace line from this file
        tb = e.__traceback__
        fn = sys.argv[0] if sys.argv else __file__
        while tb:
            if fn not in tb.tb_next.tb_frame.f_code.co_filename:
                break
            tb = tb.tb_next

        # get source of function and triggering line number
        source,linestart = inspect.getsourcelines(tb)
        offset = tb.tb_frame.f_lineno - linestart

        # print error info
        print("KeyError in plot {} ({}):".format(i, self.plot_funcs[i].__name__))
        print("    {}:{}: {}".format(fn, tb.tb_frame.f_lineno, source[offset].strip()))

    def save_plots(self):
        if not self.args.out and not self.args.out_only:
            return

        print("saving plots")

        # get output prefix:
        prefix = self.args.out if self.args.out else self.args.out_only

        # create dir if needed or check for dir type
        if not os.path.exists(prefix):
            os.mkdir(prefix)
        elif not os.path.isdir(prefix):
            print("not a directory: {}".format(prefix))
            sys.exit(1)

        # Prepare for a single file with all plots
        p = os.path.join(prefix, "all_plots.pdf")
        pdf_pages = PdfPages(p)

        for fig in list(map(plt.figure, plt.get_fignums())):
            # Add plot to the one and only pdf
            pdf_pages.savefig(fig, transparent=True)

            # fetch and remove title from plot (used in filename instead)
            title = fig.axes[0].get_title().replace(' ', '_')
            fig.axes[0].set_title("")

            # create filename and save plot
            filename = os.path.join(prefix, title + ".pdf")
            print(filename)
            fig.savefig(filename, transparent=True, bbox_inches='tight', pad_inches=0)

        # Save the teh single file
        pdf_pages.close()

if __name__ == "__main__":
    groups = ['node', 'info_coding']
    index = 'info_rate'
    plot_funcs = []
    l = plotlib(groups, index, plot_funcs)
