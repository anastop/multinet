#! /usr/bin/python

# Copyright (c) 2015 Intracom S.A. Telecom Solutions. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution,
# and is available at http://www.eclipse.org/legal/epl-v10.html

"""With this module re start the REST mininet server, that manages a mininet
topology"""

import argparse
import bottle
import json
import logging
import net.topologies

from net.multinet import Multinet

# We must define logging level separately because this module runs
# independently.
logging.basicConfig(level=logging.DEBUG)

MININET_TOPO = None


@bottle.route(
    '/init/controller/<ip_address>/port/<port>/switch/<switch_type>/topology/<topo>/size/<size>/group/<group>/delay/<delay>/hosts/<hosts>/dpid/<dpid>',
    method='POST')
def init(ip_address, port, switch_type, topo, size, group, delay, hosts, dpid):
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

    global MININET_TOPO
    MININET_TOPO = Multinet(
        ip_address,
        int(port),
        switch_type,
        topo,
        int(size),
        int(group),
        int(delay),
        int(hosts),
        int(dpid))
    MININET_TOPO.init_topology()


@bottle.route('/start', method='POST')
def start():
    """
    Calls the start_topology() method of the current topology object to start
    the switches of the topology.
    """
    MININET_TOPO.start_topology()


@bottle.route('/detect_hosts', method='POST')
def start():
    """
    Calls the detect_hosts() method of the current topology object to make
    the hosts visible in the controller side
    """
    MININET_TOPO.detect_hosts()


@bottle.route('/get_switches', method='POST')
def get_switches():
    """
    Calls the get_switches() method of the current topology object to query the
    current number of switches.

    :returns: number of switches of the topology
    :rtype: int
    """

    global MININET_TOPO
    return json.dumps(MININET_TOPO.get_switches())


@bottle.route('/stop', method='POST')
def stop():
    """
    Calls the stop_topology() method of the current topology object to terminate
    the topology.
    """

    global MININET_TOPO
    MININET_TOPO.stop_topology()


@bottle.route('/ping_all', method='POST')
def ping_all():
    """
    Calls the ping_all() method of the current topology object to issue
    all-to-all ping commands
    """

    global MININET_TOPO
    MININET_TOPO.ping_all()


@bottle.route('/ping_line_pair/host1/<host1>/host2/<host2>', method='POST')
def ping_line_pair(host1, host2):
    """
    Calls the ping_all() method of the current topology object to issue
    all-to-all ping commands
    """
    global MININET_TOPO

    def hostName(host):
        parsed = [int(x) for x in host.split(',')]
        sw, port = parsed[0], parsed[1]
        return net.topologies.genHostName(sw,
                                      port,
                                      MININET_TOPO._dpid_offset,
                                      MININET_TOPO._num_switches)

    h1, h2 = hostName(host1), hostName(host2)

    ploss = MININET_TOPO.ping([h1, h2])
    status = 200 if not ploss == 100 else 500
    return bottle.HTTPResponse(status=status, body='')


def rest_start():
    """Starts Mininet REST server"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--rest-host',
                        required=True,
                        type=str,
                        dest='rest_host',
                        action='store',
                        help='IP address to start Mininet REST server')
    parser.add_argument('--rest-port',
                        required=True,
                        type=str,
                        dest='rest_port',
                        action='store',
                        help='Port number to start Mininet REST server')
    args = parser.parse_args()

    bottle.run(host=args.rest_host, port=args.rest_port, debug=True)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    rest_start()
