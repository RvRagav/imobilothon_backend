# mqtt_sub.py
import time
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC = "hazards/alerts/pothole"

def on_connect(client, userdata, flags, rc):
    print("connected rc=", rc)
    if rc == 0:
        client.subscribe(TOPIC)
        print("subscribed to", TOPIC)

def on_message(client, userdata, msg):
    print("RECEIVED:", msg.topic, msg.payload.decode())

c = mqtt.Client(client_id="live-subscriber")
c.on_connect = on_connect
c.on_message = on_message
c.on_log = lambda client, userdata, level, buf: print("MQTT log:", buf)

c.connect(BROKER, PORT, keepalive=60)
c.loop_start()
try:
    # keep running until you CTRL+C
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping subscriber")
finally:
    c.loop_stop()
    c.disconnect()