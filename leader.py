#!/usr/bin/env python

# Copyright (c) 2015 Intracom S.A. Telecom Solutions. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution,
# and is available at http://www.eclipse.org/legal/epl-v10.html

"""With this module ee start the REST mininet server, that manages a mininet distributed
topology"""

import argparse
import bottle
import logging
import mininet_handler_util as h_util

# We must define logging level separately because this module runs
# independently.
logging.basicConfig(level=logging.DEBUG)

REST_PORT = ''


@bottle.route(
    '/init/controller/<ip_address>/port/<port>/switch/<switch_type>/topology/<topo>/size/<size>/group/<group>/delay/<delay>/hosts/<hosts>',
    method='POST')
def init(ip_address, port, topo, switch_type, size, group, delay, hosts):
    """
    Initializes a new topology object. The type of the new topology is
    defined by the topo parameter.

    :param ip_address: controller IP address
    :param port: controller OF port number
    :param topo: type of the topology we want to start ("DisconnectedTopo",
                 "LinearTopo", "MeshTopo")
    :param size: initial number of switches to boot the topology with
    :param group: group addition size
    :paran delay: group addition delay (in milliseconds)
    :param hosts: number of hosts per switch.
    :param dpid: dpid offset of topology.
    :type ip_address: str
    :type port: int
    :type topo: str
    :type size: int
    :type group: int
    :type delay: int
    :type hosts: int
    :type dpid: int
    """
    global REST_PORT
    ip_list = bottle.request.json
    reqs = h_util.broadcast_init(ip_list,
                                 REST_PORT,
                                 ip_address,
                                 port,
                                 switch_type,
                                 topo,
                                 size,
                                 group,
                                 delay,
                                 hosts)
    stat, bod = h_util.aggregate_broadcast_response(reqs)
    return bottle.HTTPResponse(status=stat, body=bod)


@bottle.route('/start', method='POST')
def start():
    """
    Calls the start_topology() method of the current topology object to start
    the switches of the topology.
    """
    global REST_PORT
    ip_list = bottle.request.json
    reqs = h_util.broadcast_cmd(ip_list,
                                REST_PORT,
                                'start')
    stat, bod = h_util.aggregate_broadcast_response(reqs)
    return bottle.HTTPResponse(status=stat, body=bod)


@bottle.route('/get_switches', method='POST')
def get_switches():
    """
    Calls the get_switches() method of the current topology object to query the
    current number of switches.

    :returns: number of switches of the topology
    :rtype: int
    """
    global REST_PORT
    ip_list = bottle.request.json
    reqs = h_util.broadcast_cmd(ip_list,
                                REST_PORT,
                                'get_switches')
    stat, bod = h_util.aggregate_broadcast_response(reqs)
    return bottle.HTTPResponse(status=stat, body=bod)


@bottle.route('/stop', method='POST')
def stop():
    """
    Calls the stop_topology() method of the current topology object to terminate
    the topology.
    """
    global REST_PORT
    ip_list = bottle.request.json
    reqs = h_util.broadcast_cmd(ip_list,
                                REST_PORT,
                                'stop')
    stat, bod = h_util.aggregate_broadcast_response(reqs)
    return bottle.HTTPResponse(status=stat, body=bod)


@bottle.route('/ping_all', method='POST')
def ping_all():
    """
    Calls the ping_all() method of the current topology object to issue
    all-to-all ping commands
    """
    global REST_PORT
    ip_list = bottle.request.json
    reqs = h_util.broadcast_cmd(ip_list,
                                REST_PORT,
                                'ping_all')
    stat, bod = h_util.aggregate_broadcast_response(reqs)
    return bottle.HTTPResponse(status=stat, body=bod)


def rest_start():
    """Starts leader server"""
    global REST_PORT
    parser = argparse.ArgumentParser()
    parser.add_argument('--leader-host',
                        required=True,
                        type=str,
                        dest='leader_host',
                        action='store',
                        help='IP address to start the leader server')
    parser.add_argument('--leader-port',
                        required=True,
                        type=str,
                        dest='leader_port',
                        action='store',
                        help='Port number to start the leader server')
    parser.add_argument('--rest-port',
                        required=True,
                        type=str,
                        dest='rest_port',
                        action='store',
                        help='Port number to the Mininet REST server')
    args = parser.parse_args()
    REST_PORT = args.rest_port
    bottle.run(host=args.leader_host, port=args.leader_port, debug=True)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    rest_start()
