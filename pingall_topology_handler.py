#!/usr/bin/env python

import sys
import mininet_handler_util as h_util


def pingall_handler_main():
    leader_host = sys.argv[1]
    leader_port = sys.argv[2]
    number_of_vms = sys.argv[3]
    starting_ip = sys.argv[4]

    exit_on_failed_req = True

    ip_list = h_util.ip_range(starting_ip, int(number_of_vms))

    res = h_util.leader_cmd(leader_host
                            leader_port,
                            'ping_all',
                            ip_list)

    h_util.handle_post_request(res, exit_on_failed_req)

if __name__ == '__main__':
    pingall_handler_main()
