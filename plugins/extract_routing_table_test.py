
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
        self.find_msgs = []
        self._send_query = True
        pass
        
    
    def on_query_received(self, msg):
        
        exp_obj = ExpObj()
        msg1 = []
        msgs = []
        if self._send_query:
            # We only want to extract from ONE node
            self._send_query = False 
            print 'Got query (%s) from  Node  %r ' % (
                            msg.query ,  msg.src_node)
            
            if not exp_obj.seen_node(msg.src_node):
                print ' node %r Already seen = %r ' %( msg.src_node , 
                                exp_obj.seen_node(msg.src_node))
                self.add_to_extract(msg.src_node,exp_obj)
                msg1.append(self.continue_extraction(msg,exp_obj) )   
                print 'msg1 ' , msg1
                msgs.append(self.continue_ping())
                print 'msgs ' , msgs
                self.find_msgs = msg1 + msgs
            
            else:
                print " Already in process"   
        return self.find_msgs
    
     
    def add_to_extract(self,node_,exp_obj):    
        print "add_to_extract"
        exp_obj.save_node_in_to_extract_queue(node_)
        
    
    def continue_extraction(self,msg,exp_obj): 
        print "continue_extracting for node %r " % msg.src_node
        
        log_distance = exp_obj.next_log_dist() 
        print 'log_distance %r ' %  log_distance       
        
        target = msg.src_node.id.generate_close_id(log_distance)
        print 'target %r ' %  target
        
        self._node_to_extract = exp_obj.to_extract_queue.pop(0)
        print 'popped %r ' %  self._node_to_extract
        
        # command for extraction
        self.find_msgs.append(self.msg_f.outgoing_find_node_query(
                                                    self._node_to_extract,
                                                    target, None,
                                                    exp_obj))
        print 'msg send for extraction: % r' % self.find_msgs
        
        return self.find_msgs
    
    def continue_ping(self):   
        
        
        pass
    
    def on_response_received(self, msg, related_query):
        msgs_to_send = []
        exp_obj = related_query.experimental_obj
        if not exp_obj:
            pass
        if related_query.query == message.PING:
            print "query % r " % related_query.query
            pass
        elif related_query.query == message.FIND_NODE:
            print 'query % r' % related_query.query
            
        return msgs_to_send
    
    def on_timeout(self, related_query):
        pass
    def on_error_received(self, msg, related_query):
        pass
    
class ExpObj:
    def __init__(self):
        
        # Data Structures to store nodes at different phases
        self.to_extract_queue = []      #Node to be extract
        self.extracting_queue = []      #Node which are extracting      
        self.pinging_queue = []         #Node which are pinging
        self.pinged_queue = []          #Node to that are pinged 
        
        self.all_ids = set()
        self.current_log_dist = 160
        pass
    
    def seen_node(self, node_):
        #The purpose of this function is to check whether the node
        # is already seen or not of this 
        if node_ in self.to_extract_queue:
            return True
        elif node_ in self.extracting_queue:
            return True
        elif node_ in self.pinging_queue:
            return True
        elif node_ in self.pinged_queue:
            return True
        else:
            return False
        pass
    
    def save_node_in_to_extract_queue(self,node_):
        self.to_extract_queue.append(node_)
        print ' Node is In.....to_extract_queue ' , node_.addr
        pass
    
    def save_node_in_extracting_queue(self,node_):
        self.extracting_queue.append(node_)
        print 'Node is In.....to_extracting_queue ' , node_.addr
        pass
    
    def save_node_in_pinging_queue(self,node_):
        self.pinging_queue.append(node_)
        print 'Node is In.....pinging_queue ' , node_.addr
        pass
    
    def save_node_in_pinged_queue(self,node_):
        self.pinged_queue.append(node_)
        print 'Node is In.....pinged_queue ' , node_.addr
        pass
    
    def next_log_dist(self):
        self.current_log_dist -= 1
        return self.current_log_dist
        
    def save_bucket(self, log_distance_bucket, nodes):   
        pass  
    def reg_status_of_node(self, node_, status):
        pass
    def print_nodes(self):
        pass
        
        
