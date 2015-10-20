#!/usr/bin/env python

import json
import util.multinet_requests as m_util

@pytest.fixture
def config():
    data = {}
    with open('test-config.json') as test_config:
        data = json.load(test_config)
    return data


def test_init(config):
    res = m_util.master_cmd(conf['master_ip'],
                            conf['master_port'],
                            'init',
                            config['topo'])
    assert res.status_code == 200

def test_start(config):
    res = m_util.master_cmd(config['master_ip'],
                            config['master_port'],
                            'start')
    assert res.status_code == 200

def test_get_switches(config):
    res = m_util.master_cmd(conf['master_ip'],
                            conf['master_port'],
                            'get_switches')
    assert res.status_code == 200
    
    res_json = json.loads(res.text)
    for d in res.json:
        for _, v in d:
            assert int(v) == int(config['topo_size'])

def test_stop(config):
    res = m_util.master_cmd(config['master_ip'],
                            config['master_port'],
                            'stop')
    assert res.status_code == 200




   
    
    
