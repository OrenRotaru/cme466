import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.MQTT_BROKER = os.getenv("MQTT_BROKER")
        self.MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
        self.MQTT_TOPIC_SUBSCRIBE = os.getenv("MQTT_TOPIC_SUBSCRIBE")  # Receive commands from admin
        self.MQTT_TOPIC_PUBLISH = os.getenv("MQTT_TOPIC_PUBLISH")      # Send sensor data to admin


config = Config()
