# Multinet

The goal of Multinet is to provide a fast, controlled and resource-efficient way
to boot large-scale (>2000 switches) SDN topologies. It builds on the
[Mininet](https://github.com/mininet/mininet) project to emulate SDN networks,
via multiple isolated Mininet topologies each mapped to a separate VM, and all
connected to the same controller.

_Why isolated topologies?_

The main motivation behind Multinet was to be able to stress an SDN controller
in terms of its switch scalable limits. In this context, Multinet contents
itself to booting topologies that are isolated from each other, without really caring
to be interconnected, as we believe this policy is simple and good enough 
to approximate the behavior of large-scale realistic SDN networks and their 
interaction with the controller. If creating large-scale _interconnected_ 
topologies is your primary concern, then you might want to look at other efforts 
such as [Maxinet](https://github.com/mininet/mininet/wiki/Cluster-Edition-Prototype)
or the [Cluster Edition Prototype](https://github.com/mininet/mininet/wiki/Cluster-Edition-Prototype)
of Mininet. Instead, Multinet clearly emphasizes on creating scalable pressure to 
the controller and provides options to control certain aspects that affect the interaction 
of the and the controller, such as the way these are being connected to it during start-up. 

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


## Getting Started

### Environment setup

To use Multinet you should have a distributed environment of machines configured
as follows:

- Software dependences:
    - Python 2.7
    - `bottle`, `requests` and `paramiko` Python packages
    - a recent version of Mininet (we support 2.2.1rc)
- Connectivity:
    - the machines should be able to communicate with each other
    - the machines should have SSH connectivity

In the next section we demonstrate how to prepare such an environment using
[Vagrant](https://www.vagrantup.com/) to provision and boot multiple VMs.
If you already have a custom environment set up, jump to
[how to run](#how-to-run) section.

### Environment setup using Vagrant

1. Provision the base box

   ```bash
   cd vagrant/base/
   ```

   If you sit behind a proxy, edit the `http_proxy` variable in the
   `Vagrantfile`. Then start provisioning:

   ```bash
   vagrant up
   ```

2. Package the base box

   ```bash
   vagrant package --output mh-provisioned.box
   vagrant box add mh-provisioned mh-provisioned.box
   vagrant destroy
   ```

   For more info on Vagrant box packaging take a look at
   [this guide](https://scotch.io/tutorials/how-to-create-a-vagrant-base-box-from-an-existing-one)

3. Configure the virtual machines

   ```bash
   cd vagrant/packaged_multi/
   ```

   Edit the `Vagrantfile` according to your preferences. For example:

   ```rb
   http_proxy = '' #if you sit behind a corporate proxy, provide it here
   mh_vm_basebox = 'mh-provisioned' #the name of the Vagrant box we created in step 2
   mh_vm_ram_mini = '2048' #RAM size per VM
   mh_vm_cpus_mini = '2' #number of CPUs per VM
   num_mininet_vms = 10 #total number of VMs to boot
   mh_vm_private_network_ip_mini = '10.1.1.70' #the first IP Address in the
                                               #mininet VMs IP Address range
   forwarded_ports_guest = ['8181'] #ports in guest that you want to forward
   forwarded_ports_host = ['8182'] #the respective ports in the host machine
                                   #where the guest ports will be forwarded to
   ```

4. Boot the virtual machines as follows:

   ```bash
   vagrant up
   ```

### How to run

1. Edit `config.json` to your preferences:

   ```json
   {
       "multinet_base_dir": "/home/vagrant/multinet",  
       "master_ip" : "10.1.1.70",
       "master_port": 3300,  
       "worker_port": 3333,  
       "worker_ip_list": [ "10.1.1.70", "10.1.1.71" ],  
       "ssh_port": 22,  
       "username": "vagrant",  
       "password": "vagrant"  
   }
   ```

   In the file above:
   - `multinet_base_dir` is the location inside the machines where deployment
      files will be copied. This location is common for all participating machines
   - `master_ip` is the IP address of the machine where the master will run
   - `master_port` is the port where the master listens for REST requests
      from external client applications
   - `worker_port` is the port where each worker listens for REST requests
      from the master
   - `worker_ip_list` is the list with the IPs of all machines where workers
      will be created to launch topologies
   - `ssh_port` is the port where machines listen for SSH connections
   - `username`, `password` are the credentials used to access via SSH the machines


2. Run the `provision.py` script to copy and start the master and the workers  

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
   python start_topology_handler <master-ip> <master-port> <number-of-vms>
   <starting-ip-in-range>
   ```

   For example:

   ```bash
   python start_topology_handler.py 10.1.1.40 3300 4 10.1.1.40
   ```
   The topologies should now be booted and ready for use

5. After you have used the topologies you can stop them

   ```bash
   python stop_topology_handler.py <master-ip> <master-port> <number-of-vms>
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
To achieve this we adopt a master-worker architecture to orchestrate the instance deployment and to get a centralized and unified interface.  
We implement the following components:  
- `master`:  
  - Runs on a single host.  
  - Orchestrates a pool of workers  
  - Aggregates the workers status.  
  - Acts as an intermediate interface between the end user and the workers  
- `worker`:  
  - Controls the individual Mininet topologies and does all the heavy work.

### Implementation Details

_Core components_  
- `MininetNetwork` class  
  - Extends the `Mininet` class.  
  - Adds a dpid offset during the switch creation phase to distinguish between the switches in different instances.  
  - Inserts the notion of gradual switch bootup, inserting some idle time
    (`group_delay`) between the bootup of groups of switches (`group_size`)  
- `worker`  
  - creates its own `MininetNetwork` instance  
  - creates a REST API that wraps the exposed methods of that instance.  
- `master`  
  - exposes a REST API to the end user.  
  - broadcasts the commands to the workers  
  - aggregates the responses and returns a summary response to the end user  

_Gradual bootup_  
We observed that the SDN controller displays some instability issues when
it is overwhelmed with switch additions. The solution we pose to this problem
is the gradual switch bootup.  
In more detail, we modified the Mininet `start` method as follows
- We split the switches we need to start in groups
- The size of each group is specified by the `group_size` parameter    
- We start the switches in each group normally  
- After all the switches in a group have started we insert a delay  
- The delay is specified by the `group_delay` parameter  

We have observed that this method allows us to boot larger topologies with
greater stability. Moreover it gives us a way to estimate the boot time of
a topology in a deterministic way.

### Programmatic API

##### Interacting with the master programmatically

The master exposes a REST API as described bellow

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
# Send a POST request to the master 'init' endpoint
mininet_handler_util.master_init(master_host,
                                 master_port,
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
# Send a POST request to any master endpoint (except for 'init').
# The endpoint is specified by the 'opcode' parameter
mininet_handler_util.master_cmd(master_host,
                                master_port,
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
   # worker.py
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

## Code Structure


## Code structure

| Path                                             | Description                                     |
|--------------------------------------------------|-------------------------------------------------|
| `figs/`                 | Figures needed for documentation |
| `vagrant/`                                        | Vagrantfiles for fast provisioning of a running environment |
| `config/`                                   | configuration files for the init handler and the deploy script |
| `handlers/`                 | Command line wrappers for the leader commands |
| `util/`                                     | A more generic utility module |
| `cleanup.sh`                           | cleanup script to reset the virtual machines environment |
| `deploy.py`                              | Automation script to copy and start the master and the workers in the virtual machines |
| `master.py`                              | Master REST server |
| `worker.py`                              | Worker REST server |
| `MininetNetwork.py`                                   | Class inheriting from the core `Mininet` with added / modified functionality |
| `topologies.py`       | example topologies |  
