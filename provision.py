import util.netutil
import util.mininet_utils
import argparse
import json
import logging
import sys

if __name__ == '__main__':


    logging.getLogger().setLevel(logging.DEBUG)
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--json-config',
                        required=True,
                        type=str,
                        dest='json_config',
                        action='store',
                        help='Test configuration file (JSON)')


    args = parser.parse_args()
    json_conf_file = open(args.json_config)
    conf = json.load(json_conf_file)

    mininet_server_remote_path = \
            '/tmp/transfered_files/nstat-mininet-handlers/follower.py'
    leader_remote_path = \
            '/tmp/transfered_files/nstat-mininet-handlers/leader.py'
    leader_ip = conf['leader_ip']
    leader_port = conf['mininet_leader_port']
    mininet_ssh_port = conf['mininet_ssh_port']
    mininet_rest_server_port = conf['mininet_server_rest_port']
    mininet_username = conf['mininet_username']
    mininet_password = conf['mininet_password']
    mininet_ip_list = conf['mininet_ip_list']
    mininet_base_dir = conf['mininet_base_dir']

    total_vms=len(mininet_ip_list)
    #total_mininet_size=[int((sz/total_vms)*total_vms) for sz in conf['mininet_size']]

    mininet_ssh_sessions = {}
    ip_list_cp_files = mininet_ip_list + [conf['leader_ip']]
    for curr_ip in ip_list_cp_files:
        logging.info('Initiating session with Mininet VM.')
        mininet_ssh_session = util.netutil.ssh_connect_or_return(curr_ip,
            mininet_username, mininet_password, 10, mininet_ssh_port)
        mininet_ssh_sessions[curr_ip] = mininet_ssh_session

        logging.info(
            'Create remote directory in Mininet for storing files.')
        util.netutil.create_remote_directory(curr_ip, mininet_username,
            mininet_password, '/tmp/transfered_files/',
            mininet_ssh_port)
        logging.info('Copying handlers to Mininet VMs')
        util.netutil.copy_directory_to_target(curr_ip,
                                            mininet_username,
                                            mininet_password,
                                            mininet_base_dir,
                                            '/tmp/transfered_files/',
                                            mininet_ssh_port)

    util.mininet_utils.start_mininet_leader(mininet_ssh_sessions[leader_ip],
                                       leader_remote_path,
                                       leader_ip,
                                       leader_port,
                                       mininet_rest_server_port)
    for curr_ip in mininet_ip_list:
        util.mininet_utils.start_mininet_follower(mininet_ssh_sessions[curr_ip],
                                             mininet_server_remote_path,
                                             curr_ip,
                                             mininet_rest_server_port)
