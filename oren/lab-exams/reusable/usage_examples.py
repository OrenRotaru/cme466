"""
Quick Usage Examples for MQTTClient
====================================
Copy-paste these snippets for your exam!
"""

from mqtt_client import MQTTClient, create_client
from cryptography.fernet import Fernet

# ─── EXAMPLE 1: Basic Text Messaging ───────────────────────────────────────────


def example_basic_text():
    """Simple text send/receive without encryption."""

    client = MQTTClient(
        broker="broker.hivemq.com",
        subscribe_topics=["my/topic"],
        publish_topic="my/topic",
    )

    # Register callback for incoming messages
    def on_message(msg):
        print(f"Received: {msg.data}")

    client.on_message(on_message)
    client.connect()

    # Send a text message
    client.publish_text(text="Hello World!")


# ─── EXAMPLE 2: Encrypted Text ─────────────────────────────────────────────────


def example_encrypted_text():
    """Text messaging with Fernet encryption."""

    KEY = b"B7cOuif_4ztTXpSeeGFt7fnUGCcMdSOPxVF7Ayybwiw="

    client = MQTTClient(
        broker="broker.hivemq.com",
        subscribe_topics=["secure/topic"],
        publish_topic="secure/topic",
        encryption_key=KEY,
    )

    def on_message(msg):
        print(f"Decrypted: {msg.data} (was encrypted: {msg.decrypted})")

    client.on_message(on_message)
    client.connect()

    # Send encrypted text
    client.publish_text(text="Secret message!", encrypt=True)


# ─── EXAMPLE 3: Send/Receive Images ────────────────────────────────────────────


def example_images():
    """Send and receive images with optional encryption."""

    KEY = b"B7cOuif_4ztTXpSeeGFt7fnUGCcMdSOPxVF7Ayybwiw="

    client = MQTTClient(
        broker="broker.hivemq.com",
        subscribe_topics=["images/topic"],
        publish_topic="images/topic",
        encryption_key=KEY,
    )

    def on_message(msg):
        if msg.message_type.value == "image":
            # Save received image
            with open("received_image.jpg", "wb") as f:
                f.write(msg.data)
            print("Image saved!")

    client.on_message(on_message)
    client.connect()

    # Send image (encrypted)
    client.publish_image(image_path="photo.jpg", encrypt=True)

    # Send image (NOT encrypted)
    client.publish_image(image_path="photo.jpg", encrypt=False)


# ─── EXAMPLE 4: JSON Messages ──────────────────────────────────────────────────


def example_json():
    """Send and receive JSON data."""

    client = MQTTClient(
        broker="broker.hivemq.com",
        subscribe_topics=["data/topic"],
        publish_topic="data/topic",
    )

    def on_message(msg):
        if msg.message_type.value == "json":
            data = msg.data  # Already parsed as dict
            print(f"Received JSON: {data}")
            print(f"  - User: {data.get('user')}")
            print(f"  - Value: {data.get('value')}")

    client.on_message(on_message)
    client.connect()

    # Send JSON
    client.publish_json(
        data={"user": "sensor1", "value": 42.5, "status": "ok"}, encrypt=False
    )


# ─── EXAMPLE 5: Python Objects (Pickle) ────────────────────────────────────────


def example_pickle():
    """Send and receive Python objects."""

    client = MQTTClient(
        broker="broker.hivemq.com",
        subscribe_topics=["objects/topic"],
        publish_topic="objects/topic",
    )

    def on_message(msg):
        if msg.message_type.value == "pickle":
            obj = msg.data  # Deserialized Python object
            print(f"Received object: {obj}")

    client.on_message(on_message)
    client.connect()

    # Send a complex Python object
    my_object = {
        "parking_spots": [0, 1, 1, 0, 1],
        "sensor_data": 45.2,
        "active": True,
    }
    client.publish_pickle(obj=my_object, encrypt=False)


# ─── EXAMPLE 6: Qt GUI Integration ─────────────────────────────────────────────


def example_qt_integration():
    """Using with PySide6/PyQt for GUI applications."""

    from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
    from PySide6.QtCore import Slot
    import sys

    class MyWindow(QMainWindow):
        def __init__(self):
            super().__init__()

            self.label = QLabel("Waiting for messages...")
            self.setCentralWidget(self.label)

            # Create MQTT client
            self.mqtt = MQTTClient(
                broker="broker.hivemq.com",
                subscribe_topics=["my/topic"],
            )

            # Connect Qt signal to slot
            self.mqtt.text_received.connect(self.on_text)
            self.mqtt.connect()

        @Slot(str, str)
        def on_text(self, topic: str, text: str):
            self.label.setText(f"Received: {text}")

    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())


# ─── EXAMPLE 7: Multiple Topics ────────────────────────────────────────────────


def example_multiple_topics():
    """Subscribe to multiple topics with different handlers."""

    client = MQTTClient(
        broker="broker.hivemq.com",
        subscribe_topics=["sensors/temp", "sensors/humidity", "commands"],
    )

    # Topic-specific callbacks
    def on_temperature(msg):
        print(f"Temperature: {msg.data}")

    def on_humidity(msg):
        print(f"Humidity: {msg.data}")

    def on_command(msg):
        print(f"Command received: {msg.data}")

    client.on_topic("sensors/temp", on_temperature)
    client.on_topic("sensors/humidity", on_humidity)
    client.on_topic("commands", on_command)

    client.connect()


# ─── EXAMPLE 8: Context Manager ────────────────────────────────────────────────


def example_context_manager():
    """Using MQTTClient as a context manager."""

    with MQTTClient(
        broker="broker.hivemq.com",
        publish_topic="my/topic",
    ) as client:
        client.publish_text(text="Hello!")
        client.publish_json(data={"key": "value"})
    # Auto-disconnects when exiting the 'with' block


# ─── QUICK REFERENCE ───────────────────────────────────────────────────────────
"""
PUBLISH METHODS:
    client.publish_text(topic, text, encrypt=False)
    client.publish_json(topic, data, encrypt=False)
    client.publish_bytes(topic, data, encrypt=False)
    client.publish_image(topic, image_bytes=None, image_path=None, encrypt=False)
    client.publish_pickle(topic, obj, encrypt=False)

RECEIVE CALLBACKS (non-Qt):
    client.on_message(callback)         # All messages
    client.on_topic("topic", callback)  # Specific topic

QT SIGNALS:
    client.message_received   -> MQTTMessage object
    client.text_received      -> (topic: str, text: str)
    client.json_received      -> (topic: str, data: dict)
    client.bytes_received     -> (topic: str, data: bytes)
    client.image_received     -> (topic: str, image_bytes: bytes)
    client.pickle_received    -> (topic: str, obj: Any)
    client.connected          -> ()
    client.disconnected       -> ()
    client.connection_error   -> (error: str)

MESSAGE TYPES:
    MessageType.TEXT    - Plain text string
    MessageType.JSON    - Parsed JSON dict
    MessageType.BYTES   - Raw bytes
    MessageType.IMAGE   - Image bytes (JPEG, PNG, etc.)
    MessageType.PICKLE  - Deserialized Python object

GENERATE ENCRYPTION KEY:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"
    # Or in code:
    key = MQTTClient.generate_key()
"""
