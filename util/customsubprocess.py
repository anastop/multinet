# Copyright (c) 2015 Intracom S.A. Telecom Solutions. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution,
# and is available at http://www.eclipse.org/legal/epl-v10.html

""" Extended subprocess functionality """

import logging
import subprocess


def check_output_streaming(cmd, prefix='', queue=None):
    """ Redirect output to stderr, printing it whenever a new line
    is detected (bufsize=1 denotes line buffered output). This
    can be considered as "realtime" printing.
    Additionally, prints output by prepending it with a user-defined
    prefix. Furthermore, it optionally forwards output to a queue
    in order e.g. to be processed by a separate thread in real-time.

    :param cmd: the command line list.
    :param prefix: the user defined prefix for output.
    :param queue: queue to forward console output to.
    :returns: return exit status of command.
    :raises subprocess.CalledProcessError: If the exit status of the executed
    command is not 0.
    :rtype: str
    :type cmd: list<str>
    :type prefix: str
    :type queue: multiprocessing.Queue
    """

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, bufsize=1,
                            universal_newlines=True)

    for line in iter(proc.stdout.readline, ''):
        if queue is not None:
            queue.put(line)
        logging.debug('{0} {1}'.format(prefix, line.rstrip()))

    proc.wait()
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)
    else:
        return proc.returncode

def blockable_shell(cmd,shell = True,block_shell = False):
    Process = subprocess.Popen('%s' %cmd,stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=shell)
    if block_shell:
        Process.wait()
    return Process.pid
