import requests
import sys
import multiprocessing
import json
import time
import logging


logging.getLogger().setLevel(logging.DEBUG)

def ip_range(start_ip, num_ips):
    '''
    Generate a number of consecutive ips
    Assume the ip range fits in one subnet
    '''
    ip_split = start_ip.split('.')
    ip_pref, ip_suf = ip_split[:-1], int(ip_split[-1])
    return ['.'.join(ip_pref + [str(ip_suf + i)]) for i in xrange(0, num_ips)]


def dpid_offset_range(num_vms):
    return [1000 * i + 1 for i in xrange(0, num_vms)]


def init_topology(mininet_rest_host,
                  mininet_rest_port,
                  controller_ip_address,
                  controller_of_port,
                  mininet_switch_name,
                  mininet_topo_type,
                  mininet_topo_size,
                  mininet_group_size,
                  mininet_group_delay,
                  mininet_hosts_per_switch,
                  dpid_offset):
    route = (
        'init/controller/{0}/port/'
        '{1}/switch/{2}/topology/{3}/size/{4}/group/{5}/delay/{6}/hosts/{7}/dpid/{8}'.
        format(
            controller_ip_address,
            controller_of_port,
            mininet_switch_name,
            mininet_topo_type,
            mininet_topo_size,
            mininet_group_size,
            mininet_group_delay,
            mininet_hosts_per_switch,
            dpid_offset))

    return make_post_request(mininet_rest_host,
                             mininet_rest_port,
                             route)


def make_post_request_runner(host_ip,
                             host_port,
                             route,
                             data,
                             queue):

    queue.put(make_post_request(host_ip,
                                host_port,
                                route,
                                data))


def init_topology_runner(mininet_rest_host,
                         mininet_rest_port,
                         controller_ip_address,
                         controller_of_port,
                         switch_type,
                         mininet_topo_type,
                         mininet_topo_size,
                         mininet_group_size,
                         mininet_group_delay,
                         mininet_hosts_per_switch,
                         dpid_offset,
                         queue):

    queue.put(init_topology(mininet_rest_host,
                            mininet_rest_port,
                            controller_ip_address,
                            controller_of_port,
                            switch_type,
                            mininet_topo_type,
                            mininet_topo_size,
                            mininet_group_size,
                            mininet_group_delay,
                            mininet_hosts_per_switch,
                            dpid_offset))


def make_post_request(host_ip,
                      host_port,
                      route,
                      data=None):

    session = requests.Session()
    session.trust_env = False

    url = 'http://{0}:{1}/{2}'.format(host_ip, host_port, route)
    route_name = route.split('/')[0]
    logging.info('[{0}_topology_handler][url] {1}'.format(route_name, url))
    if data is None:
        mininet_post_call = session.post(url)
    else:
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        mininet_post_call = requests.post(
            url,
            data=json.dumps(data),
            headers=headers)
    logging.info('[{0}_topology_handler][response status code] {1}'.
          format(route_name, mininet_post_call.status_code))
    logging.info('[{0}_topology_handler][response data] {1}'.
          format(route_name, mininet_post_call.text))

    return mininet_post_call


def handle_post_request(mininet_post_call, exit_on_fail=True):
    if mininet_post_call.status_code != 200:
        if exit_on_fail:
            sys.exit(mininet_post_call.status_code)
        else:
            logging.debug(mininet_post_call.text)


def broadcast_init(mininet_rest_hosts,
                   mininet_rest_port,
                   controller_ip_address,
                   controller_of_port,
                   switch_type,
                   mininet_topo_type,
                   mininet_topo_size,
                   mininet_group_size,
                   mininet_group_delay,
                   mininet_hosts_per_switch):

    dpid_offset_list = dpid_offset_range(len(mininet_rest_hosts))
    offset_idx = 0
    processes = []
    result_queue = multiprocessing.Queue()

    for mininet_rest_host in mininet_rest_hosts:
        dpid_offset = dpid_offset_list[offset_idx]
        offset_idx += 1
        process = multiprocessing.Process(target=init_topology_runner,
                                          args=(mininet_rest_host,
                                                mininet_rest_port,
                                                controller_ip_address,
                                                controller_of_port,
                                                switch_type,
                                                mininet_topo_type,
                                                mininet_topo_size,
                                                mininet_group_size,
                                                mininet_group_delay,
                                                mininet_hosts_per_switch,
                                                dpid_offset,
                                                result_queue,))
        process.start()
        processes.append(process)

    for process in processes:
        process.join()
        time.sleep(1)

    return [result_queue.get() for _ in processes]


def broadcast_cmd(mininet_hosts,
                  mininet_port,
                  opcode):

    processes = []
    result_queue = multiprocessing.Queue()

    for mininet_ip in mininet_hosts:
        data = None
        process = multiprocessing.Process(target=make_post_request_runner,
                                          args=(mininet_ip,
                                                mininet_port,
                                                opcode,
                                                data,
                                                result_queue,))
        processes.append(process)
        process.start()
        time.sleep(1)

    for process in processes:
        process.join()

    return [result_queue.get() for _ in processes]


def aggregate_broadcast_response(reqs):
    status = 200 if all(
        r.status_code >= 200 and r.status_code < 300 for r in reqs) else 500
    body = json.dumps([r.text for r in reqs])
    return status, body


def master_init(master_host,
                master_port,
                ip_list,
                controller_ip_address,
                controller_of_port,
                switch_type,
                mininet_topo_type,
                mininet_topo_size,
                mininet_group_size,
                mininet_group_delay,
                mininet_hosts_per_switch):

    route = (
        'init/controller/{0}/port/'
        '{1}/switch/{2}/topology/{3}/size/{4}/group/{5}/delay/{6}/hosts/{7}'. format(
            controller_ip_address,
            controller_of_port,
            switch_type,
            mininet_topo_type,
            mininet_topo_size,
            mininet_group_size,
            mininet_group_delay,
            mininet_hosts_per_switch))

    return make_post_request(master_host,
                             master_port,
                             route,
                             data=ip_list)


def master_cmd(master_host,
               master_port,
               opcode,
               ip_list):

    return make_post_request(master_host,
                             master_port,
                             opcode,
                             data=ip_list)
