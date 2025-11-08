# mqtt_test.py (robust)
import time
import sys
import threading
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC = "test/imobilothon"

connected_evt = threading.Event()
received_evt = threading.Event()

def on_connect(client, userdata, flags, rc):
    print(f"on_connect (client={client._client_id}): rc={rc}")
    if rc == 0:
        client.subscribe(TOPIC)
        connected_evt.set()

def on_message(client, userdata, msg):
    print(f"Received: topic={msg.topic} payload={msg.payload.decode()}")
    received_evt.set()

def on_log(client, userdata, level, buf):
    print("MQTT log:", buf)

def run_test():
    c = mqtt.Client(client_id="test-subscriber")
    c.on_connect = on_connect
    c.on_message = on_message
    c.on_log = on_log

    print(f"Connecting subscriber to {BROKER}:{PORT}...")
    c.connect(BROKER, PORT, keepalive=60)
    c.loop_start()

    # wait up to 5s for subscriber to connect
    if not connected_evt.wait(5):
        print("Subscriber did not connect within 5s, aborting.")
        c.loop_stop(); c.disconnect()
        return

    # publisher
    p = mqtt.Client(client_id="test-publisher")
    p.on_log = on_log
    print(f"Connecting publisher to {BROKER}:{PORT}...")
    p.connect(BROKER, PORT, keepalive=60)
    p.loop_start()
    print("Publishing test message...")
    rc, mid = p.publish(TOPIC, "hello-from-host", qos=0)
    print(f"publish returned rc={rc} mid={mid}")

    # wait up to 5s for subscriber to receive
    if received_evt.wait(5):
        print("Subscriber received the message.")
    else:
        print("Subscriber did not receive the message within 5s.")

    p.loop_stop(); p.disconnect()
    c.loop_stop(); c.disconnect()

if __name__ == '__main__':
    run_test()