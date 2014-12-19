#!/usr/bin/env python

from plotlib import *

srcs = ('src1', 'src2')
dsts = ('dst1', 'dst2')
rlys = ('relay')

def plot_system_rate(data, means):
    d = means.loc(axis=1)[:,:,dsts]

def plot_dst_rates(data, means):
    d = means.loc(axis=1)[:,:,dsts]
    d['rslt_rate'].plot()
    d['rslt_rate'].sum(axis=1, level=0, inplace=True).plot()

if __name__ == "__main__":
    plot_funcs = [
            plot_system_rate,
            plot_dst_rates,
    ]

    groups = ['info_coding', 'node']
    index = 'info_rate'
    pl = plotlib(groups, index, plot_funcs)
