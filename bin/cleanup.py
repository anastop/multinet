import util.netutil
import util.multinet_requests as m_util
import time
import logging

if __name__ == '__main__':

    conf = m_util.parse_json_conf()


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
        print('Initiating session with Multinet VM.')
        session = util.netutil.ssh_connect_or_return(curr_ip, username,
                                                     password, 10, ssh_port)
        ssh_sessions[curr_ip] = session

        get_pid_cmd = """sudo netstat -antup --numeric-ports | grep ':""" + \
                  str(mininet_rest_server_port) + \
                  """ ' | awk '{print $NF}' | awk -F '/' '{print $1}'"""
        cmd_in, cmd_out, cmd_err = util.netutil.ssh_run_command(session,
                                                                get_pid_cmd)
        multinet_server_pid = str(cmd_out.read().decode()).strip().strip('-')
        util.netutil.ssh_run_command(session, 'sudo kill -9 {0}'.
                                     format(multinet_server_pid))
        util.netutil.ssh_run_command(session, 'sudo mn -c')

        print('Delete remote Multinet directory.')
        util.netutil.remove_remote_directory(curr_ip, username, password,
                                             '/tmp/multinet/', ssh_port)
