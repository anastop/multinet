#!/usr/bin/env python

# Copyright (c) 2015 Intracom S.A. Telecom Solutions. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution,
# and is available at http://www.eclipse.org/legal/epl-v10.html

"""
With this module we create the master REST server
to manage the distributed topologies
"""

import argparse
import bottle
import logging
import util.multinet_requests as m_util

# We must define logging level separately because this module runs
# independently.
logging.basicConfig(level=logging.DEBUG)

WORKER_PORT = ''


@bottle.route(
    '/init/controller/<ip_address>/port/<port>/switch/<switch_type>/topology/<topo>/size/<size>/group/<group>/delay/<delay>/hosts/<hosts>',
    method='POST')
def init(ip_address, port, topo, switch_type, size, group, delay, hosts):
    """
    Broadcast the POST request to the 'init' endpoint of the workers
    Aggregate the responses

    Args:
      controller_ip_address (str): The IP address of the controller
      controller_of_port (int): The OpenFlow port of the controller
      switch_type (str): The type of soft switch to use for the emulation
      topo_type (str): The type of the topology we want to build
      topo_size (int): The size of the topology we want to build
      group_size (int): The number of switches in a gorup for gradual bootup
      group_delay (int): The delay between the bootup of each group
      hosts_per_switch (int): The number of hosts connected to each switch

    Returns:
      list: A list of responses for all the POST requests performed
    """
    global WORKER_PORT
    ip_list = bottle.request.json
    reqs = m_util.broadcast_init(ip_list,
                                 WORKER_PORT,
                                 ip_address,
                                 port,
                                 switch_type,
                                 topo,
                                 size,
                                 group,
                                 delay,
                                 hosts)
    stat, bod = m_util.aggregate_broadcast_response(reqs)
    return bottle.HTTPResponse(status=stat, body=bod)


@bottle.route('/start', method='POST')
def start():
    """
    Broadcast the POST request to the 'start' endpoint of the workers
    Aggregate the responses
    """
    global WORKER_PORT
    ip_list = bottle.request.json
    reqs = m_util.broadcast_cmd(ip_list,
                                WORKER_PORT,
                                'start')
    stat, bod = m_util.aggregate_broadcast_response(reqs)
    return bottle.HTTPResponse(status=stat, body=bod)


@bottle.route('/get_switches', method='POST')
def get_switches():
    """
    Broadcast the POST request to the 'get_switches' endpoint of the workers
    Aggregate the responses
    """
    global WORKER_PORT
    ip_list = bottle.request.json
    reqs = m_util.broadcast_cmd(ip_list,
                                WORKER_PORT,
                                'get_switches')
    stat, bod = m_util.aggregate_broadcast_response(reqs)
    return bottle.HTTPResponse(status=stat, body=bod)


@bottle.route('/stop', method='POST')
def stop():
    """
    Broadcast the POST request to the 'stop' endpoint of the workers
    Aggregate the responses
    """
    global WORKER_PORT
    ip_list = bottle.request.json
    reqs = m_util.broadcast_cmd(ip_list,
                                WORKER_PORT,
                                'stop')
    stat, bod = m_util.aggregate_broadcast_response(reqs)
    return bottle.HTTPResponse(status=stat, body=bod)


@bottle.route('/ping_all', method='POST')
def ping_all():
    """
    Broadcast the POST request to the 'ping_all' endpoint of the workers
    Aggregate the responses
    """
    global WORKER_PORT
    ip_list = bottle.request.json
    reqs = m_util.broadcast_cmd(ip_list,
                                WORKER_PORT,
                                'ping_all')
    stat, bod = m_util.aggregate_broadcast_response(reqs)
    return bottle.HTTPResponse(status=stat, body=bod)


def rest_start():
    """Start the master server"""
    global WORKER_PORT
    parser = argparse.ArgumentParser()
    parser.add_argument('--master-host',
                        required=True,
                        type=str,
                        dest='master_host',
                        action='store',
                        help='IP address to start the master server')
    parser.add_argument('--master-port',
                        required=True,
                        type=str,
                        dest='master_port',
                        action='store',
                        help='Port number to start the master server')
    parser.add_argument('--worker-port',
                        required=True,
                        type=str,
                        dest='worker_port',
                        action='store',
                        help='Port number to the Mininet REST server')
    args = parser.parse_args()
    WORKER_PORT = args.WORKER_PORT
    bottle.run(host=args.master_host, port=args.master_port, debug=True)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    rest_start()
