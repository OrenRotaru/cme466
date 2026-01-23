import paho.mqtt.client as paho
import pickle

# MQTT on_connect callback
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Subscriber connected with code {reason_code}.")
    client.subscribe("jpor/asn2")

# MQTT on_message callback
def on_message(client, userdata, msg):
    try:
        payload = pickle.loads(msg.payload)
        
        # Check if the message is a distance (float/int)
        if isinstance(payload, (float, int)):
            print(f"Live Sensor Data: {payload} cm")
        else:
            print(f"Received other data: {payload}")
            
    except Exception as e:
        print(f"Error decoding: {e}")

# MQTT Client Setup
client = paho.Client(paho.CallbackAPIVersion.VERSION2, client_id="", protocol=paho.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message

mqttBroker = "broker.mqttdashboard.com"
port = 1883

client.connect(mqttBroker, port)

# Main loop
try:
    print("Subscriber waiting for live sensor updates...")
    client.loop_forever()
except KeyboardInterrupt:
    print("\nDisconnecting...")
    client.disconnect()