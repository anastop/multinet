# Copyright (c) 2015 Intracom S.A. Telecom Solutions. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution,
# and is available at http://www.eclipse.org/legal/epl-v10.html

"""Support for customized booting of Mininet topologies"""

import logging
import time

import mininet
import mininet.util
import mininet.net
import mininet.node
import mininet.link
import mininet.clean
import itertools
import topologies

logging.basicConfig(level=logging.DEBUG)


class MininetNetwork(mininet.net.Mininet):

    """
    Superclass representing a Mininet topology that is being booted in custom
    way. Switches are being added in groups with certain delay between each
    group.
    """
    TOPOS = {
        'disconnected': topologies.DisconnectedTopo,
        'linear': topologies.LinearTopo,
        'ring': topologies.RingTopo,
        'mesh': topologies.MeshTopo
    }

    switch_classes = {'ovsk': mininet.node.OVSKernelSwitch, 'user': mininet.node.UserSwitch }

    def __init__(self, controller_ip, controller_port, switch_name, topo_name,
                 num_switches, group_size, group_delay_ms, hosts_per_switch,
                 dpid_offset):
        #            'ring': RingTopo,
        #            'mesh': MeshTopo,
        self._topo_name = topo_name
        self._num_switches = num_switches
        self._dpid_offset = dpid_offset
        self._group_size = group_size
        self._group_delay = float(group_delay_ms) / 1000
        self._hosts_per_switch = hosts_per_switch

        self._controller_ip = controller_ip
        self._controller_port = controller_port


        super(
            MininetNetwork,
            self).__init__(
            topo=self.TOPOS[
                self._topo_name](
                k=self._num_switches,
                n=self._hosts_per_switch,
                dpid=self._dpid_offset),
            switch=self.switch_classes[switch_name],
            host=mininet.node.Host,
            controller=mininet.node.RemoteController,
            link=mininet.link.Link,
            intf=mininet.link.Intf,
            build=False,
            xterms=False,
            cleanup=False,
            ipBase='10.0.0.0/8',
            inNamespace=False,
            autoSetMacs=False,
            autoStaticArp=False,
            autoPinCpus=False,
            listenPort=None,
            waitConnected=False)
        self.ipBaseNum += self._dpid_offset

    def buildFromTopo(self, topo=None):
        """Build mininet from a topology object
           At the end of this function, everything should be connected
           and up."""

        info = logging.info
        # Possibly we should clean up here and/or validate
        # the topo
        if self.cleanup:
            pass

        info('*** Creating network\n')

        if not self.controllers and self.controller:
            # Add a default controller
            info('*** Adding controller\n')
            classes = self.controller
            if not isinstance(classes, list):
                classes = [classes]
            for i, cls in enumerate(classes):
                # Allow Controller objects because nobody understands partial()
                if isinstance(cls, mininet.node.Controller):
                    self.addController(cls,
                                       ip=self._controller_ip,
                                       port=self._controller_port)
                else:
                    self.addController('c%d' % i,
                                       cls,
                                       ip=self._controller_ip,
                                       port=self._controller_port)

        info('*** Adding hosts:\n')
        for hostName in topo.hosts():
            kwargs_host = topo.nodeInfo(hostName)
            self.addHost(hostName, **kwargs_host)
            info(hostName + ' ')

        info('\n*** Adding switches:\n')
        for switchName in topo.switches():
            # A bit ugly: add batch parameter if appropriate
            params = topo.nodeInfo(switchName)
            cls = params.get('cls', self.switch)
            params['dpid'] = None
            #if hasattr(cls, 'batchStartup'):
            #    params.setdefault('batch', True)
            self.addSwitch(switchName, **params)
            info(switchName + ' ')

        info('\n*** Adding links:\n')
        for srcName, dstName, params in topo.links(
                sort=True, withInfo=True):
            self.addLink(**params)
            info('(%s, %s) ' % (srcName, dstName))

        info('\n')

    def init_topology(self):
        """Inits the topology"""

        logging.info("[mininet] Initializing topology.")
        self.build()
        logging.info('[mininet] Topology initialized successfully. '
                     'Booted up {0} switches'.format(self._num_switches))

    def start_topology(self):
        "Start controller and switches."
        info = logging.info
        if not self.built:
            self.build()
        info('*** Starting controller\n')
        for controller in self.controllers:
            info(controller.name + ' ')
            controller.start()
        info('\n')
        info('*** Starting %s switches\n' % len(self.switches))

        for ind, switch in enumerate(self.switches):
            if ind % self._group_size == 0:
                time.sleep(self._group_delay)
            logging.debug('[mininet] Starting switch with index {0}'.
                          format(ind + 1))
            info(switch.name + ' ')
            switch.start(self.controllers)

        started = {}
        for swclass, switches in itertools.groupby(
                sorted(self.switches, key=type), type):
            switches = tuple(switches)
            if hasattr(swclass, 'batchStartup'):
                success = swclass.batchStartup(switches)
                started.update({s: s for s in success})
        info('\n')
        if self.waitConn:
            self.waitConnected()

        logging.info('[mininet] Topology started successfully. '
                     'Booted up {0} switches'.format(self._num_switches))
        time.sleep(self._group_delay * 2)
        self.detect_hosts(ping_cnt=50)

    def detect_hosts(self, ping_cnt=50):
        for host in self.hosts:
            # ping the void
            host.sendCmd('ping -c{0} {1}'.format(str(ping_cnt),
                                                 str(self.controllers[0].IP())))
            
        logging.debug('[mininet] Hosts should be visible now')

    def get_switches(self):
        """Returns the total number of switches of the topology

        :returns: number of switches of the topology
        :rtype: int
        """
        return len(self.switches)

    def stop_topology(self):
        """Stops the topology"""

        logging.info('[mininet] Halting topology. Terminating switches.')
        for h in self.hosts:
            h.sendInt()
        mininet.clean.cleanup()
        logging.info('[mininet] Topology halted successfully')

#    def stop_switches(self):
#        '''Stops all the switches in the topology
#        '''
#        self.stop()

    def ping_all(self):
        """
        All-to-all host pinging used for testing.
        """
        self.pingAll(timeout=None)
