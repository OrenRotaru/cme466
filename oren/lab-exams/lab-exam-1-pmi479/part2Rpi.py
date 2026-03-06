import time
from mqtt_simple import MQTTHelper

BROKER = "test.mosquitto.org"
SUB_TOPIC = "cme466_lab_exam_pmi479"
PUB_TOPIC = "cme466_lab_exam_pmi479"


if __name__ == "__main__":

    mqtt = MQTTHelper(broker=BROKER, 
    sub_topic=SUB_TOPIC, 
    auto_decrypt=False,
    pub_topic=PUB_TOPIC,
    )

    def handle_message(topic: str, payload: bytes):
      message = mqtt.parse_text(payload)
      print(message)

    mqtt.on_message = handle_message


    mqtt.connect()

    try:
        while True:
          command = input("command: ")
          mqtt.send_text(command)
          time.sleep(1)
    except KeyboardInterrupt:
        mqtt.disconnect()
