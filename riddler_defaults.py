#
# General settings
#
nodes_file = "network_test"
data_file = "test.pickle"
export_file = "test_socket"
client_host = ""
client_port = 6677

#
# Test settings
#
test_profile = 'udp_rates'  # Profiles to run (udp_rates, udp_ratios, tcp_algos, tcp_windows, hold_times, or power_meas, rlnc).
test_time  = 30          # Time for each loop to run
test_sleep = 30          # Time to sleep between runs
test_loops = 3         # Number of repetitions for each run
sample_interval = 1     # Seconds between each node sample

#
# Settings for udp_rates, tcp_algos, power_meas
#
hold_time = 10
purge_time = 200
packet_length = 100     # Not implemented yet
rts_threshold = "off"

#
# Settings for udp_rates, hold_times, power_meas
#
rate_start = 100       # Initial rate of each swipe in kbit/s
rate_stop  = 1000        # Last rate of each swipe in kbit/s
rate_step  = 100         # Rate increment for each run in kbit/s

#
# Settings for udp_ratio
#
ratio_start = 10    # Percentage
ratio_stop  = 100   # Percentage
ratio_step  = 10    # Percentage

#
# Settings for hold_times
#
hold_start = 10
hold_stop = 20
hold_step = 2

#
# Settings for tcp_algos
#
tcp_window = 87380
tcp_algos = [           # Algorithms to test
                #'bic',
                'cubic',
                #'highspeed',
                #'htcp',
                #'hybla',
                #'illinois',
                #'lp',
                'reno',
                #'scalable',
                'vegas',
                'veno',
                'westwood',
                #'yeah',
            ]

#
# Settings for tcp_windows
window_start = 100000
window_stop = 250000
window_step = 50000
tcp_algo = 'westwood'

#
# Settings for rlnc
#
errors = [(99, 99, 20), (99, 99, 50)]
rlnc_rates = {'helper': 4000, 'nohelper': 4000, 'noloss': 4000, 'loss': 4000}
rlnc_codings = ['nohelper']
gen_size = 64
packet_size = 1454
iperf_len = 1412
fixed_overshoot = {'helper': 1.05, 'nohelper': 1.06, 'loss': 1, 'noloss': 1}
encoders = [1, 2, 4, 8]
encoder_timeout = 10
decoder_timeout = 10
recoder_timeout = 10
helper_timeout = 10
helper_overshoot = 1
ack_timeout=[.1, .2, .3, .4, .5, .6, .7, .8, .9]
req_timeout=[.1, .2, .3, .4, .5, .6, .7, .8, .9]
fox_verbose = 3
helper_threshold = 1
systematic = 1
