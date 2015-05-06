#!/usr/bin/env python

from plotlib import *

srcs = ('src1', 'src2')
dsts = ('dst1', 'dst2')
rlys = ('relay')

def plot_system_rate(data, means):
    d = means.loc(axis=1)[:,:,dsts]
    ax = d['rslt_rate'].sum(axis=1, level=0, inplace=True).plot(**plot_args)

    generate_marker(ax)
    generate_legend(ax)
    ax.set_title("System Throughput")
    ax.set_xlabel("Offered Load [kbps]")
    ax.set_ylabel("Throughput [kbps]")

def plot_dst_rates(data, means):
    d = means.loc(axis=1)[:,:,dsts]
    ax = d['rslt_rate'].plot()

    generate_marker(ax)
    generate_legend(ax)
    ax.set_title("Flow Throughput")
    ax.set_xlabel("Offered Load [kbps]")
    ax.set_ylabel("Throughput [kbps]")

def plot_src_rates(data, means):
    s = means.loc(axis=1)[:,:,srcs]
    tx = s['smpl_iw tx packets']
    t = s['rslt_time']
    s = s['args_iperf_len']
    r = tx * s * 8 / t / 1024
    ax = r.plot()

    generate_marker(ax)
    generate_legend(ax)
    ax.set_title("Source Transmit Rate")
    ax.set_xlabel("Offered Load [kbps]")
    ax.set_ylabel("Transmit Rate [kbps]")

def plot_dst_failed(data, means):
    codings = ['nc', 'nc_prio']
    d = means.loc(axis=1)[:,codings,dsts]
    f = d['smpl_bat_nc_decode_failed']
    r = d['smpl_bat_nc_decode_failed'] + d['smpl_bat_nc_decode']
    l = 100 * f / r
    ax = l.plot()

    generate_marker(ax)
    generate_legend(ax)
    ax.set_title("Failed Decodings")
    ax.set_xlabel("Offered Load [kbps]")
    ax.set_ylabel("Failed Decodings [%]")

def plot_system_loss(data, means):
    codings = ['nc', 'nc_prio']
    d = means.loc(axis=1)[:,codings,dsts]
    r = means.loc(axis=1)[:,codings,rlys]

    tx = r['smpl_bat_nc_code'].sum(axis=1, level=0)
    rx_f = d['smpl_bat_nc_decode_failed'].sum(axis=1, level=0)
    rx_d = d['smpl_bat_nc_decode'].sum(axis=1, level=0)
    rx = rx_f + rx_d
    loss = 100 * (tx - rx)/tx

    ax = loss.plot(**plot_args)

    generate_marker(ax)
    generate_legend(ax)
    ax.set_title("Overhearing Losses")
    ax.set_xlabel("Offered Load [kbps]")
    ax.set_ylabel("Losses [%]")

def plot_relay_drops(data, means):
    codings = ['nc', 'nc_prio']
    r = means.loc(axis=1)[:,:,rlys]
    s = means.loc(axis=1)[:,:,srcs]
    d = r['smpl_bat_forward'] - r['smpl_iw tx packets'] + r['smpl_bat_mgmt_tx']
    tx = r['smpl_iw tx packets']
    rx = r['smpl_bat_forward'] + r['smpl_bat_nc_code']/2

    d = 1 - tx/rx
    d.columns = d.columns.droplevel(level='node')
    d *= 100

    ax = d.plot(**plot_args)

    generate_marker(ax)
    generate_legend(ax)
    ax.set_title("Dropped Packets at Relay")
    ax.set_xlabel("Offered Load [kbps]")
    ax.set_ylabel("Dropped Packets [%]")

if __name__ == "__main__":
    plot_funcs = [
            plot_system_rate,
            plot_dst_rates,
            plot_src_rates,
            plot_dst_failed,
            plot_system_loss,
            plot_relay_drops,
    ]

    groups = ['info_coding', 'node']
    index = 'info_rate'
    pl = plotlib(groups, index, plot_funcs)
