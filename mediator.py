import sys
import json
import paho.mqtt.client as mqtt
from alog import Level, Log
import co2_utils

# Configuration
clientId = "mediator"
username = ""
password = ""
broker = "iot.eclipse.org"
port = 1883
# Set log level (e, w, i, v) as required
Log.level = Level.v

# DO NOT modify the following code
reload(sys)
sys.setdefaultencoding('utf-8')

# MQTT
client = None
loop = True

# Container-based On-demand Computation Offloading (CO2)
prefix = 'ucan/co2/'
topic_reg_req = prefix + 'register/request'
topic_sch_req = prefix + 'search/request'
topic_reg_rep = ''
topic_reg_rep_base = prefix + 'register/response/'
topic_sch_rep = ''
topic_sch_rep_base = prefix + 'search/response/'

# Edge Repository
edge_capability = {}
device_requirement = {}

def reg_handler(msg):
	global topic_reg_rep, topic_reg_rep_base
	global edge_capability

	dict = json.loads(msg.payload) 
	Log.v('reg_handler', dict)

	edgeId = dict['client_id']
	topic_reg_rep = topic_reg_rep_base + edgeId

	if edgeId == None:
		Log.e('reg_handler', 'Request without edge id: ' + dict)
		payload = json.dumps({"code":100,"message":"without edge id"})   
	elif dict.get('disk') == None:
		payload = json.dumps({"code":100,"message":"without disk data"})
	elif dict.get('memory') == None:
		payload = json.dumps({"code":100,"message":"without memory data"})
	elif dict.get('cpu') == None:
		payload = json.dumps({"code":100,"message":"without cpu data"})
	else:
		edge_capability[edgeId] = {}
		edge_capability[edgeId]['broker'] = dict['broker']
		edge_capability[edgeId]['disk'] = dict['disk']
		edge_capability[edgeId]['memory'] = dict['memory']
		edge_capability[edgeId]['cpu'] = dict['cpu']
		payload = json.dumps({"code":200, "message":"success"})

	Log.v('reg_handler', 'Pub topic: {}'.format(topic_reg_rep))
	Log.v('reg_handler', 'Pub payload: {}'.format(payload))
	client.publish(topic_reg_rep, payload, qos = 2, retain = False)

def sch_handler(msg):
	global topic_sch_rep, topic_sch_rep_base
	global edge_capability, device_requirement

	dict = json.loads(msg.payload)
	Log.v('sch_handler', dict)

	deviceId = dict['client_id']
	topic_sch_rep = topic_sch_rep_base + deviceId
	device_requirement['disk'] = dict['disk']
	device_requirement['memory'] = dict['memory']
	device_requirement['cpu'] = dict['cpu']

	code, message = co2_utils.select_edge(co2_utils.max_cpu, edge_capability, device_requirement)
	if code == 200:
		print message
		ip = edge_capability[message]['broker']['ip']
		port = edge_capability[message]['broker']['port']
		payload = json.dumps({"code":200, "client_id":message, "broker":{"ip":ip, "port":port}})
	elif code == 100:
		payload = json.dumps({"code":100, "message":message}) 

	Log.v('sch_handler', 'Pub: {}\n{}'.format(topic_sch_rep, payload))
	client.publish(topic_sch_rep, payload, qos = 2, retain = False)

def on_message(client, userdata, msg):
	rx_topic = msg.topic
	Log.v('on_message', 'topic: {}'.format(rx_topic))
	if rx_topic == topic_reg_req:   # register/request
		reg_handler(msg)
	elif rx_topic == topic_sch_req: # search/request
		sch_handler(msg)
	else:
		Log.w('on_message', 'Unknown topic: {}'.format(rx_topic))

def on_subscribe(client, userdata, mid, qos):
	Log.v('on_subscribe', 'Subscribed {} with QoS ({})'.format(topic_reg_req, qos[0]))
	Log.v('on_subscribe', 'Subscribed {} with QoS ({})'.format(topic_sch_req, qos[1]))

def on_connect(client, userdata, flags, rc):
	if rc == 0:
		Log.i('on_connect', 'Mediator broker connected ...')
		client.subscribe([(topic_reg_req, 2),(topic_sch_req, 2)])
	else:
		Log.e('on_connect', 'Connection refused with rc ({}).'.format(rc))
		Log.e('on_connect', 'Shutting down mediator')
		client.loop_stop()
		exit()

def start_mediator():
	global client, clientId
	global username, password
	global broker, port, loop

	Log.v('start_mediator', 'Starting mediator ...')

	# Connect to mediator broker
	Log.v('start_mediator', 'Connecting mediator broker ...')
	client = mqtt.Client(clientId)
	client.username_pw_set(username, password)
	client.on_connect = on_connect
	client.on_message = on_message
	client.on_subscribe = on_subscribe
	client.connect(broker, port)
	client.loop_start()
	loop = True
	try:
		while loop:
			pass
	except KeyboardInterrupt:
		Log.i('start_mediator', 'Mediator stopped with Ctrl + C ...')
		exit()

start_mediator()