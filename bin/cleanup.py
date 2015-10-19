import util.netutil
import util.multinet_requests as m_util
import time
import logging

def kill_remote_server(session, server_port):
  #  get_pid = """sudo netstat -antup --numeric-ports | grep ':""" + \
  #      str(server_port) + \
  #      """ ' | awk '{print $NF}' | awk -F '/' '{print $1}'"""
    get_pid = 'sudo netstat -antup --numeric-ports | grep "%s" | awk \'{print $NF}\' | awk -F \'/\' \'{print $1}\'' % str(server_port)
    _, cmd_out, _ = util.netutil.ssh_run_command(session, get_pid)
    pid = str(cmd_out.read().decode()).strip().strip('-')
    util.netutil.ssh_run_command(session, 'sudo kill -9 {0}'.format(pid))


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
    copy_dest_ips = worker_ips + [master_ip] if master_ip not in worker_ips else worker_ips
    for curr_ip in copy_dest_ips:
        print('Initiating session with Multinet VM.')
        session = util.netutil.ssh_connect_or_return(curr_ip, username,
                                                     password, 10, ssh_port)
        ssh_sessions[curr_ip] = session

        kill_remote_server(session, worker_port)
        kill_remote_server(session, master_port)

        util.netutil.ssh_run_command(session, 'sudo mn -c')

        print('Delete remote Multinet directory.')
        util.netutil.ssh_run_command(session, 'rm -rf /tmp/multinet')
