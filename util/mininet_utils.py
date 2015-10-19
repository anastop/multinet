# Copyright (c) 2015 Intracom S.A. Telecom Solutions. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution,
# and is available at http://www.eclipse.org/legal/epl-v10.html

"""
Mininet-related utilities
"""

import logging
import time
import util.netutil


def start_mininet_server(mininet_ssh_session, mininet_server_remote_path,
                         mininet_rest_server_host, mininet_rest_server_port):
    """
    Remotely boots a REST server on the Mininet node over an SSH connection

    :param mininet_ssh_session: ssh session used to issue remote command
    :param mininet_server_remote_path: path where mininet_custom_boot.py is
           stored and used to start the mininet topology.
    :param mininet_rest_server_host: hostname/IP the REST server should listen
           to
    :param mininet_rest_server_port: port the REST server should listen to
    :type mininet_ssh_session: ssh connection object
    :type mininet_server_remote_path: str
    :type mininet_rest_server_host: str
    :type mininet_rest_server_port: int
    """

    pythonpath = '/'.join(mininet_server_remote_path.split('/')[:-2])
    logging.info('PYTHONPATH=%s' % pythonpath)
    boot_command = (
        'sudo PYTHONPATH={0} python {1} --rest-host {2} --rest-port {3} > {1}_{2}_{3}_log.txt 2>&1 &'. format(
            pythonpath,
            mininet_server_remote_path,
            mininet_rest_server_host,
            mininet_rest_server_port))
    stdin, stdout, stderr = util.netutil.ssh_run_command(mininet_ssh_session, boot_command)
    logging.debug('{0} {1}'.format('[start_mininet_server] Boot command: ',
                                   boot_command))
    time.sleep(10)


def start_mininet_worker(mininet_ssh_session, mininet_server_remote_path,
                         mininet_rest_server_host, mininet_rest_server_port):
    """
    Remotely boots a REST server on the Mininet node over an SSH connection

    :param mininet_ssh_session: ssh session used to issue remote command
    :param mininet_server_remote_path: path where mininet_custom_boot.py is
           stored and used to start the mininet topology.
    :param mininet_rest_server_host: hostname/IP the REST server should listen
           to
    :param mininet_rest_server_port: port the REST server should listen to
    :type mininet_ssh_session: ssh connection object
    :type mininet_server_remote_path: str
    :type mininet_rest_server_host: str
    :type mininet_rest_server_port: int
    """
    start_mininet_server(mininet_ssh_session, mininet_server_remote_path,
                         mininet_rest_server_host, mininet_rest_server_port)
