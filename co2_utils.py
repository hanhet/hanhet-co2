import hmac
import hashlib
import random
import socket
#import utils

def get_unused_port(start_port, end_port):
    count = end_port - start_port
    while count > 1 :
        service_port = random.randint(start_port, end_port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', service_port))
        if result <> 0: # Available
            sock.close()
            return service_port
        count = count - 1
    return -1

# Generate device id
def generate_device_id(key):
    nicId = 'dummy' #utils.getHwAddr()+utils.getAddress('adr')
    hashId = hmac.new(key, nicId, hashlib.sha1)
    deviceId = hashId.hexdigest()
    return deviceId

def select_edge(method, edge_cap, device_req):
    return method(edge_cap, device_req)

def max_cpu(edge_cap, device_req):
    if len(edge_cap) == 1:
        for edge in edge_cap:
            if edge_cap[edge]['cpu']['remaincpu'] > device_req['cpu']['mincpu']:
                return 200, edge
            else:
                return 100, 'qualied edge not found'
	else:    
		max_edge = None
		for edge in edge_cap:
			if max_edge is None:
				max_edge = edge
				continue
			if edge_cap[edge]['cpu']['remaincpu'] > edge_cap[max_edge]['cpu']['remaincpu']:
				max_edge = edge
				print edge_cap[max_edge]['cpu']['remaincpu']

        if edge_cap[max_edge]['cpu']['remaincpu'] > device_req['cpu']['mincpu']:
            return 200, max_edge
        else:
            return 100, 'qualied edge not found'