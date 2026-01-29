"""
MQTT service for handling broker connections and message passing.
"""

from datetime import datetime

from PySide6.QtCore import QObject, Signal, Slot

import paho.mqtt.client as paho

from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_SUBSCRIBE


class MqttService(QObject):
    """
    Worker that runs the MQTT client loop in a separate thread.
    Emits signals when messages are received or connection status changes.
    """

    messageReceived = Signal(str, str)  # timestamp, payload
    connectionStatusChanged = Signal(str)  # status string

    def __init__(self, parent=None):
        super().__init__(parent)
        self._client = paho.Client(paho.CallbackAPIVersion.VERSION2)
        self._connected = False
        self._subscribed = False

        # Set up callbacks
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._client.on_subscribe = self._on_subscribe

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """Called when connected to the broker."""
        if reason_code == 0:
            print(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            self._connected = True
            # Subscribe to topic
            client.subscribe(MQTT_TOPIC_SUBSCRIBE)
        else:
            print(f"Connection failed with code: {reason_code}")
            self.connectionStatusChanged.emit("error")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        """Called when disconnected from the broker."""
        print(f"Disconnected from MQTT broker: {reason_code}")
        self._connected = False
        self._subscribed = False
        self.connectionStatusChanged.emit("disconnected")

    def _on_subscribe(self, client, userdata, mid, reason_codes, properties):
        """Called when subscription is confirmed."""
        print(f"Subscribed to topic: {MQTT_TOPIC_SUBSCRIBE}")
        self._subscribed = True
        self.connectionStatusChanged.emit("connected")

    def _on_message(self, client, userdata, msg):
        """Called when a message is received."""
        try:
            payload = msg.payload.decode("utf-8")
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"MQTT message received: {payload}")
            self.messageReceived.emit(timestamp, payload)
        except Exception as e:
            print(f"Error processing message: {e}")

    @property
    def is_connected(self) -> bool:
        """Check if the client is connected to the broker."""
        return self._connected

    @Slot()
    def connect_to_broker(self):
        """Connect to the MQTT broker and start the loop."""
        self.connectionStatusChanged.emit("connecting")
        try:
            print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
            self._client.connect(MQTT_BROKER, MQTT_PORT)
            self._client.loop_start()
        except Exception as e:
            print(f"MQTT connection error: {e}")
            self.connectionStatusChanged.emit("error")

    def publish(self, topic: str, payload: str):
        """Publish a message to a topic."""
        if self._connected:
            self._client.publish(topic, payload)
            print(f"Published to {topic}: {payload}")
        else:
            print("Warning: MQTT not connected, message not sent")

    def stop(self):
        """Stop the MQTT client loop and disconnect."""
        self._client.loop_stop()
        self._client.disconnect()
