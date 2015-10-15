#!/usr/bin/env python

import sys
import util.mininet_handler_util as h_util


def get_switches_main():
    master_host = sys.argv[1]
    master_port = sys.argv[2]
    number_of_vms = sys.argv[3]
    starting_ip = sys.argv[4]

    exit_on_failed_req = False

    ip_list = h_util.ip_range(starting_ip, int(number_of_vms))

    res = h_util.master_cmd(master_host
                            master_port,
                            'get_switches',
                            ip_list)

    h_util.handle_post_request(res, exit_on_failed_req)

if __name__ == '__main__':
    get_switches_main()
