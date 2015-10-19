import util.netutil
import util.mininet_utils
import util.multinet_requests as m_util
import sys

if __name__ == '__main__':

    conf = m_util.parse_json_conf()

    mininet_server_remote_path = '/tmp/multinet/multi/worker.py'
    master_remote_path = '/tmp/multinet/multi/master.py'
    master_ip = conf['master_ip']
    master_port = conf['master_port']
    ssh_port = conf['deploy']['ssh_port']
    worker_port = conf['worker_port']
    username = conf['deploy']['username']
    password = conf['deploy']['password']
    worker_ips = conf['worker_ip_list']
    multinet_base_dir = conf['deploy']['multinet_base_dir']

    total_worker_machines = len(worker_ips)

    ssh_sessions = {}
    copy_dest_ips = worker_ips + [master_ip]
    for curr_ip in copy_dest_ips:
        print('Initiating session with Mininet VM.')
        session = util.netutil.ssh_connect_or_return(curr_ip, username,
                                                     password, 10, ssh_port)
        ssh_sessions[curr_ip] = session

        print('Create remote directory in Mininet for storing files.')
        util.netutil.create_remote_directory(curr_ip, username, password,
                                             '/tmp/multinet/', ssh_port)

        print('Copying handlers to Mininet VMs')
        util.netutil.copy_directory_to_target(curr_ip, username, password,
                                              multinet_base_dir,
                                              '/tmp/',
                                              ssh_port)

    util.mininet_utils.start_mininet_master(ssh_sessions[master_ip],
                                            master_remote_path,
                                            master_ip,
                                            master_port,
                                            worker_port)
    for curr_ip in worker_ips:
        util.mininet_utils.start_mininet_worker(ssh_sessions[curr_ip],
                                                mininet_server_remote_path,
                                                curr_ip,
                                                worker_port)
