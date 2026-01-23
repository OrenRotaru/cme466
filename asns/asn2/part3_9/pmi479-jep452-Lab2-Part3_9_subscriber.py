import paho.mqtt.client as paho
import pickle
from gpiozero import LED

led = LED(22)

# MQTT Callbacks
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with code {reason_code}.")
    client.subscribe("jpor/asn2")

# Message callback
def on_message(client, userdata, msg):
    payload = pickle.loads(msg.payload)
    # Control LED based on the message typed in the publisher
    if payload == "on":
        led.on()
    elif payload == "off":
        led.off()
    print(f"Received: {payload}")

# MQTT Client Setup
client = paho.Client(
    paho.CallbackAPIVersion.VERSION2, client_id="", userdata=None, protocol=paho.MQTTv5
)
# Assign callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connect to Broker
mqttBroker = "broker.mqttdashboard.com"
client.connect(mqttBroker, 1883)

# Main loop
try:
    client.loop_forever()
except KeyboardInterrupt:
    led.off()
    client.disconnect()