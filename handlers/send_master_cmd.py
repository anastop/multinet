#!/usr/bin/env python

import sys
import util.mininet_handler_util as h_util


def master_cmd_main():
    add_remove_sw = None
    master_host = sys.argv[1]
    master_port = sys.argv[2]
    opcode = sys.argv[3]
    number_of_vms = sys.argv[4]
    starting_ip = sys.argv[5]

    if len(sys.argv) > 5:
        add_remove_sw = sys.argv[6]

    exit_on_failed_req = \
        False if opcode == 'pingall' or opcode == 'get_switches' else True

    ip_list = h_util.ip_range(starting_ip, int(number_of_vms))

    res = h_util.master_cmd(master_host
                            master_port,
                            opcode,
                            ip_list,
                            add_remove_sw)

    h_util.handle_post_request(res, exit_on_failed_req)

if __name__ == '__main__':
    master_cmd_main()
