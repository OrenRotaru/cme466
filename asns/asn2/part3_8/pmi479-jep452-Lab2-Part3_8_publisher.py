import paho.mqtt.client as paho
import time
import threading
import pickle
from gpiozero import Button, LED

button = Button(24)
led = LED(23)

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

# Function to send the button alert
def send_button_event():
    led.on() # Feedback on the PI side to confirm button press
    msg = "BUTTON PRESED"
    client.publish("jpor/asn2", pickle.dumps(msg))
    print(f"Published: {msg}")
    time.sleep(0.2)
    led.off()

# Link the physical button to the function
button.when_pressed = send_button_event

try:
    print("Publisher is running. Press the button on GPIO 24...")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping Publisher...")

client.loop_stop()
client.disconnect()