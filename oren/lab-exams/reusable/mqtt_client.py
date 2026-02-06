"""
Reusable MQTT Client Class for CME466 Lab Exams
================================================
A flexible, generic MQTT client that handles:
- Text/String messages
- JSON messages
- Binary/Image data
- Python objects (pickle)
- Optional Fernet encryption for any of the above

Usage:
    from mqtt_client import MQTTClient

    client = MQTTClient(
        broker="broker.hivemq.com",
        port=1883,
        subscribe_topics=["my/topic"],
        encryption_key=b"your-fernet-key"  # Optional
    )
    client.connect()
    client.publish_text("my/topic", "Hello!", encrypt=True)
"""

import json
import pickle
import base64
from typing import Optional, List, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum

import paho.mqtt.client as mqtt
from cryptography.fernet import Fernet

# Optional PySide6/PyQt support for Qt signals
try:
    from PySide6.QtCore import QObject, Signal

    HAS_PYSIDE6 = True
except ImportError:
    try:
        from PyQt5.QtCore import QObject, pyqtSignal as Signal

        HAS_PYSIDE6 = False
    except ImportError:
        QObject = object
        Signal = None
        HAS_PYSIDE6 = False


class MessageType(Enum):
    """Enum for different message types."""

    TEXT = "text"
    JSON = "json"
    BYTES = "bytes"
    IMAGE = "image"
    PICKLE = "pickle"
    UNKNOWN = "unknown"


@dataclass
class MQTTMessage:
    """
    Container for received MQTT messages with metadata.
    """

    topic: str
    payload: bytes
    message_type: MessageType = MessageType.UNKNOWN
    decrypted: bool = False
    data: Any = None  # Parsed data (str, dict, bytes, object)
    error: Optional[str] = None


class MQTTClient(QObject if QObject != object else object):
    """
    Generic, reusable MQTT client with optional encryption support.

    Features:
    - Connect/disconnect with automatic reconnection
    - Publish text, JSON, bytes, images, or Python objects
    - Optional Fernet encryption on any message type
    - Qt signals for thread-safe GUI updates (if PySide6/PyQt5 available)
    - Callback-based message handling

    Attributes:
        broker (str): MQTT broker address
        port (int): MQTT broker port
        subscribe_topics (List[str]): Topics to subscribe to on connect
        encryption_key (bytes): Optional Fernet key for encryption
        client_id (str): Optional client ID
    """

    # Qt Signals (only active if PySide6/PyQt5 is available)
    if Signal:
        # Emitted when any message is received
        message_received = Signal(object)  # MQTTMessage
        # Specific signals for different data types
        text_received = Signal(str, str)  # topic, text
        json_received = Signal(str, dict)  # topic, data
        bytes_received = Signal(str, bytes)  # topic, data
        image_received = Signal(str, bytes)  # topic, image_bytes
        pickle_received = Signal(str, object)  # topic, object
        # Connection status
        connected = Signal()
        disconnected = Signal()
        connection_error = Signal(str)

    def __init__(
        self,
        broker: str = "broker.hivemq.com",
        port: int = 1883,
        subscribe_topics: Optional[List[str]] = None,
        publish_topic: Optional[str] = None,
        encryption_key: Optional[bytes] = None,
        client_id: Optional[str] = None,
        auto_reconnect: bool = True,
    ):
        """
        Initialize the MQTT client.

        Args:
            broker: MQTT broker address
            port: MQTT broker port (default 1883)
            subscribe_topics: List of topics to subscribe to on connect
            publish_topic: Default topic for publishing (can be overridden)
            encryption_key: Fernet key for encryption (generate with Fernet.generate_key())
            client_id: Optional client ID (auto-generated if not provided)
            auto_reconnect: Whether to auto-reconnect on disconnect
        """
        if QObject != object:
            super().__init__()

        self.broker = broker
        self.port = port
        self.subscribe_topics = subscribe_topics or []
        self.publish_topic = publish_topic
        self.encryption_key = encryption_key
        self.auto_reconnect = auto_reconnect

        # Setup Fernet cipher if key provided
        self.cipher: Optional[Fernet] = None
        if encryption_key:
            self.cipher = Fernet(encryption_key)

        # Setup MQTT client
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # Callback storage for non-Qt usage
        self._message_callbacks: List[Callable[[MQTTMessage], None]] = []
        self._topic_callbacks: dict[str, List[Callable[[MQTTMessage], None]]] = {}

        self._is_connected = False

    # ─── CONNECTION MANAGEMENT ─────────────────────────────────────────────────

    def connect(self) -> bool:
        """
        Connect to the MQTT broker and start the background loop.

        Returns:
            True if connection initiated successfully
        """
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            print(f"[MQTT] Connecting to {self.broker}:{self.port}...")
            return True
        except Exception as e:
            print(f"[MQTT] Connection failed: {e}")
            if Signal and hasattr(self, "connection_error"):
                self.connection_error.emit(str(e))
            return False

    def disconnect(self):
        """Disconnect from the broker and stop the loop."""
        self.client.loop_stop()
        self.client.disconnect()
        print("[MQTT] Disconnected")

    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._is_connected

    def subscribe(self, topic: str):
        """Subscribe to an additional topic after connection."""
        self.client.subscribe(topic)
        if topic not in self.subscribe_topics:
            self.subscribe_topics.append(topic)
        print(f"[MQTT] Subscribed to: {topic}")

    def unsubscribe(self, topic: str):
        """Unsubscribe from a topic."""
        self.client.unsubscribe(topic)
        if topic in self.subscribe_topics:
            self.subscribe_topics.remove(topic)
        print(f"[MQTT] Unsubscribed from: {topic}")

    # ─── ENCRYPTION HELPERS ────────────────────────────────────────────────────

    def set_encryption_key(self, key: bytes):
        """Set or update the encryption key."""
        self.encryption_key = key
        self.cipher = Fernet(key)
        print("[MQTT] Encryption key updated")

    def _encrypt(self, data: bytes) -> bytes:
        """Encrypt bytes using Fernet."""
        if not self.cipher:
            raise ValueError("No encryption key set. Call set_encryption_key() first.")
        return self.cipher.encrypt(data)

    def _decrypt(self, data: bytes) -> bytes:
        """Decrypt Fernet-encrypted bytes."""
        if not self.cipher:
            raise ValueError("No encryption key set. Call set_encryption_key() first.")
        return self.cipher.decrypt(data)

    # ─── PUBLISH METHODS ───────────────────────────────────────────────────────

    def publish_text(
        self, topic: Optional[str] = None, text: str = "", encrypt: bool = False
    ) -> bool:
        """
        Publish a plain text message.

        Args:
            topic: Topic to publish to (uses default if not provided)
            text: Text message to send
            encrypt: Whether to encrypt before sending
        """
        topic = topic or self.publish_topic
        if not topic:
            raise ValueError("No topic specified and no default publish_topic set")

        payload = text.encode("utf-8")
        if encrypt:
            payload = self._encrypt(payload)

        result = self.client.publish(topic, payload)
        result.wait_for_publish()
        print(f"[MQTT] Published text to {topic} (encrypted={encrypt})")
        return result.is_published()

    def publish_json(
        self, topic: Optional[str] = None, data: dict = None, encrypt: bool = False
    ) -> bool:
        """
        Publish a JSON message.

        Args:
            topic: Topic to publish to
            data: Dictionary to serialize as JSON
            encrypt: Whether to encrypt before sending
        """
        topic = topic or self.publish_topic
        if not topic:
            raise ValueError("No topic specified and no default publish_topic set")

        payload = json.dumps(data or {}).encode("utf-8")
        if encrypt:
            payload = self._encrypt(payload)

        result = self.client.publish(topic, payload)
        result.wait_for_publish()
        print(f"[MQTT] Published JSON to {topic} (encrypted={encrypt})")
        return result.is_published()

    def publish_bytes(
        self, topic: Optional[str] = None, data: bytes = b"", encrypt: bool = False
    ) -> bool:
        """
        Publish raw bytes.

        Args:
            topic: Topic to publish to
            data: Raw bytes to send
            encrypt: Whether to encrypt before sending
        """
        topic = topic or self.publish_topic
        if not topic:
            raise ValueError("No topic specified and no default publish_topic set")

        payload = data
        if encrypt:
            payload = self._encrypt(payload)

        result = self.client.publish(topic, payload)
        result.wait_for_publish()
        print(f"[MQTT] Published {len(data)} bytes to {topic} (encrypted={encrypt})")
        return result.is_published()

    def publish_image(
        self,
        topic: Optional[str] = None,
        image_bytes: bytes = None,
        image_path: str = None,
        encrypt: bool = False,
    ) -> bool:
        """
        Publish an image (from bytes or file path).

        Args:
            topic: Topic to publish to
            image_bytes: Raw image bytes (if already loaded)
            image_path: Path to image file (alternative to image_bytes)
            encrypt: Whether to encrypt before sending
        """
        topic = topic or self.publish_topic
        if not topic:
            raise ValueError("No topic specified and no default publish_topic set")

        if image_path:
            with open(image_path, "rb") as f:
                image_bytes = f.read()

        if not image_bytes:
            raise ValueError("Either image_bytes or image_path must be provided")

        payload = image_bytes
        if encrypt:
            payload = self._encrypt(payload)

        result = self.client.publish(topic, payload)
        result.wait_for_publish()
        print(
            f"[MQTT] Published image ({len(image_bytes)} bytes) to {topic} (encrypted={encrypt})"
        )
        return result.is_published()

    def publish_pickle(
        self, topic: Optional[str] = None, obj: Any = None, encrypt: bool = False
    ) -> bool:
        """
        Publish a Python object using pickle serialization.

        Args:
            topic: Topic to publish to
            obj: Python object to serialize and send
            encrypt: Whether to encrypt before sending
        """
        topic = topic or self.publish_topic
        if not topic:
            raise ValueError("No topic specified and no default publish_topic set")

        payload = pickle.dumps(obj)
        if encrypt:
            payload = self._encrypt(payload)

        result = self.client.publish(topic, payload)
        result.wait_for_publish()
        print(f"[MQTT] Published pickle object to {topic} (encrypted={encrypt})")
        return result.is_published()

    # ─── CALLBACK REGISTRATION ─────────────────────────────────────────────────

    def on_message(self, callback: Callable[[MQTTMessage], None]):
        """
        Register a callback for all incoming messages.

        Args:
            callback: Function that takes an MQTTMessage
        """
        self._message_callbacks.append(callback)

    def on_topic(self, topic: str, callback: Callable[[MQTTMessage], None]):
        """
        Register a callback for messages on a specific topic.

        Args:
            topic: Topic to filter for
            callback: Function that takes an MQTTMessage
        """
        if topic not in self._topic_callbacks:
            self._topic_callbacks[topic] = []
        self._topic_callbacks[topic].append(callback)

    # ─── INTERNAL CALLBACKS ────────────────────────────────────────────────────

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Internal callback when connected to broker."""
        if rc == 0:
            self._is_connected = True
            print(f"[MQTT] Connected to {self.broker}")

            # Subscribe to configured topics
            for topic in self.subscribe_topics:
                client.subscribe(topic)
                print(f"[MQTT] Subscribed to: {topic}")

            if Signal and hasattr(self, "connected"):
                self.connected.emit()
        else:
            print(f"[MQTT] Connection failed with code: {rc}")
            if Signal and hasattr(self, "connection_error"):
                self.connection_error.emit(f"Connection failed with code: {rc}")

    def _on_disconnect(self, client, userdata, disconnect_flags, rc, properties=None):
        """Internal callback when disconnected from broker."""
        self._is_connected = False
        print(f"[MQTT] Disconnected (rc={rc})")
        if Signal and hasattr(self, "disconnected"):
            self.disconnected.emit()

    def _on_message(self, client, userdata, msg):
        """
        Internal callback when message received.
        Tries to detect message type and decrypt if necessary.
        """
        message = MQTTMessage(
            topic=msg.topic,
            payload=msg.payload,
        )

        payload = msg.payload

        # Try to decrypt if we have a cipher
        if self.cipher:
            try:
                payload = self._decrypt(payload)
                message.decrypted = True
            except Exception:
                # Not encrypted or wrong key, use original payload
                pass

        # Try to detect and parse message type
        message = self._parse_payload(message, payload)

        # Emit Qt signals if available
        self._emit_signals(message)

        # Call registered callbacks
        for callback in self._message_callbacks:
            try:
                callback(message)
            except Exception as e:
                print(f"[MQTT] Callback error: {e}")

        # Call topic-specific callbacks
        if msg.topic in self._topic_callbacks:
            for callback in self._topic_callbacks[msg.topic]:
                try:
                    callback(message)
                except Exception as e:
                    print(f"[MQTT] Topic callback error: {e}")

    def _parse_payload(self, message: MQTTMessage, payload: bytes) -> MQTTMessage:
        """Try to detect and parse the payload type."""

        # Try JSON first
        try:
            data = json.loads(payload.decode("utf-8"))
            message.message_type = MessageType.JSON
            message.data = data
            return message
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

        # Try pickle
        try:
            data = pickle.loads(payload)
            message.message_type = MessageType.PICKLE
            message.data = data
            return message
        except Exception:
            pass

        # Try plain text
        try:
            text = payload.decode("utf-8")
            message.message_type = MessageType.TEXT
            message.data = text
            return message
        except UnicodeDecodeError:
            pass

        # Check if it looks like an image (common magic bytes)
        if self._is_image(payload):
            message.message_type = MessageType.IMAGE
            message.data = payload
            return message

        # Default to raw bytes
        message.message_type = MessageType.BYTES
        message.data = payload
        return message

    def _is_image(self, data: bytes) -> bool:
        """Check if bytes appear to be a common image format."""
        if len(data) < 8:
            return False

        # JPEG
        if data[:2] == b"\xff\xd8":
            return True
        # PNG
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return True
        # GIF
        if data[:6] in (b"GIF87a", b"GIF89a"):
            return True
        # BMP
        if data[:2] == b"BM":
            return True
        # WebP
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return True

        return False

    def _emit_signals(self, message: MQTTMessage):
        """Emit Qt signals for the message."""
        if not Signal:
            return

        try:
            # General message signal
            if hasattr(self, "message_received"):
                self.message_received.emit(message)

            # Type-specific signals
            if message.message_type == MessageType.TEXT and hasattr(
                self, "text_received"
            ):
                self.text_received.emit(message.topic, message.data)
            elif message.message_type == MessageType.JSON and hasattr(
                self, "json_received"
            ):
                self.json_received.emit(message.topic, message.data)
            elif message.message_type == MessageType.BYTES and hasattr(
                self, "bytes_received"
            ):
                self.bytes_received.emit(message.topic, message.data)
            elif message.message_type == MessageType.IMAGE and hasattr(
                self, "image_received"
            ):
                self.image_received.emit(message.topic, message.data)
            elif message.message_type == MessageType.PICKLE and hasattr(
                self, "pickle_received"
            ):
                self.pickle_received.emit(message.topic, message.data)
        except Exception as e:
            print(f"[MQTT] Signal emit error: {e}")

    # ─── UTILITY METHODS ───────────────────────────────────────────────────────

    @staticmethod
    def generate_key() -> bytes:
        """Generate a new Fernet encryption key."""
        key = Fernet.generate_key()
        print(f"[MQTT] Generated key: {key.decode()}")
        return key

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False


# ─── CONVENIENCE FUNCTIONS ─────────────────────────────────────────────────────


def create_client(
    broker: str = "broker.hivemq.com",
    subscribe: Union[str, List[str]] = None,
    publish: str = None,
    key: bytes = None,
) -> MQTTClient:
    """
    Quick helper to create and connect an MQTT client.

    Example:
        client = create_client(
            broker="broker.hivemq.com",
            subscribe="my/topic",
            publish="my/response",
            key=b"my-fernet-key"
        )
    """
    topics = [subscribe] if isinstance(subscribe, str) else (subscribe or [])

    client = MQTTClient(
        broker=broker,
        subscribe_topics=topics,
        publish_topic=publish,
        encryption_key=key,
    )
    return client
