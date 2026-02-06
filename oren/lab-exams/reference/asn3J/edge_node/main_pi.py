# main_pi.py - Edge Node Application for Parking Management System (Raspberry Pi)
import time, pickle
import paho.mqtt.client as paho
from gpiozero import DistanceSensor, LED, Button

# Configuration Parameters
BROKER = "broker.mqttdashboard.com"
TOPIC_DATA = "jpor/asn3/data"
TOPIC_CMD  = "jpor/asn3/commands"

# Hardware Setup

spots = [
    Button(5, pull_up=False),
    Button(6, pull_up=False),
    Button(13, pull_up=False),
    Button(19, pull_up=False),
    Button(26, pull_up=False)
]

# LED and Ultrasonic Sensor
warn_led = LED(12)
sensor = DistanceSensor(echo=24, trigger=23)

# MQTT Functions

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected: {reason_code}")
    client.subscribe(TOPIC_CMD)

def on_message(client, userdata, msg):
    try:
        # Deserialize the incoming message
        data = pickle.loads(msg.payload)
        cmd = data.get("command")
        
        if cmd == "WARN_ON":
            warn_led.blink(on_time=0.5, off_time=0.5)
            print("[APP]: Warning LED ON")
            
        elif cmd == "WARN_OFF":
            warn_led.off()
            print("[APP]: Warning LED OFF")
            
        elif cmd == "DISPLAY_MSG":
            text = data.get("text")
            print(f"\n[APP]: {text}\n")
            
    except Exception as e:
        print(f"Error: {e}")

# MQTT Client Setup
client = paho.Client(paho.CallbackAPIVersion.VERSION2, protocol=paho.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, 1883)
client.loop_start()

print("Monitoring Parking Spots... (Ctrl+C to stop)")

try:
    while True:
        # Read Parking Spots
        current_status = []
        
        # Check each spot manually
        for spot_button in spots:
            if spot_button.is_pressed:
                current_status.append(1) # Occupied
            else:
                current_status.append(0) # Empty

        # Read Sensor
        dist = round(sensor.distance * 100, 2)
        
        # Create Data Packet for each parking spot and sensor
        data_packet = {
            "parking_spots": current_status,
            "sensor_data": dist
        }
        
        # Send Data
        payload = pickle.dumps(data_packet)
        client.publish(TOPIC_DATA, payload)
        
        # What is being sent, doesnt need to be shown
        # print(f"Sent: {current_status} | {dist}cm")
        time.sleep(2)

except KeyboardInterrupt:
    print("Stopping...")

finally:
    warn_led.off()
    client.disconnect()
