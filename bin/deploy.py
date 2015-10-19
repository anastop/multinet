import util.netutil
import util.multinet_requests as m_util
import time
import logging

if __name__ == '__main__':

    conf = m_util.parse_json_conf()

    worker_remote_path = '/tmp/multinet/multi/worker.py'
    master_remote_path = '/tmp/multinet/multi/master.py'
    master_ip = conf['master_ip']
    master_port = conf['master_port']
    ssh_port = conf['deploy']['ssh_port']
    worker_port = conf['worker_port']
    username = conf['deploy']['username']
    password = conf['deploy']['password']
    worker_ips = conf['worker_ip_list']
    multinet_base_dir = conf['deploy']['multinet_base_dir']
    # TODO hard-coded for now, fix later
    config_file = '/tmp/multinet/config/config.json'
    pythonpath = '/'.join(master_remote_path.split('/')[:-2])
    logging.info('PYTHONPATH=%s' % pythonpath)
    master_boot_command = (
        'PYTHONPATH={0} python {1} --json-config {2} > /tmp/multinet/master_log.txt 2>&1 &'.format(
            pythonpath,
            master_remote_path,
            config_file))

    total_worker_machines = len(worker_ips)

    ssh_sessions = {}
    copy_dest_ips = worker_ips + [master_ip]
    for curr_ip in copy_dest_ips:
        print('Initiating session with Multinet VM.')
        session = util.netutil.ssh_connect_or_return(curr_ip, username,
                                                     password, 10, ssh_port)
        ssh_sessions[curr_ip] = session

        print('Create remote directory in Multinet for storing files.')
        util.netutil.create_remote_directory(curr_ip, username, password,
                                             '/tmp/multinet/', ssh_port)

        print('Copying handlers to Multinet VMs')
        util.netutil.copy_directory_to_target(curr_ip, username, password,
                                              multinet_base_dir,
                                              '/tmp/',
                                              ssh_port)

    util.netutil.ssh_run_command(ssh_sessions[master_ip], master_boot_command)
    logging.debug(
        '[start master {0}] Boot command:  {1}'.format(
            master_ip,
            master_boot_command))
    time.sleep(10)
    for curr_ip in worker_ips:
        worker_boot_command = (
            'sudo PYTHONPATH={0} python {1} --rest-host {2} --rest-port {3} > {1}_{2}_{3}_log.txt 2>&1 &'. format(
                pythonpath,
                worker_remote_path,
                curr_ip,
                worker_port))
        stdin, stdout, stderr = util.netutil.ssh_run_command(
            ssh_sessions[curr_ip], worker_boot_command)
        logging.debug(
            '[start worker {0}] Boot command: {1}'.format(
                curr_ip,
                worker_boot_command))
        time.sleep(10)
