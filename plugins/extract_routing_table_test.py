
import core.message as message
from core.node import Node
import core.ptime as time


STATUS_OK = 'OK'                 # pinged and give response
STATUS_TIMEOUT = 'TIMEOUT'       # pinged but fail to response
STATUS_ERROR = 'ERROR'
STATUS_ON_PROCESS = 'ON_PROCESS' # to be extracting
STATUS_COMPLETED = 'COMPLETED' 

NUM_REPETITIONS = 5


class ExperimentalManager:
    def __init__(self, my_id, msg_f):
        self._node_to_extract = None
        self.my_id = my_id
        self.msg_f = msg_f
        
        
        self._send_query = True
        
    def on_query_received(self, msg):
        find_msgs = []
        exp_obj = ExpObj()
        
        if self._send_query:
            # We only want to extract from ONE node
            self._send_query = False 
            print 'Got query (%s) from  Node  %r ' % (
                            msg.query ,  msg.src_node)
            if msg.src_node not in exp_obj.known_nodes:
                # keep the node in a set called known_nodes 
                #if it is not known before
                exp_obj.known_nodes.add(msg.src_node)
                #1 save the node for extraction
                self.add_to_extract(msg.src_node,exp_obj)
                
                #pop a node and keep it in extracting_queue
                poped_node = exp_obj.to_extract_queue.pop()
                #2
                self.add_to_extracting(poped_node,exp_obj)
                find_msgs.extend(self.continue_extraction(msg,exp_obj))
                
            else:
                 print "Already known node" 
        return  find_msgs
    
    def continue_extraction(self,msg,exp_obj): 
        _to_extract_msgs = []
        print "continue_extracting for node %r " % msg.src_node.ip
        log_distance = exp_obj.next_log_dist() 
        target = msg.src_node.id.generate_close_id(log_distance)
        _node_to_ext = exp_obj.extracting_queue.pop()
        # command for extraction
        _to_extract_msgs.append(self.msg_f.outgoing_find_node_query(
                                                    _node_to_ext,
                                                    target, None,
                                                    exp_obj))
        return _to_extract_msgs
    
    def continue_ping(self,node_,exp_obj):
        ping_msgs = []
        print 'pinging'
        ping_msgs.append(self.msg_f.outgoing_ping_query(node_,
                                                            exp_obj))
        #print node_ 
        return ping_msgs
    
    def on_response_received(self, msg, related_query):
        msgs_to_send = []
        exp_obj = related_query.experimental_obj
        if not exp_obj:
            return
        else:
            msgs_to_send.extend(self.does_on_response(msg,exp_obj,
                                                      related_query))
        return msgs_to_send
    
    def does_on_response(self, msg, exp_obj,related_query):
        on_response_msg = []
        ping_msgs = []
        if related_query.query == message.PING:
            exp_obj.reg_status_of_node(msg.src_node, STATUS_OK)
            
        elif related_query.query == message.FIND_NODE:
            # keep the node in a set called known_nodes 
            #if it is not known before
            for node_ in msg.nodes:
                exp_obj.known_nodes.add(node_)
                print "node %r" % node_.ip
                #3
                self.add_to_pinging_queue(node_,exp_obj)
                ping_msgs.extend(self.continue_ping(node_,exp_obj))  
            
        exp_obj.print_nodes()    
        return on_response_msg + ping_msgs
    
    def on_timeout(self, related_query):
        exp_obj = related_query.experimental_obj
        if exp_obj:
            print 'Time out', related_query.query
            if related_query.query == message.PING:
                exp_obj.reg_status_of_node(
                                        related_query.dst_node, 
                                        STATUS_TIMEOUT)
            exp_obj.print_nodes()
    
    def add_to_extract(self,node_,exp_obj): 
        exp_obj.save_node_in_to_extract_queue(node_)
        
    def add_to_extracting(self,node_,exp_obj):
        exp_obj.save_node_in_extracting_queue(node_)
    
    def add_to_pinging_queue(self,node_,exp_obj):
        exp_obj.save_node_in_pinging_queue(node_)
        
    def add_to_pinged(self,node_,exp_obj):
        exp_obj.save_node_in_pinged_queue(node_) 
    
    def on_error_received(self, msg, related_query):
        return
    
    def on_stop(self):
        return
    
class ExpObj:
    def __init__(self):
        
        # Data Structures to store nodes at different phases
        self.to_extract_queue = []      #Node to be extract
        self.extracting_queue = []      #Node which are extracting      
        self.pinging_queue = []         #Node which are pinging
         
        self.known_nodes = set()
        self.node_status = {}            ##Node , that are pinged saved with their status
        
        
        self.all_ids = set()
        
        self.all_ids = set()
        self.current_log_dist = 160
        
    def save_node_in_to_extract_queue(self,node_):
        self.to_extract_queue.append(node_)
        print 'Node is In.....to_extract_queue ' , node_.ip
        
    
    def save_node_in_extracting_queue(self,node_):
        self.extracting_queue.append(node_)
        print 'Node is In.....to_extracting_queue ' , node_.ip
        
    
    def save_node_in_pinging_queue(self,node_):
        self.pinging_queue.append(node_)
        print 'Node is In.....pinging_queue ' , node_.ip
        
    
    def save_node_in_pinged_queue(self,node_):
        self.pinged_queue.append(node_)
        print 'Node is In.....pinged_queue ' , node_.ip
        
    def next_log_dist(self):
        self.current_log_dist -= 1
        return self.current_log_dist
        
    def save_bucket(self, log_distance_bucket, nodes): 
        
        self.extracted_nodes.append((log_distance_bucket, nodes))  
        for node_ in nodes:
            self.all_ids.add(node_.id)  
            
    def reg_status_of_node(self, node_, status):
        self.node_status[node_] = status
        print"jjjjjjjjjj"
        
    def print_nodes(self):
        total = {}
        total[STATUS_OK] = 0
        total[STATUS_TIMEOUT] = 0
        total[STATUS_ERROR] = 0
        '''
        total[STATUS_ON_PROCESS] = 0
        total[STATUS_COMPLETED] = 0'
        
        for logdist, nodes in self.extracted_nodes:
            print '\nLog Distance = ', logdist'''
        for node_ in self.pinging_queue:
            total[self.node_status[node_]] += 1
            print self.node_status.get(node_)
        print '\nTotal OK/TIMEOUT/ERROR'
        print total

        
        
