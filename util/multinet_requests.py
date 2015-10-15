import requests
import sys
import multiprocessing
import json
import time
import logging
import argparse


logging.getLogger().setLevel(logging.DEBUG)

def parse_json_conf():
    """Parse a JSON configuration file.
    The path to this file is given as a command line argument.

    Command Line Args:
      --json-config (str): The path to the JSON configuration file

    Returns:
      dict: The parsed json configuration
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--json-config',
                        required=True,
                        type=str,
                        dest='json_config',
                        action='store',
                        help='Configuration file (JSON)')


    args = parser.parse_args()

    conf = {}
    with open(args.json_config) as conf_file:
      conf = json.load(conf_file)
    return conf


def ip_range(start_ip, num_ips):
    """Generate a number of consecutive ips
    Assume the ip range fits in one subnet

    Args:
      start_ip (str): The starting IP in the range
      num_ips (int): The number of consecutive IP addresses to generate

    Returns:
      list: The list of consecutive IP addresses
    """
    ip_split = start_ip.split('.')
    ip_pref, ip_suf = ip_split[:-1], int(ip_split[-1])
    return ['.'.join(ip_pref + [str(ip_suf + i)]) for i in xrange(0, num_ips)]


def dpid_offset_range(num_vms):
    """Generate a range of dpid dpid_offset_list
    Every VM has allocates 1000 unique dpid offsets

    Args:
      num_vms (int): The number of virtual machines

    Returns:
      list: The dpid offset range
    """
    return [1000 * i + 1 for i in xrange(0, num_vms)]


def make_post_request(host_ip, host_port, route, data=None):
    """Make a POST request
    Make a POST request to a remote REST server and log the response

    Args:
      host_ip (str): The ip of the remote REST server
      host_port (int): The port of the remote REST server
      route (str): The REST API endpoint
      data (dict or list): A dictionary or a list with any additional data

    Returns:
      requests.models.Response: The HTTP response for the performed request
    """
    session = requests.Session()
    session.trust_env = False

    url = 'http://{0}:{1}/{2}'.format(host_ip, host_port, route)
    route_name = route.split('/')[0]
    logging.info('[{0}_topology_handler][url] {1}'.format(route_name, url))
    if data is None:
        post_call = session.post(url)
    else:
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        post_call = requests.post(
            url,
            data=json.dumps(data),
            headers=headers)
    logging.info('[{0}_topology_handler][response status code] {1}'.
          format(route_name, post_call.status_code))
    logging.info('[{0}_topology_handler][response data] {1}'.
          format(route_name, post_call.text))

    return post_call


def init_topology(worker_host_ip,
                  worker_port,
                  controller_ip_address,
                  controller_of_port,
                  switch_type,
                  topo_type,
                  topo_size,
                  group_size,
                  group_delay,
                  hosts_per_switch,
                  dpid_offset):
    """Initialize a Multinet topology
    Make a POST request at the 'init' endpoint of a worker

    Args:
      worker_host_ip (str): The IP address of the worker
      worker_port (int): The port of the worker
      controller_ip_address (str): The IP address of the controller
      controller_of_port (int): The OpenFlow port of the controller
      switch_type (str): The type of soft switch to use for the emulation
      topo_type (str): The type of the topology we want to build
      topo_size (int): The size of the topology we want to build
      group_size (int): The number of switches in a gorup for gradual bootup
      group_delay (int): The delay between the bootup of each group
      hosts_per_switch (int): The number of hosts connected to each switch
      dpid_offset (int): The dpid offset of this worker

    Returns:
      requests.models.Response: The HTTP response for the performed request
    """
    route = (
        'init/controller/{0}/port/'
        '{1}/switch/{2}/topology/{3}/size/{4}/group/{5}/delay/{6}/hosts/{7}/dpid/{8}'.
        format(
            controller_ip_address,
            controller_of_port,
            switch_type,
            topo_type,
            topo_size,
            group_size,
            group_delay,
            hosts_per_switch,
            dpid_offset))

    return make_post_request(worker_host_ip, worker_port, route)


def make_post_request_runner(host_ip, host_port, route, data, queue):
    """Wrapper function to create a new job for each POST request.
    Make a POST request and put the response in a queue.
    Used for multiprocessing.

    Args:
      host_ip (str): The IP address of the REST server
      host_port (int): The port of the REST server
      route (str): The REST API endpoint
      data (str): Any additional JSON data
      queue (multiprocessing.Queue): The queue where all the responses are stored
    """
    queue.put(make_post_request(host_ip, host_port, route, data))


def init_topology_runner(worker_host_ip,
                         worker_port,
                         controller_ip_address,
                         controller_of_port,
                         switch_type,
                         topo_type,
                         topo_size,
                         group_size,
                         group_delay,
                         hosts_per_switch,
                         dpid_offset,
                         queue):
    """Wrapper function to create a new job for each init POST request
    Make an init POST request and put the response in a queue.
    Used for multiprocessing.

    Args:
      worker_host_ip (str): The IP address of the worker
      worker_port (int): The port of the worker
      controller_ip_address (str): The IP address of the controller
      controller_of_port (int): The OpenFlow port of the controller
      switch_type (str): The type of soft switch to use for the emulation
      topo_type (str): The type of the topology we want to build
      topo_size (int): The size of the topology we want to build
      group_size (int): The number of switches in a gorup for gradual bootup
      group_delay (int): The delay between the bootup of each group
      hosts_per_switch (int): The number of hosts connected to each switch
      dpid_offset (int): The dpid offset of this worker
      queue (multiprocessing.Queue): The queue where all the responses are stored
    """
    queue.put(init_topology(worker_host_ip,
                            worker_port,
                            controller_ip_address,
                            controller_of_port,
                            switch_type,
                            topo_type,
                            topo_size,
                            group_size,
                            group_delay,
                            hosts_per_switch,
                            dpid_offset))



def handle_post_request(post_call, exit_on_fail=True):
    """Handle the response of a REST request
    If the status code is not successful and the caller specifies so, sys.exit
    Else log the response text

    Args:
      post_call (requests.models.Response): The response to handle
      exit_on_fail (Optional[bool]): True -> Exit on error status code / False -> continue
    """
    failed_post_call = post_call.status_code >= 300 or post_call.status < 200
    if failed_post_call and exit_on_fail:
        sys.exit(post_call.status_code)
    else:
        logging.debug(post_call.text)


def broadcast_init(worker_ip_list,
                   worker_port,
                   controller_ip_address,
                   controller_of_port,
                   switch_type,
                   topo_type,
                   topo_size,
                   group_size,
                   group_delay,
                   hosts_per_switch):
    """Broadcast an init POST request to all the workers
    Use multiple processes to send POST requests to the 'init' 
    endpoint of all the workers simultaneously.
    The dpid offset is infered automatically 
    
    Args:
      worker_ip_list (list): A list of IP addresses to broadcast the POST request
      worker_port (int): The port of the workers
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
    dpid_offset_list = dpid_offset_range(len(worker_ip_list))
    offset_idx = 0
    processes = []
    result_queue = multiprocessing.Queue()

    for worker_host_ip in worker_ip_list:
        dpid_offset = dpid_offset_list[offset_idx]
        offset_idx += 1
        process = multiprocessing.Process(target=init_topology_runner,
                                          args=(worker_host_ip,
                                                worker_port,
                                                controller_ip_address,
                                                controller_of_port,
                                                switch_type,
                                                topo_type,
                                                topo_size,
                                                group_size,
                                                group_delay,
                                                hosts_per_switch,
                                                dpid_offset,
                                                result_queue,))
        process.start()
        processes.append(process)

    for process in processes:
        process.join()
        time.sleep(1)

    return [result_queue.get() for _ in processes]


def broadcast_cmd(worker_ip_list, worker_port, opcode):
    """Broadcast a POST request to all the workers
    Use multiple processes to send POST requests to a specified
    endpoint of all the workers simultaneously.

    Args:
      worker_ip_list (list): A list of IP addresses to broadcast the POST request
      worker_port (int): The port of the workers
      opcode (str): The REST API endpoint

    Returns:
      list: A list of responses for all the POST requests performed
    """
    processes = []
    result_queue = multiprocessing.Queue()

    for worker_ip in worker_ip_list:
        data = None
        process = multiprocessing.Process(target=make_post_request_runner,
                                          args=(worker_ip,
                                                worker_port,
                                                opcode,
                                                data,
                                                result_queue,))
        processes.append(process)
        process.start()
        time.sleep(1)

    for process in processes:
        process.join()

    return [result_queue.get() for _ in processes]


def aggregate_broadcast_response(responses):
    """Perform an aggregation on a list of HTTP responses
    If all the responses status code is successful return 200 else return 500
    Gather all the responses text in a list

    Args:
      responses (list): A list of HTTP responses

    Returns:
      status (int): The aggregate status code
      body (list): The list of all the responses text 
    """
    status = 200 if all(
        r.status_code >= 200 and r.status_code < 300 for r in responses) else 500
    body = json.dumps([r.text for r in responses])
    return status, body


def master_init(master_ip,
                master_port,
                controller_ip_address,
                controller_of_port,
                switch_type,
                topo_type,
                topo_size,
                group_size,
                group_delay,
                hosts_per_switch):
    """Wrapper function to make an init POST request to the master

    Args:
      master_ip (str): The IP address of the master
      master_port (int): The port of the master
      controller_ip_address (str): The IP address of the controller
      controller_of_port (int): The OpenFlow port of the controller
      switch_type (str): The type of soft switch to use for the emulation
      topo_type (str): The type of the topology we want to build
      topo_size (int): The size of the topology we want to build
      group_size (int): The number of switches in a gorup for gradual bootup
      group_delay (int): The delay between the bootup of each group
      hosts_per_switch (int): The number of hosts connected to each switch

    Returns:
      requests.models.Response: The HTTP response for the performed request
    """
    route = (
        'init/controller/{0}/port/'
        '{1}/switch/{2}/topology/{3}/size/{4}/group/{5}/delay/{6}/hosts/{7}'. format(
            controller_ip_address,
            controller_of_port,
            switch_type,
            topo_type,
            topo_size,
            group_size,
            group_delay,
            hosts_per_switch))

    return make_post_request(master_ip, master_port, route)


def master_cmd(master_ip, master_port, opcode):
    """Wrapper function to send a command to the master

    Args:
      master_ip (str): The IP address of the master
      master_port (int): The port of the master
      opcode (str): The REST API endpoint (the command we want to send)
 
    Returns:
      requests.models.Response: The HTTP response for the performed request
    """
    return make_post_request(master_ip, master_port, opcode)
