# Copyright (C) 2009-2011 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information


"""
FORMAT
The first line contains this node's identifier

The rest of the lines contain routing table nodes
log_distance hex_id ip port rtt

EXAMPLE
008b9c909a072b8745703736e4c835925e323742
136 008b9df33988efc53a140eadd478bd15b4f27916 72.91.157.171 21294 84.053993
138 008b9bab35e106b40077877c74b454f314e2293b 39.272.248.7 33079 140.555859

"""

import sys
import logging

from identifier import Id
from node import Node

logger = logging.getLogger('dht')


def save(my_id, rnodes, filename):
    f = open(filename, 'w')
    f.write('%r\n' % my_id)
    for rnode in rnodes:
        f.write('%d %r %s %d %f\n' % (
                my_id.log_distance(rnode.id),
                rnode.id, rnode.addr[0], rnode.addr[1],
                rnode.rtt * 1000))
    f.close()

def load(filename):
    my_id = None
    nodes = []
    try:
#        print >>sys.stderr, 'opening', filename
        f = open(filename)
#        print >>sys.stderr, 'OK'
        hex_id = f.readline().strip()
        my_id = Id(hex_id)
#        print >>sys.stderr, 'my id OK'
        for line in f:
#            print >>sys.stderr, 'line', line
            _, hex_id, ip, port, _ = line.split()
            addr = (ip, int(port))
            node_ = Node(addr, Id(hex_id))
            nodes.append(node_)
    except(IOError):
        logger.debug("No state saved, loading default.")
        return None, []
    except:
        logger.exception("Error when loading state, loading default.")
        raise
        return None, []
    f.close
    return my_id, nodes
        
