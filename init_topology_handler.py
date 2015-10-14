#!/usr/bin/env python

import json
import mininet_handler_util as h_util
import argparse

def leader_init_main():
    logging.getLogger().setLevel(logging.DEBUG)
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--json-config',
                        required=True,
                        type=str,
                        dest='json_config',
                        action='store',
                        help='Configuration file (JSON)')


    args = parser.parse_args()
    json_conf_file = open(args.json_config)
    init_conf = json.load(json_conf_file)
    
    h_util.leader_init(init_conf['leader_host'],
                       init_conf['leader_port'],
                       init_conf['ip_list'],
                       init_conf['controller_ip_address'],
                       init_conf['controller_of_port'],
                       init_conf['mininet_switch_type'],
                       init_conf['mininet_topo_type'],
                       init_conf['mininet_topo_size'],
                       init_conf['mininet_group_size'],
                       init_conf['mininet_group_delay'],
                       init_conf['mininet_hosts_per_switch'])

if __name__ == '__main__':
    leader_init_main()
