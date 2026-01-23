import paho.mqtt.client as paho
import time
import threading
import pickle
from gpiozero import DistanceSensor, LED

# GPIO Pin Setup
sensor = DistanceSensor(echo=24, trigger=23)
led = LED(22)

# Event to signal when connected
connected_event = threading.Event()

# MQTT on_connect callback
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Publisher connected with code {reason_code}.")
    connected_event.set()

# MQTT Client Setup
client = paho.Client(paho.CallbackAPIVersion.VERSION2, client_id="", protocol=paho.MQTTv5)
client.on_connect = on_connect

# Connect to the MQTT Broker
mqttBroker = "broker.mqttdashboard.com"
port = 1883

# Establish connection
client.connect(mqttBroker, port)
client.loop_start()
connected_event.wait()

try:
    print("Publisher is running. Sending Distance data...")
    while True:
        # gpiozero returns distance in meters, multiplying by 100 for cm
        distance_cm = round(sensor.distance * 100, 2)
        
        # Local feedback: LED turns on if object is closer than 5cm
        if distance_cm < 5:
            led.on()
        else:
            led.off()

        # Publish the numeric distance
        client.publish("jpor/asn2", pickle.dumps(distance_cm))
        print(f"Published: {distance_cm} cm")
        
        time.sleep(1)  # Publish rate: 1 Hz

except KeyboardInterrupt:
    print("\nStopping Publisher...")

client.loop_stop()
client.disconnect()