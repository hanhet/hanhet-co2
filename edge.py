import sys, os 
import json
import base64 
import paho.mqtt.client as mqtt
import subprocess
import datetime
from alog import Level, Log
import co2_utils
import resourceUtils

# Configuration
mediatorClientId = "mediator"
mediatorUsername = ""
mediatorPassword = ""
mediatorBroker = "iot.eclipse.org"
mediatorPort = 1883
edgeClientId = "edge"
edgeUsername = ""
edgePassword = ""
edgeBroker = "iot.eclipse.org"
edgePort = 1883
# Set log level (e, w, i, v) as required
Log.level = Level.v
# Range of Service Ports
start_port = 1000
end_port = 9000

# DO NOT modify the following code
reload(sys) 
sys.setdefaultencoding('utf-8')

# Generate device id
key = 'signature is unique'
deviceId = co2_utils.generate_device_id(key)

# MQTT Configuration
mediatorClient = None
edgeClient = None
loop = True

portTable = {}

# Container-based On-demand Computation Offloading (CO2)
prefix = 'ucan/co2/'
topic_reg_req = prefix + 'register/request'
topic_reg_rep = prefix + 'register/response/' + deviceId
topic_off_req = prefix + 'offloading/request/' + deviceId
topic_off_rep = ''
topic_off_rep_base = prefix + 'offloading/response/'

def on_e_message(client, userdata, msg):
   # TODO: Ugly Code
   request = json.loads(msg.payload)
   deviceId = request['client_id']
   compose_content_base64 = request['req']
   compose_file_content = base64.b64decode(compose_content_base64)

   # Port handling
   port_count = compose_file_content.count('<vport')
   for i in range(port_count):
      service_port = co2_utils.get_unused_port(start_port, end_port)
      compose_file_content = compose_file_content.replace('<vport{}>'.format(str(i)), str(service_port))

   print compose_file_content

   portTable[deviceId] = {}
   portTable[deviceId]['port'] = service_port
   
   compose_file = '{}.yml'.format(deviceId)
   fp = open(compose_file, 'w')
   fp.write(compose_file_content)
   fp.close()
     
   # TODO: How to run docker-compose without subprocess (rapydo-controller)
   try:
      subprocess.call('sudo docker-compose -f {} up -d'.format(compose_file), shell=True)
      payload = json.dumps({"code":200, "service_ports":service_port})      
   except:
      payload = json.dumps({"code":100, "message":"service construction failed"})
  
   # Sending offloading response
   os.remove(compose_file)
   topic_off_rep = topic_off_rep_base + deviceId
   client.publish(topic_off_rep, payload, qos = 2, retain = False) 

def on_m_message(client, userdate, msg):
   Log.v('on_m_message', 'Sub topic: {}'.format(msg.topic))
   Log.v('on_m_message', 'Sub payload: {}'.format(msg.payload))

def on_e_subscribe(client, userdata, mid, qos):
   Log.v('on_e_subscribe', 'Subscribed {} with QoS ({})'.format(topic_off_req, qos[0]))

def generate_register_payload():
   global deviceId, edgeBroker
   cpu = resourceUtils.get_cpu_time()
   total_mem = resourceUtils.get_total_memory()
   free_mem = resourceUtils.get_free_memory()
   total_disk = resourceUtils.get_total_disk()
   free_disk = resourceUtils.get_free_disk()

   data = {"client_id":deviceId,"broker":{"ip":edgeBroker,"port":edgePort},"cpu":{"remaincpu":cpu},"memory":{"totalmem":total_mem,"remainmem":free_mem},"disk":{"totaldisk":total_disk,"remaindisk":free_disk}}
   payload = json.dumps(data)
   return payload

def on_m_subscribe(client, userdata, mid, qos):
   Log.v('on_m_subscribe', 'Subscribed {} with QoS ({})'.format(topic_reg_rep, qos[0]))
   client.publish(topic_reg_req, generate_register_payload(), qos = 2)

def on_e_connect(client, userdata, flags, rc):
   if rc == 0:
		Log.i('on_e_connect', 'Edge broker connected ...')
		client.subscribe(topic_off_req, 2)
   else:
      Log.e('on_e_connect', 'Connection refused with rc ({}).'.format(rc))
      Log.e('on_e_connect', 'Shutting down edge')
      exit()

def on_m_connect(client, userdate, flags, rc):
   if rc == 0:
      Log.i('on_m_connect', 'Mediator broker connected ...')
      client.subscribe(topic_reg_rep, 2)
   else:
      Log.e('on_m_connect', 'Connection refused with rc ({}).'.format(rc))
      Log.e('on_m_connect', 'Shutting down edge')
      client.loop_stop()
      exit()

def start_edge():
   global mediatorClient, edgeClient, loop
   Log.v('start_edge', 'Starting edge on {} ...'.format(sys.platform))

   Log.v('start_edge', 'Connecting mediator broker: {}:{}'.format(mediatorBroker, mediatorPort))
   mediatorClient = mqtt.Client(client_id = mediatorClientId + deviceId)
   mediatorClient.username_pw_set(mediatorUsername, mediatorPassword)
   mediatorClient.on_connect = on_m_connect
   mediatorClient.on_message = on_m_message
   mediatorClient.on_subscribe = on_m_subscribe
   mediatorClient.connect(mediatorBroker, mediatorPort)
   mediatorClient.loop_start()

   Log.v('start_edge', 'Connecting edge broker: {}:{}'.format(edgeBroker, edgePort))
   edgeClient = mqtt.Client(client_id = edgeClientId + deviceId)
   edgeClient.username_pw_set(edgeUsername, edgePassword)
   edgeClient.on_connect = on_e_connect
   edgeClient.on_message = on_e_message
   edgeClient.on_subscribe = on_e_subscribe 
   edgeClient.connect(edgeBroker, edgePort)
   edgeClient.loop_start()

   loop = True
   try:
		while loop:
			pass
   except KeyboardInterrupt:
	   print('Edge stopped with Ctrl + C ...')
	   exit()

start_edge()