# Multinet

The goal of Multinet is to provide a fast, controlled and resource-efficient way
to boot large-scale (>2000 switches) SDN topologies. It builds on the
[Mininet](https://github.com/mininet/mininet) project to emulate SDN networks,
via multiple isolated Mininet topologies each mapped to a separate VM, and all
connected to the same controller.

_Why isolated topologies?_

The main motivation behind Multinet was to be able to stress an SDN controller
in terms of its switch scalable limits. In this context, Multinet contents
itself to booting topologies that are isolated between them, without caring to
interconnect them, as we believe this policy is good enough to approximate the
behavior of large-scale, real-world SDN networks and their interaction with the
controller.

_Why multiple VMs?_

The cost to boot a large Mininet topology on a single machine grows
exponentially with the number of switches. To amortize this cost, we opted to
scale out and utilize multiple VMs to spawn multiple smaller topologies in parallel.
Eventually, one of the key questions that we try to answer through Multinet is:
_what is the best time to boot-up a topology of S Mininet switches with the least
amount of resources_?


## Features

- Large-scale SDN networks emulation, using multiple isolated Mininet
  topologies distributed across multiple VMs
- Controllable boot-up of switches in groups of configurable size and
  configurable intermediate delay. This enables studying different policies of
  connecting large-scale topologies to the controller.   
- Centralized and RESTful control of topologies via a master-worker architecture
- Well-known topology types offered out-of-the-box (`disconnected`, `linear`,
  `ring`, `mesh`)
- Smooth integration with custom topologies created via the high-level Mininet API,
  provided they have slightly modified their `build` method


![Multinet Architecture](figs/multinet.png)


## Quick Start Guide

### Environment setup

To utilize the `Multinet` features you should have a distributed environment
set up with the following configuration and dependencies
- The machines should have an external IP and be able to communicate with
  each other. The easiest way to achieve this is to put the in
  a private network  
- `Python 2.7` is required
- A recent version of `Mininet` should be installed. We support `2.2.1rc`  
- `bottle`, `requests` and `paramiko` should be installed with `pip`  
- If you are under a virtualized environment, the virtio drivers provide
  greater throughput (also see [the vagrant docs](https://docs.vagrantup.com/v2/virtualbox/networking.html))

In the next section we demonstrate how to prepare such an environment using
Vagrant to boot multiple virtual machines. If you already have a custom environment
set up jump to [how to run section](#how-to-run) section.

### Environment setup using Vagrant

Just follow these instructions

1. Provision the base box

   ```bash
   cd vagrant/base
   ```

   Edit the `http_proxy` variable in the `Vagrantfile` if you are
   behind a corporate proxy. Then start provisioning as follows:

   ```bash
   vagrant up
   ```

2. Package the base box (also take a look at [this guide](https://scotch.io/tutorials/how-to-create-a-vagrant-base-box-from-an-existing-one)

   ```bash
   vagrant package --output mh-provisioned.box
   vagrant box add mh-provisioned mh-provisioned.box
   vagrant destroy
   ```

3. Configure the virtual machines

   ```bash
   cd ../packaged_multi
   ```

   Edit the `Vagrantfile` according to your preferences. For example:

   ```rb
   http_proxy = '' # If you are behind a corporate proxy
   mh_vm_basebox = 'mh-provisioned' # the name of the box we added in step 2
   mh_vm_ram_mini = '2048' # RAM size per VM
   mh_vm_cpus_mini = '2' # Number of CPUs per VM
   num_mininet_vms = 10 # Number of VMs to boot
   mh_vm_private_network_ip_mini = '10.1.1.70' # the first IP Address in the  
                                               # mininet VMs IP Address range
   forwarded_ports_guest = ['8181'] # Ports in guest that you want to forward
   forwarded_ports_host = ['8182'] # The respective ports in the host machine  
                                   # that the guest ports will be forwarded to
   ```

4. Boot the virtual machines as follows:

   ```bash
   vagrant up
   ```

### How to run

1. Edit `config.json` to your preferences  
   ```
   {
       # The location inside the VMs where the files will be copied  
       "mininet_base_dir": "/home/vagrant/nstat-mininet-handlers",  
       "leader_ip" : "10.1.1.70", # leader IP (usually the first in range)  
       # The ports the leader and the followers will listen to  
       "mininet_leader_port": 3300,  
       "mininet_server_rest_port":3333,  
       #list of the VM IP addresses
       "mininet_ip_list":[  
           "10.1.1.70",  
           "10.1.1.71"  
        ],  
       # options to enable ssh connectivity
       "mininet_ssh_port":22,  
       "mininet_username":"vagrant",  
       "mininet_password":"vagrant"  
   }
   ```

2. Run the `provision.py` script to copy and start the leader and the followers  
   ```bash
   python provision.py --json-config config.json
   ```

3. Initialize the topologies. This will build an identical topology in every
   `Multinet` instance  

   ```bash
   python init_topology_handler.py --json-config init_config.json
   ```

4. Start the topologies  

   ```bash
   python start_topology_handler <leader-ip> <leader-port> <number-of-vms>
   <starting-ip-in-range>
   ```

   For example:

   ```bash
   python start_topology_handler.py 10.1.1.40 3300 4 10.1.1.40
   ```
   The topologies should now be booted and ready for use

5. After you have used the topologies you can stop them

   ```bash
   python stop_topology_handler.py <leader-ip> <leader-port> <number-of-vms>
   <starting-ip-in-range>
   ```

   For example:

   ```bash
   python stop_topology_handler.py 10.1.1.40 3300 4 10.1.1.40
   ```

   This handler effectively performs a `sudo mn -c` operation inside each VM.

## Advanced Guide

### System Architecture
The end goal do deploy a Mininet topology to each VM. These Mininet topologies are more or less identical, the only difference being that each switch needs to have a dpid offset to avoid naming collisions in the controller's datastore.  
To achieve this we adopt a leader-follower architecture to orchestrate the instance deployment and to get a centralized and unified interface.  
We implement the following components:  
- `Leader`:  
  - Runs on a single host.  
  - Orchestrates a pool of followers  
  - Aggregates the followers status.  
  - Acts as an intermediate interface between the end user and the followers  
- `Follower`:  
  - Controls the individual Mininet topologies and does all the heavy work.

### Implementation Details

Core components
- `MininetNetwork` class
  - Extends the `Mininet` class.  
  - Adds a dpid offset during the switch creation phase to distinguish between the switches in different instances.
  - Inserts the notion of gradual switch bootup, inserting some idle time
    (`group_delay`) between the bootup of groups of switches (`group_size`)  
- `follower`  
  - creates its own `MininetNetwork` instance  
  - creates a REST API that wraps the exposed methods of that instance.  
- `leader`  
  - exposes a REST API to the end user.  
  - broadcasts the commands to the followers  
  - aggregates the responses and returns a summary response to the end user  

### Programmatic API

##### Interacting with the leader programmatically

The leader exposes a REST API as described bellow

- Initialize the topologies  
  ```python
  @bottle.route(
    '/init/controller/<ip_address>/port/<port>/switch/<switch_type>/topology/<topo>/size/<size>/group/<group>/delay/<delay>/hosts/<hosts>',
    method='POST')
  ```

- Boot the topologies  
  ```python
  @bottle.route('/start', method='POST')
  ```

- Stop the topologies  
  ```python
  @bottle.route('/stop', method='POST')
  ```

- Perform a `pingall` in each topology  
  ```python
  @bottle.route('/ping_all', method='POST')
  ```

- Get the number of switches in each topology  
  ```python
  @bottle.route('/get_switches', method='POST')
  ```

You can also utilize the following wrapper functions
from the `mininet_handler_util` module

```python
# Send a POST request to the leader 'init' endpoint
mininet_handler_util.leader_init(leader_host,
                                 leader_port,
                                 ip_list,
                                 controller_ip_address,
                                 controller_of_port,
                                 switch_type,
                                 mininet_topo_type,
                                 mininet_topo_size,
                                 mininet_group_size,
                                 mininet_group_delay,
                                 mininet_hosts_per_switch)
```

```python
# Send a POST request to any leader endpoint (except for 'init').
# The endpoint is specified by the 'opcode' parameter
mininet_handler_util.leader_cmd(leader_host,
                                leader_port,
                                opcode,
                                ip_list)
```

#### Adding your own topologies

First of all **note** that the build method signature of any existing topology
created with the high level Mininet API need to be modified to conform with
the following method signature in order to be compatible
```python
# k is the number of switches
# n is the number of hosts per switch
# dpid is the dpid offset
def build(self, k=2, n=1, dpid=1, **_opts):
```

1. Create a topology with the Mininet high level API, for example

 ```python
 ## mytopo.py
 class MyTopo(Topo):
       "Disconnected topology of k switches, with n hosts per switch."

       def build(self, k=2, n=1, dpid=1, **_opts):
           """
           k: number of switches
           n: number of hosts per switch
           dpid: the dpid offset (to enable distributed topology creation)
           """
           self.k = k
           self.n = n

           for i in xrange(k):
               # Add switch
               switch = self.addSwitch(genSwitchName(i, dpid))
              # Add hosts to switch
               for j in xrange(n):
                   host = self.addHost(genHostName(i, j, dpid, n))
                   self.addLink(host, switch)
 ```

2. Add it to the `MininetNetwork.TOPOS` dictionary

   ```python
   # follower.py
   import mytopo ...
   MininetNetwork.TOPOS['mytopo'] = mytopo.MyTopo
   MININET_TOPO = MininetNetwork( ... )
   ```
   ```python
   # or from inside MininetNetwork.py
   TOPOS = {
      'linear': ...
      'mytopo': mytopo.MyTopo
   }
   ```

__TODO__: a "Code Structure" subsection would be really helpful. See for example
NSTAT wiki: this is meant to provide short descriptions of the source files.
You may provide descriptions of groups of source files, if you like.
