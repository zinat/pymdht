import csv

import core.message as message
from core.node import Node
import core.ptime as time


STATUS_OK = 'OK'                 # pinged and give response
STATUS_TIMEOUT = 'TIMEOUT'       # pinged but fail to response
STATUS_ERROR = 'ERROR'
STATUS_PINGING = 'PINGING'

NO_VERSION = '_'

NUM_REPETITIONS = 5

MAX_PARALLEL_EXTRACT = 2

TIMEOUT = 2



class ExtractingTable(object):

    def __init__(self, node_):
        self.node = node_
        self._next_extracting_level = 159
        self._num_repetitions = 0
        self._levels = []
        self.last_fn_query_ts = 0


    def add_pnodes(self, pnodes):
        self._levels.append(pnodes)
        if len(self._levels) < 2:
            return
        for new_pnode in pnodes:
            for seen_pnode in self._levels[-2]:
                if new_pnode == seen_pnode:
                    self._num_repetitions += 1
                    break
                
    def next_level(self):
        if self._num_repetitions >= NUM_REPETITIONS:
            return
        level = self._next_extracting_level
        self._next_extracting_level -= 1
        self.last_fn_query_ts = time.time()
        return level

    def _write(self, csv_file):
        csv_file.writerow('table')
        for level in self._levels:
            csv_file.writerow('level')
            for pnode in level:
                csv_file.writerow(pnode.get_csv())
            csv_file.writerow('elevel')

        csv_file.writerow('etable')
            

class PingedNode(object):

    def __init__(self, node_):
        self.node = node_
        self.rtt = 0
        self.version = NO_VERSION

    def __eq__(self, other):
        # nodes are defined per IP address alone!!!
        return self.node.addr[0] == other.node.addr[0]

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return self.node.addr[0]

    def get_csv(self):
        return [self.node.addr[0], str(self.node.addr[1]),
                repr(self.node.id), self.version, str(self.rtt)]

    
class ExtractingQueue(object):
    
    def __init__(self, msg_f):
        self.msg_f = msg_f
        self._to_extract_queue = []      #Node to be extract
        self._extracting_queue = []      #Node which are extracting      
        self._all_extracting_ips = set()
        self._next_snode_to_extract = 0
        self._csv_file = csv.writer(open('exp_extract.csv', 'w'))
        
    def add(self, node_):
        if node_.addr[0] in self._all_extracting_ips:
            return #already sampled
        print 'added'
        self._all_extracting_ips.add(node_.addr[0])
        self._to_extract_queue.append(node_)

    def get_fn_queries(self):
        if self._to_extract_queue and len(
            self._extracting_queue) < MAX_PARALLEL_EXTRACT:
            node_ = self._to_extract_queue.pop(0)
            etable = ExtractingTable(node_)
            self._extracting_queue.append(etable)
        current_etable_index = self._next_snode_to_extract
        etable = self._extracting_queue[self._next_snode_to_extract]
        self._next_snode_to_extract = (self._next_snode_to_extract
                                       + 1) % len(self._extracting_queue)
        level = etable.next_level()
        queries = []
        if level:
            print 'extracting'
            queries.append(
                self.msg_f.outgoing_find_node_query(
                    etable.node, etable.node.id.generate_close_id(level),
                    experimental_obj=etable))
        else:
            print 'extraction done'
            # extraction done
            if etable.last_fn_query_ts > TIMEOUT:
                print 'write'
                # all pings timed out, write to file
                etable._write(self._csv_file)
                del self._extracting_queue[current_etable_index]
        return queries

    
class ExperimentalManager:
    def __init__(self, my_id, msg_f):
        self.extracting_queue = ExtractingQueue(msg_f)
        self.my_id = my_id
        self.msg_f = msg_f
        
    def on_query_received(self, msg):
        self.extracting_queue.add(msg.src_node)
        find_msgs = self.extracting_queue.get_fn_queries()
        return find_msgs

    def on_response_received(self, msg, related_query):
        #self.extracting_queue.add(msg.src_node)
        ping_queries = []
        find_node_queries = []
        exp_obj = related_query.experimental_obj
        if not exp_obj:
            return []

        if related_query.query == message.PING:
            # exp_obj is a PingedNode
            exp_obj.status = related_query.rtt
        elif related_query.query == message.FIND_NODE:
            # exp_obj is a ExtractingTable
            pnodes = [PingedNode(node_) for node_ in msg.nodes]
            exp_obj.add_pnodes(pnodes)
            ping_queries = [self.msg_f.outgoing_ping_query(
                    node_, pnode) for pnode in pnodes]
        return ping_queries + find_node_queries

    def on_timeout(self, related_query):
        print "timeout"
        exp_obj = related_query.experimental_obj
        if not exp_obj:
            return []
        if related_query.query == message.PING:
            exp_obj.status = TIMEOUT
        elif related_query.query == message.FIND_NODE:
            # timeout while extracting: retry?????
            pass
        return []

    def on_error_received(self, msg, related_query):
        exp_obj = related_query.experimental_obj
        if not exp_obj:
            return []
        if related_query.query == message.PING:
            # consider ERROR as TIMEOUT
            exp_obj.status = TIMEOUT
        elif related_query.query == message.FIND_NODE:
            # ERROR while extracting: retry?????
            pass
        return []

    def on_stop(self):
        #TODO: write to file
        
        return

        
        
