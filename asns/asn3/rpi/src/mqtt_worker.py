import multiprocessing as mp
import paho.mqtt.client as paho
from config import config
import time

def mqtt_main(command_queue: mp.Queue, telemetry_queue: mp.Queue):

  def on_connect(client, userdata, flags, reason_code, properties):
    # Subscribe to the command topic when connected
    client.subscribe(config.MQTT_TOPIC_SUBSCRIBE)
    print(f"Subscribed to {config.MQTT_TOPIC_SUBSCRIBE}")

  def on_message(client, userdata, msg):
    # We need to put incoming messages into the command queue
    payload = msg.payload.decode()
    command_queue.put(payload)

  def on_subscribe(client, userdata, mid, reason_codes, properties):
    pass

  # defining the client
  client = paho.Client(
    paho.CallbackAPIVersion.VERSION2,
    client_id="mqtt_worker",
    userdata=None,
    protocol=paho.MQTTv5
  )
  client.on_connect = on_connect
  client.on_message = on_message
  client.on_subscribe = on_subscribe

  # connecting to the broker
  client.connect(config.MQTT_BROKER, config.MQTT_PORT)
  client.loop_start()

  while True:
    # TODO: check if there is telemetry to send to the broker
    time.sleep(0.01)