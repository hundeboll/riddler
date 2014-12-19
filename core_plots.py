#!/usr/bin/env python

from plotlib import *

srcs = ('core1', 'core2')
dsts = ('core4', 'core3')
rlys = ('core0',)

def plot_rate(data, means):
    # pick nodes to work with
    s = means.loc(axis=1)[:,:,srcs]
    d = means.loc(axis=1)[:,:,dsts]

    # get data from different set of nodes
    d = d['rslt_rate'].sum(axis=1, level='info_coding')
    s = s['rslt_rate'].sum(axis=1, level='info_coding')

    # merge data
    r = pd.concat([s,d], keys=['src', 'dst'], axis=1)

    # plot it
    ax = r.xs('core', axis=1, level=1).plot(x='src', y='dst', label='core', **plot_args)
    r.xs('nc', axis=1, level=1).plot(x='src', y='dst', ax=ax, label='nc', **plot_args)
    r.xs('plain', axis=1, level=1).plot(x='src', y='dst', ax=ax, label='plain', **plot_args)

    # add legend and labels
    generate_marker(ax)
    ax.legend(['core', 'nc', 'plain'], loc='best')
    ax.set_title("throughpout vs. offered load")
    ax.set_xlabel("offered load [kbps]")
    ax.set_ylabel("throughput [kpbs]")
    ax.set_ylim(bottom=0)

def plot_overheard(data, means):
    # columns we work with
    tx_col = ['smpl_bat_rlnc_tx_plain', 'smpl_bat_rlnc_tx_enc']
    rx_col = ['smpl_bat_core_sniffed']
    rlnc_col = 'smpl_bat_core_own'
    nc_tx_col = ['smpl_bat_tx']
    nc_rx_col = ['smpl_bat_nc_buffer']

    # get nodes
    src = means.loc(axis=1)[:,'core',srcs]
    dst = means.loc(axis=1)[:,'core',dsts]
    nc_src = means.loc(axis=1)[:,'nc',srcs]
    nc_dst = means.loc(axis=1)[:,'nc',dsts]

    # get data
    tx = src[tx_col].sum(axis=1, level=2)
    rx = dst[rx_col].sum(axis=1, level=2)
    rlnc = dst[rlnc_col].sum(axis=1, level=1)
    nc_tx = nc_src[nc_tx_col].sum(axis=1, level=2)
    nc_rx = nc_dst[nc_rx_col].sum(axis=1, level=2)
    nc_dec = nc_dst['smpl_bat_nc_decode'].sum(axis=1, level=1)
    nc_plain = nc_dst['smpl_bat_rx'].sum(axis=1, level=1) - nc_dec

    # fix names such that rlnc received at core3 is overheard at core4
    rlnc.rename(columns={'core3': 'core4', 'core4': 'core3'}, inplace=True)
    nc_plain.rename(columns={'core3': 'core4', 'core4': 'core3'}, inplace=True)

    # don't count overheard non-core packets from relay to other dst
    rx = rx - rlnc
    nc_rx = nc_rx - nc_plain

    # fix names to allow division
    tx.rename(columns={'core1': 'core left', 'core2': 'core right'}, inplace=True)
    rx.rename(columns={'core3': 'core left', 'core4': 'core right'}, inplace=True)
    nc_tx.rename(columns={'core1': 'nc left', 'core2': 'nc right'}, inplace=True)
    nc_rx.rename(columns={'core3': 'nc left', 'core4': 'nc right'}, inplace=True)

    # plot percentage
    core = 100 * (1 - rx/tx)
    nc = 100 * (1 - nc_rx/nc_tx)

    core[core < 0] = 0

    # do the plotting
    ax = core.plot(**plot_args)
    nc.plot(ax=ax, **plot_args)

    # add labels and titles
    generate_marker(ax)
    generate_legend(ax)
    ax.set_title("packet loss on the overhearing link")
    ax.set_xlabel("offered load [kbps]")
    ax.set_ylabel("loss [%]")

def plot_core_txrx(data, means):
    # columns we intend to work on
    core_rx_col = 'smpl_bat_core_rx'
    core_tx_col = 'smpl_bat_core_tx'
    rlnc_tx_col = 'smpl_bat_rlnc_tx_rec'
    rlnc_rx_col = 'smpl_bat_core_own'

    # select nodes to work with
    dst = means.loc(axis=1)[:,'core',dsts]
    rly = means.loc(axis=1)[:,'core',rlys]

    # extract and prepare values
    core_rx = dst[core_rx_col].sum(axis=1, level='info_coding')
    core_tx = rly[core_tx_col].multiply(2, axis=1)
    rlnc_tx = rly[rlnc_tx_col]
    rlnc_rx = dst[rlnc_rx_col].sum(axis=1, level='info_coding')
    rlnc_tx.is_copy = False
    rlnc_tx['core','core0'] = rlnc_tx['core'].subtract(core_tx['core'])

    # remove unused index level
    rlnc_tx.columns = rlnc_tx.columns.droplevel(level='node')
    core_tx.columns = core_tx.columns.droplevel(level='node')

    # rename colum names to fix legend labels in plots
    core_rx.rename(columns={'core': 'core rx'}, inplace=True)
    core_tx.rename(columns={'core': 'core tx'}, inplace=True)
    rlnc_tx.rename(columns={'core': 'rlnc tx'}, inplace=True)
    rlnc_rx.rename(columns={'core': 'rlnc rx'}, inplace=True)

    # do the actual plotting
    ax = core_tx.plot(**plot_args)
    core_rx.plot(ax=ax, **plot_args)
    rlnc_tx.plot(ax=ax, **plot_args)
    rlnc_rx.plot(ax=ax, **plot_args)

    # add labels and titles
    generate_legend(ax)
    ax.set_title("tx and rx of core packets")
    ax.set_xlabel("offered load [kbps]")
    ax.set_ylabel("packets [#]")
    ax.set_ylim(bottom=0)

def plot_core_decoding(data, means):
    # columns we intend to work on
    core_rx_col = 'smpl_bat_core_rx'
    rlnc_rx_col = 'smpl_bat_core_own'
    dec_col = 'smpl_bat_core_dec'

    # select nodes to work with
    dst = means.loc(axis=1)[:,'core',dsts]

    # extract and prepare values
    core_rx = dst[core_rx_col].sum(axis=1, level='info_coding')
    rlnc_rx = dst[rlnc_rx_col].sum(axis=1, level='info_coding')
    dec = dst[dec_col].sum(axis=1, level='info_coding')

    # rename columns to fix legend labels in plots
    core_rx.rename(columns={'core': 'core rx'}, inplace=True)
    rlnc_rx.rename(columns={'core': 'rlnc rx'}, inplace=True)
    dec.rename(columns={'core': 'total decode'}, inplace=True)

    # do the actual plotting
    ax = core_rx.plot(**plot_args)
    rlnc_rx.plot(ax=ax, **plot_args)
    dec.plot(ax=ax, **plot_args)

    # add labels and titles
    generate_legend(ax)
    ax.set_title("decoding success")
    ax.set_xlabel("offered load [kbps]")
    ax.set_ylabel("packets [#]")
    ax.set_ylim(bottom=0)

def plot_partial(data, means):
    # columns to work with
    trashed_col = 'smpl_bat_core_thrashed'
    partial_col = 'smpl_bat_core_partial'

    # select nodes to work with
    dst = means.loc(axis=1)[:,'core',dsts]

    # extract values and sum for both receivers
    trashed = dst[trashed_col].sum(axis=1, level='info_coding')
    partial = dst[partial_col].sum(axis=1, level='info_coding')

    # rename columns to get better legend
    trashed.rename(columns={'core': 'trashed decoders'}, inplace=True)
    partial.rename(columns={'core': 'partial packets'}, inplace=True)

    # do the plot
    ax = trashed.plot(**plot_args)
    partial.plot(ax=ax, **plot_args)

    # add labels and titles
    generate_legend(ax)
    ax.set_title("number of non-complete decoders and partial decoded packets")
    ax.set_xlabel("offered load [kbps]")
    ax.set_ylabel("packets/decoders")
    ax.set_ylim(bottom=0)

def plot_diff(data, means):
    # columns to work with
    rate_col = 'rslt_rate'

    # nodes to work with
    data = data[data['node'].isin(dsts)]
    data = data[data['info_coding'] == 'core']

    # order data into loop -> rate -> node
    data = data.set_index(['info_loop', 'info_rate', 'node'])
    data.sortlevel(inplace=True)

    # create per-node columns
    data = data.unstack('node')

    # get the delta values
    delta = data[rate_col][dsts[0]] - data[rate_col][dsts[1]]
    delta = delta.abs()

    # mean the deltas
    delta = delta.unstack('info_loop').mean(axis=1)

    # plotting
    ax = delta.plot(**plot_args)

    # add labels
    ax.set_title("absolute throughput difference")
    ax.set_xlabel("offered load [kbps]")
    ax.set_ylabel("average absolute difference [kbps]")
    ax.set_ylim(bottom=0)

def plot_ranks(data, means):
    bs = data['info_core_bs'][0]*2

    # columns to work with
    rank_cols = {
            'smpl_bat_core_rank0':  '== 01',
            'smpl_bat_core_rank1':  '<= 15',
            'smpl_bat_core_rank2':  '>= {}'.format(int(bs - bs/2)),
            'smpl_bat_core_rank4':  '>= {}'.format(int(bs - bs/4)),
            'smpl_bat_core_rank8':  '>= {}'.format(int(bs - bs/8)),
            'smpl_bat_core_rank16': '>= {}'.format(int(bs - bs/16)),
            }

    # nodes to work with
    dst = means.loc(axis=1)[:,'core',dsts]

    # get data
    ranks = dst[list(rank_cols.keys())].sum(axis=1, level=0)

    # rename  and sort columns
    ranks.rename(columns=rank_cols, inplace=True)
    ranks = ranks.reindex_axis(sorted(rank_cols.values(), key=lambda x: int(x[3:]), reverse=True), axis=1)

    # plot
    ax = ranks.plot(**plot_args)

    # add labels and titles
    generate_legend(ax)
    ax.set_title("rank of trashed decoders")
    ax.set_xlabel("offered load [kbps]")
    ax.set_ylabel("number of decoders [#]")
    ax.set_ylim(bottom=0)

def plot_rec_tx_rx(data, means):
    # columns to work with
    enc_cols = ['smpl_bat_rlnc_tx_plain', 'smpl_bat_rlnc_tx_enc']
    rec_col  = 'smpl_bat_rlnc_rx_enc'

    # nodes to work with
    src = means.loc(axis=1)[:,'core',srcs]
    rly = means.loc(axis=1)[:,'core',rlys]

    # get data
    tx = src[enc_cols].sum(axis=1, level=1)
    rx = rly[rec_col].sum(axis=1, level=0)

    # rename columns
    tx.rename(columns={'core': 'sources tx'}, inplace=True)
    rx.rename(columns={'core': 'relay rx'}, inplace=True)

    #plot it
    ax = tx.plot(**plot_args)
    rx.plot(ax=ax, **plot_args)

    # finish it up
    generate_legend(ax)
    ax.set_title("tx and rx for source-relay link")
    ax.set_xlabel("offered load [kbps]")
    ax.set_ylabel("number of packets [#]")
    ax.set_ylim(bottom=0)

def plot_src_tx(data, means):
    # columns to work with
    core_cols = ['smpl_bat_rlnc_tx_plain', 'smpl_bat_rlnc_tx_enc']
    nc_cols = 'smpl_bat_tx'

    # get nodes
    core_src = means.loc(axis=1)[:,'core',srcs]
    nc_src = means.loc(axis=1)[:,'nc',srcs]

    # get data
    core_tx = core_src[core_cols].sum(axis=1, level=2)
    nc_tx = nc_src[nc_cols].sum(axis=1, level=1)

    # rename columns to change legends
    nc_tx.rename(columns={'core1': 'nc1', 'core2': 'nc2'}, inplace=True)

    # plot it
    ax = core_tx.plot(**plot_args)
    nc_tx.plot(ax=ax, **plot_args)

    # add labels
    generate_legend(ax)
    ax.set_title("source transmissions and total throughput")
    ax.set_xlabel("offered load [kbps]")
    ax.set_ylabel("transmitted packets [#]")
    ax.set_ylim(bottom=0)

def plot_linear(data, means):
    # columns to work with
    lin_names = {
        'smpl_bat_core_own_linear': 'rec',
        'smpl_bat_core_oth_linear': 'enc',
        'smpl_bat_core_dual_linear': 'core'
        }
    lin_cols = list(lin_names.keys())
    block_cols = 'smpl_bat_core_block_dec'

    # nodes to work with
    dst = means.loc(axis=1)[:,'core',dsts]

    # get data
    block = dst[block_cols].sum(axis=1, level=0)
    lin = dst[lin_cols].sum(axis=1, level=0)
    lin = pd.DataFrame(lin.values / block.values, index=lin.index, columns=lin.columns)

    # rename labels
    lin.rename(columns=lin_names, inplace=True)

    # plot it
    ax = lin.plot(**plot_args)

    # add labels and titles
    generate_legend(ax)
    ax.set_title("linear dependent packets per block")
    ax.set_xlabel("offered load [kbps]")
    ax.set_ylabel("linear packet [#]")

def plot_losses(data, means):
    tx_col = 'smpl_bat_tx'
    rx_col = 'rslt_packets'

    src = means.loc(axis=1)[:,:,srcs]
    dst = means.loc(axis=1)[:,:,dsts]

    tx = src[tx_col].sum(axis=1, level=0, inplace=True)
    rx = dst[rx_col].sum(axis=1, level=0, inplace=True)

    loss = tx - rx

    ax = loss.plot(**plot_args)

    generate_marker(ax)
    generate_legend(ax)
    ax.set_title("end-to-end reliability")
    ax.set_xlabel("offered load [kbps]")
    ax.set_ylabel("packet loss [#]")

if __name__ == "__main__":
    # list of available plot functions
    plot_funcs = [
        plot_diff,
        plot_rate,
        plot_overheard,
        plot_core_txrx,
        plot_core_decoding,
        plot_partial,
        plot_ranks,
        plot_rec_tx_rx,
        plot_src_tx,
        plot_linear,
        plot_losses,
        ]

    groups = ['info_coding','node']
    index = 'info_rate'
    pl = plotlib(groups, index, plot_funcs)
