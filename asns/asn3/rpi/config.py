import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.MQTT_BROKER = os.getenv("MQTT_BROKER")
        self.MQTT_PORT = os.getenv("MQTT_PORT")
        self.MQTT_TOPIC = os.getenv("MQTT_TOPIC")


config = Config()
