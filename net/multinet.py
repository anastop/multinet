# Copyright (c) 2015 Intracom S.A. Telecom Solutions. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution,
# and is available at http://www.eclipse.org/legal/epl-v10.html

"""
Builds on Mininet to emulate large-scale SDN networks
by creating distributed Mininet topologies
"""

import logging
import time

import mininet
import mininet.util
import mininet.net
import mininet.node
import mininet.link
import mininet.clean
import itertools
import net.topologies

logging.basicConfig(level=logging.DEBUG)


class Multinet(mininet.net.Mininet):

    """
    Superclass representing a Mininet topology that is being booted in custom
    way. Switches are being added in groups with certain delay between each
    group.
    """

    """
    name - class correspondence for the topologies
    """ 
    TOPOS = {
        'disconnected': net.topologies.DisconnectedTopo,
        'linear': net.topologies.LinearTopo,
        'ring': net.topologies.RingTopo,
        'mesh': net.topologies.MeshTopo
    }

    """
    name - class correspondence for the soft switches
    """
    SWITCH_CLASSES = {
        'ovsk': mininet.node.OVSKernelSwitch,
        'user': mininet.node.UserSwitch
    }

    def __init__(self, controller_ip, controller_port, switch_type, topo_type,
                 num_switches, group_size, group_delay_ms, hosts_per_switch,
                 dpid_offset, auto_detect_hosts=False):
        """
        Call the super constructor and initialize any extra properties we want to user

        Args:
            controller_ip (str): The IP address of the RemoteController
            controller_port (int): The OpenFlow port of the RemoteController
            switch_type (str): The type of the soft switch to use for the emulation
            topo_type (str): The type of the topology to build
            num_switches (int): The number of the switches in the topology
            group_size (int): The number of switches in a gorup for gradual bootup
            group_delay_ms (int): The delay between the bootup of each group
            hosts_per_switch (int): The number of hosts connected to each switch
            dpid_offset (int): The dpid offset of this worker
            auto_detect_hosts (bool): Enable or disable automatic host detection
        """
        self._topo_type = topo_type
        self._num_switches = num_switches
        self._dpid_offset = dpid_offset
        self._group_size = group_size
        self._group_delay = float(group_delay_ms) / 1000
        self._hosts_per_switch = hosts_per_switch
        self.auto_detect_hosts = auto_detect_hosts
        self._controller_ip = controller_ip
        self._controller_port = controller_port
        self.booted_switches = 0

        super(
            Multinet,
            self).__init__(
            topo=self.TOPOS[
                self._topo_type](
                k=self._num_switches,
                n=self._hosts_per_switch,
                dpid=self._dpid_offset),
            switch=self.SWITCH_CLASSES[switch_type],
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
            listenPort=6634,
            waitConnected=False)
        self.ipBaseNum += self._dpid_offset

    def buildFromTopo(self, topo=None):
        """
        Build mininet from a topology object
        At the end of this function, everything should be connected and up.
        Use the dpid offset to distinguise the nodes between Multinet Instances
        """

        info = logging.info
        # Possibly we should clean up here and/or validate
        # the topo
        if self.cleanup:
            pass

        info('*** Creating network\n')

        if not self.controllers and self.controller:
            # Add a default controller
            info('*** Adding controller\n')
            try:
                classes = self.controller
                if not isinstance(classes, list):
                    classes = [classes]
                for i, cls in enumerate(classes):
                    # Allow Controller objects because nobody understands partial()
                    if isinstance(cls, mininet.node.Controller):
                        self.addController(controller=cls,
                                           ip=self._controller_ip,
                                           port=self._controller_port)
                    else:
                        self.addController(name='c{0}'.format(i),
                                           controller=cls,
                                           ip=self._controller_ip,
                                           port=self._controller_port)
            except:
                self.addController(name='c{0}'.format(i), controller=mininet.node.DefaultController)

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
        """
        Init the topology
        """

        logging.info("[mininet] Initializing topology.")
        self.build()
        logging.info('[mininet] Topology initialized successfully. '
                     'Booted up {0} switches'.format(self._num_switches))

    def start_topology(self):
        """
        Start controller and switches.
        Do a gradual bootup.
        """
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
            self.booted_switches += 1

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

        if self.auto_detect_hosts:
            self.detect_hosts(ping_cnt=50)

    def detect_hosts(self, ping_cnt=50):
        """
        Do a ping from each host to the void to send a PACKET_IN to the controller
        and enable the controller host detector

        Args:
            ping_cnt: Number of pings to send from each host
        """
        for host in self.hosts:
            # ping the void
            host.sendCmd('ping -c{0} {1}'.format(str(ping_cnt),
                                                 str(self.controllers[0].IP())))
            
        logging.debug('[mininet] Hosts should be visible now')

    def get_switches(self):
        """Returns the total number of switches of the topology

        Returns:
            (int): number of switches in the topology
        """
        return self.booted_switches

    def stop_topology(self):
        """
        Stops the topology
        """

        logging.info('[mininet] Halting topology. Terminating switches.')
        for h in self.hosts:
            h.sendInt()
        mininet.clean.cleanup()
        self.switches = []
        self.hosts = []
        self.links = []
        self.controllers = []
        self.built = False
        self.booted_switches = 0
        logging.info('[mininet] Topology halted successfully')

    def ping_all(self):
        """
        All-to-all host pinging used for testing.
        """
        self.pingAll(timeout=None)
