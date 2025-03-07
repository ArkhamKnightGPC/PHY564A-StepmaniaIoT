import json
import logging
import random
import sys
import time
import threading
from datetime import datetime
from typing import Iterator
import numpy as np
from paho.mqtt import client as mqtt_client
from typing import Any
import struct

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
LOCK = threading.Lock()
start_time = 0
end_time = 0

latencies = []

class MqttManager:
    """Class to handle the MQTT connection."""

    def __init__(self, broker: str, port: int, sub_topic: str, pub_topic: str):
        self.broker = broker
        self.port = port
        self.sub_topic = sub_topic
        self.pub_topic = pub_topic
        self.client_id = f'publish-{random.randint(0, 1000)}'
        self.client: mqtt_client.Client = self.connect_mqtt()
        self.subscribe()

    def connect_mqtt(self) -> mqtt_client:
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logger.info("Connected to MQTT Broker!")
            else:
                logger.error("Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1)
        client.on_connect = on_connect
        client.connect(self.broker, self.port)
        return client
    
    def subscribe(self):
        def on_message(client: mqtt_client, userdata: None, msg: mqtt_client.MQTTMessage):
            global end_time, latencies
            end_time = time.time()
            latency = end_time - start_time
            latencies.append(latency)
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic. Latency: {latency:.6f} seconds. Avg: {np.mean(latencies):.6f} seconds")


        self.client.subscribe(self.sub_topic)
        self.client.on_message = on_message

    def publish(self, msg: Any):
        global start_time
        start_time = time.time()
        result = self.client.publish(self.pub_topic, msg)
        status = result[0]
        if status == 0:
            print(f"Sent `{msg}` to topic `{self.pub_topic}`")
        else:
            print(f"Failed to send message  '{msg}' to topic {self.pub_topic}")

    def run(self):
        self.client.loop_forever()
    
    def run_threaded(self):
        mqtt_thread = threading.Thread(target=self.run, daemon=True)
        mqtt_thread.start()
        
if __name__ == "__main__":
    mqtt_manager = MqttManager('192.168.0.103', 1883, "pong", "ping")
    mqtt_manager.run_threaded()
    with LOCK:
        print("MQTT Manager started")
        print("Press Enter to exit\n")

    # get precise time 
    while True:
        print("Try sending Ping...")
        mqtt_manager.publish("Ping")
        time.sleep(5)
    
        
    input("")