import sys
import json
import paho.mqtt.client as mqtt
import base64
from alog import Level, Log
import co2_utils

reload(sys)
sys.setdefaultencoding('utf-8')

# Print debug message if set as True
Log.level = Level.v

# Generate service id
key = 'signature is unique for device'
deviceId = co2_utils.generate_device_id(key)
edgeId = ''

# MQTT Configuration
mediatorClient = None
mediatorClientId = "mediator"
mediatorUsername = ""
mediatorPassword = ""
mediatorBroker = "iot.eclipse.org"
edgeClient = None
edgeClientId = "edge"
edgeUsername = ""
edgePassword = ""
edgeBroker = ''#"iot.eclipse.org"
mqttLoop = True

# Container-based On-demand Computation Offloading (CO2)
prefix = 'ucan/co2'
topic_sch_req = prefix + '/search/request'
topic_sch_rep = prefix + '/search/response/' + deviceId
topic_off_req = ''
topic_off_req_base = prefix + '/offloading/request/'
topic_off_rep = prefix + '/offloading/response/' + deviceId
compose_file = 'example.yml' # TODO: This should be given by user.

fp = open(compose_file,'rb')
byte = fp.read()
fp.close()
message = base64.b64encode(byte)
data = {"client_id":deviceId,"req":message}
message2 = json.dumps(data)
#print message

def on_e_message(client, userdata, msg):
   Log.v('on_e_message', 'topic: {}'.format(msg.topic))
   Log.v('on_e_message', 'payload: {}'.format(msg.payload))
   edgeClient.disconnect()
   edgeClient.loop_stop()

def on_e_subscribe(client, userdata, mid, qos):
   Log.v('on_e_subscribe', 'Subscribed {} with QoS ({})'.format(topic_off_rep, qos[0]))
   topic_off_req = topic_off_req_base + edgeId
   client.publish(topic_off_req, message2, qos = 2)

def on_e_connect(client, userdata, flag, rc):
   if rc == 0:
      Log.i('on_e_connect', 'Edge broker connected ...')
      client.subscribe(topic_off_rep, 2)
   else:
      Log.e('on_e_connect', 'Connection refused with rc ({}).'.format(rc))
      Log.e('on_e_connect', 'Stop connecting edge broker ...')
      client.loop_stop()

def on_m_message(client, userdata, msg):
   global topic_off_req, edgeClient, edgeBroker, edgeId
   Log.v('on_m_message', 'topic: {}'.format(msg.topic))
   Log.v('on_m_message', 'payload: {}'.format(msg.payload))
   js = json.loads(msg.payload)
   edgeId = str(js['client_id'])
   edgeBroker = str(js['broker']['ip'])
   topic_off_req = topic_off_req_base + edgeId
   edgeClient.connect(edgeBroker)
   edgeClient.loop_start()

def on_m_publish(client, userdata, result):
   Log.v('on_m_publish', 'pub ok')

def generate_search_payload():
   mem = None
   disk = None
   inputnum = input("Chioce a case: ")
   if inputnum==1:
      mem = "200"
      disk = "250"
      requestdata = {"client_id":deviceId,"cpu":{"mincpu":10},"memory":{"minmem":mem},"disk":{"mindisk":disk}}
   if inputnum==2:
      requestdata = {"client_id":deviceId}
   payload = json.dumps(requestdata)
   return payload

def on_m_subscribe(client, userdata, mid, qos):
   Log.v('on_m_subscribe', 'Subscribed {} with QoS ({})'.format(topic_sch_rep, qos[0]))
   client.publish(topic_sch_req, generate_search_payload(), qos = 2)

def on_m_connect(client, userdata, flag, rc):
   if rc == 0:
      Log.i('on_m_connect', 'Mediator broker connected ...')
      client.subscribe(topic_sch_rep, 2)
   else:
      Log.e('on_m_connect', 'Connection refused with rc ({}).'.format(rc))
      Log.e('on_m_connect', 'Shutting down device')
      client.loop_stop()
      exit()

def start_device():
   global mediatorClient, edgeClient, mqttLoop
   Log.v('start_device', 'Starting device on {} ...'.format(sys.platform))

   Log.v('start_device', 'Connecting to mediator broker: {}'.format(mediatorBroker))
   mediatorClient = mqtt.Client(client_id = mediatorClientId + deviceId)
   mediatorClient.username_pw_set(mediatorUsername, mediatorPassword)
   mediatorClient.on_connect = on_m_connect
   mediatorClient.on_message = on_m_message
   mediatorClient.on_subscribe = on_m_subscribe
   mediatorClient.on_publish = on_m_publish
   mediatorClient.connect(mediatorBroker)
   mediatorClient.loop_start()

   edgeClient = mqtt.Client(client_id = edgeClientId + deviceId)
   edgeClient.username_pw_set(edgeUsername, edgePassword)
   edgeClient.on_connect = on_e_connect
   edgeClient.on_message = on_e_message
   edgeClient.on_subscribe = on_e_subscribe

   mqttLoop = True
   try:
		while mqttLoop:
			pass
   except KeyboardInterrupt:
	   print('Device stopped with Ctrl + C ...')
	   exit()

start_device()