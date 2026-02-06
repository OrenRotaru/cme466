```python
# Create JSON String
data = {"sensor": "temp_1", "value": 24.5}
json_str = json.dumps(data)  # Convert dict to string

# Parse JSON String
received_data = json.loads(json_str) # Convert string to dict
print(received_data["value"]) # Access data
```

Common Exam patterns for mqtt paho:
```python
import paho.mqtt.client as mqtt

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message

client.connect("broker.hivemq.com", 1883)
client.subscribe("test/topic")

# Essential for receiving messages without blocking the UI
client.loop_start()
```

## 2. Publishing Code Pattern
```python
# Open image in binary read format
with open("./image.jpg", 'rb') as file:
    filecontent = file.read()
    byteArr = bytearray(filecontent) # Convert to byte array
    
# Publish to topic
client.publish("lab/camera/image", byteArr)