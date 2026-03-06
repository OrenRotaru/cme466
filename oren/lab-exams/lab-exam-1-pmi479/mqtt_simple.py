import json
import pickle
import time
from typing import Optional, Callable, Any

import paho.mqtt.client as mqtt
from cryptography.fernet import Fernet


class MQTTHelper:
    """
    Simple MQTT client with encryption support.
    """

    def __init__(
        self,
        broker: str = "broker.hivemq.com",
        port: int = 1883,
        sub_topic: str = None,
        pub_topic: str = None,
        key: bytes = None,
        auto_decrypt: bool = True,
        # QoS for subscriptions
        sub_qos: int = 0,
        # Last Will and Testament
        lwt_topic: str = None,
        lwt_message: str = None,
        lwt_qos: int = 0,
        lwt_retain: bool = False,
    ):
        self.broker = broker
        self.port = port
        self.sub_topic = sub_topic
        self.pub_topic = pub_topic
        self.auto_decrypt = auto_decrypt
        self.sub_qos = sub_qos

        # Encryption
        self.key = key
        self.cipher: Optional[Fernet] = Fernet(key) if key else None

        # MQTT client
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._handle_connect
        self.client.on_disconnect = self._handle_disconnect
        self.client.on_message = self._handle_message

        # Set Last Will and Testament (before connecting!)
        if lwt_topic and lwt_message:
            self.client.will_set(
                topic=lwt_topic,
                payload=lwt_message.encode("utf-8"),
                qos=lwt_qos,
                retain=lwt_retain,
            )
            print(f"[MQTT] LWT set: '{lwt_message}' on {lwt_topic}")

        self._connected = False

        # YOUR callback - receives (topic: str, payload: bytes)
        self.on_message: Callable[[str, bytes], None] = None

        # Optional connection callbacks
        self.on_connect: Callable[[], None] = None
        self.on_disconnect: Callable[[], None] = None

    # ─── CONNECTION ────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Connect to broker and start background loop."""
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            print(f"[MQTT] Connecting to {self.broker}:{self.port}...")
            return True
        except Exception as e:
            print(f"[MQTT] Connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect from broker (clean disconnect, LWT not sent)."""
        self.client.loop_stop()
        self.client.disconnect()
        print("[MQTT] Disconnected")

    def is_connected(self) -> bool:
        return self._connected

    def subscribe(self, topic: str, qos: int = 0):
        """Subscribe to a topic with specified QoS."""
        self.client.subscribe(topic, qos=qos)
        print(f"[MQTT] Subscribed: {topic} (QoS={qos})")

    def unsubscribe(self, topic: str):
        """Unsubscribe from a topic."""
        self.client.unsubscribe(topic)
        print(f"[MQTT] Unsubscribed: {topic}")

    def wait(self, seconds: float = 1.0):
        """Wait (useful in scripts)."""
        time.sleep(seconds)

    # ─── ENCRYPTION ────────────────────────────────────────────────────────────

    def set_key(self, key: bytes):
        """Set or update encryption key."""
        self.key = key
        self.cipher = Fernet(key)

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt bytes."""
        if not self.cipher:
            raise ValueError("No encryption key set")
        return self.cipher.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt bytes."""
        if not self.cipher:
            raise ValueError("No encryption key set")
        return self.cipher.decrypt(data)

    @staticmethod
    def generate_key() -> bytes:
        """Generate a new Fernet key."""
        return Fernet.generate_key()

    # ─── SEND METHODS ──────────────────────────────────────────────────────────
    # All send methods support:
    #   - topic: override default pub_topic
    #   - encrypt: encrypt payload before sending
    #   - qos: 0, 1, or 2
    #   - retain: broker keeps message for new subscribers

    def send_text(
        self,
        text: str,
        topic: str = None,
        encrypt: bool = False,
        qos: int = 0,
        retain: bool = False,
    ):
        """Send a text string."""
        topic = topic or self.pub_topic
        payload = text.encode("utf-8")
        if encrypt:
            payload = self.encrypt(payload)
        self.client.publish(topic, payload, qos=qos, retain=retain)
        print(
            f"[MQTT] Sent text to {topic} (encrypt={encrypt}, qos={qos}, retain={retain})"
        )

    def send_json(
        self,
        data: dict,
        topic: str = None,
        encrypt: bool = False,
        qos: int = 0,
        retain: bool = False,
    ):
        """Send a JSON dictionary."""
        topic = topic or self.pub_topic
        payload = json.dumps(data).encode("utf-8")
        if encrypt:
            payload = self.encrypt(payload)
        self.client.publish(topic, payload, qos=qos, retain=retain)
        print(
            f"[MQTT] Sent JSON to {topic} (encrypt={encrypt}, qos={qos}, retain={retain})"
        )

    def send_bytes(
        self,
        data: bytes,
        topic: str = None,
        encrypt: bool = False,
        qos: int = 0,
        retain: bool = False,
    ):
        """Send raw bytes."""
        topic = topic or self.pub_topic
        payload = data
        if encrypt:
            payload = self.encrypt(payload)
        self.client.publish(topic, payload, qos=qos, retain=retain)
        print(
            f"[MQTT] Sent {len(data)} bytes to {topic} (encrypt={encrypt}, qos={qos}, retain={retain})"
        )

    def send_image(
        self,
        path: str = None,
        data: bytes = None,
        topic: str = None,
        encrypt: bool = False,
        qos: int = 0,
        retain: bool = False,
    ):
        """Send an image (from file path or bytes)."""
        topic = topic or self.pub_topic
        if path:
            with open(path, "rb") as f:
                data = f.read()
        if not data:
            raise ValueError("Provide path or data")
        payload = data
        if encrypt:
            payload = self.encrypt(payload)
        self.client.publish(topic, payload, qos=qos, retain=retain)
        print(
            f"[MQTT] Sent image ({len(data)} bytes) to {topic} (encrypt={encrypt}, qos={qos}, retain={retain})"
        )

    def send_pickle(
        self,
        obj: Any,
        topic: str = None,
        encrypt: bool = False,
        qos: int = 0,
        retain: bool = False,
    ):
        """Send a Python object (pickled)."""
        topic = topic or self.pub_topic
        payload = pickle.dumps(obj)
        if encrypt:
            payload = self.encrypt(payload)
        self.client.publish(topic, payload, qos=qos, retain=retain)
        print(
            f"[MQTT] Sent pickle to {topic} (encrypt={encrypt}, qos={qos}, retain={retain})"
        )

    # ─── HELPER PARSE METHODS ──────────────────────────────────────────────────

    def parse_text(self, payload: bytes) -> str:
        """Parse payload as text."""
        return payload.decode("utf-8")

    def parse_json(self, payload: bytes) -> dict:
        """Parse payload as JSON."""
        return json.loads(payload.decode("utf-8"))

    def parse_pickle(self, payload: bytes) -> Any:
        """Parse payload as pickle."""
        return pickle.loads(payload)

    def save_image(self, payload: bytes, filename: str):
        """Save payload as image file."""
        with open(filename, "wb") as f:
            f.write(payload)
        print(f"[MQTT] Saved image: {filename}")

    # ─── INTERNAL HANDLERS ─────────────────────────────────────────────────────

    def _handle_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self._connected = True
            print(f"[MQTT] Connected to {self.broker}")
            if self.sub_topic:
                client.subscribe(self.sub_topic, qos=self.sub_qos)
                print(f"[MQTT] Subscribed: {self.sub_topic} (QoS={self.sub_qos})")
            if self.on_connect:
                self.on_connect()
        else:
            print(f"[MQTT] Connection failed: rc={rc}")

    def _handle_disconnect(
        self, client, userdata, disconnect_flags, rc, properties=None
    ):
        self._connected = False
        print(f"[MQTT] Disconnected (rc={rc})")
        if self.on_disconnect:
            self.on_disconnect()

    def _handle_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload

        # Auto-decrypt if enabled and key is set
        if self.auto_decrypt and self.cipher:
            try:
                payload = self.decrypt(payload)
            except Exception:
                pass  # Not encrypted or wrong key, use original

        # Call user's callback with raw payload
        if self.on_message:
            self.on_message(topic, payload)

    # ─── CONTEXT MANAGER ───────────────────────────────────────────────────────

    def __enter__(self):
        self.connect()
        time.sleep(0.5)
        return self

    def __exit__(self, *args):
        self.disconnect()


# ─── EXAMPLE ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    KEY = b"B7cOuif_4ztTXpSeeGFt7fnUGCcMdSOPxVF7Ayybwiw="

    mqtt = MQTTHelper(
        broker="broker.hivemq.com",
        sub_topic="cme466/test",
        pub_topic="cme466/test",
        key=KEY,
        sub_qos=1,  # Subscribe with QoS 1
        # Last Will - sent if we disconnect unexpectedly
        lwt_topic="cme466/status",
        lwt_message="Client disconnected unexpectedly!",
        lwt_qos=1,
        lwt_retain=True,
    )

    def handle_message(topic, payload):
        print(f"[RECEIVED] {len(payload)} bytes from {topic}")
        try:
            text = mqtt.parse_text(payload)
            print(f"  -> Text: {text}")
        except:
            print(f"  -> Binary data")

    mqtt.on_message = handle_message
    mqtt.connect()

    time.sleep(1)

    # Send with QoS and retain
    mqtt.send_text("Hello!", encrypt=True, qos=1, retain=True)

    print("Waiting... (Ctrl+C to exit)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        mqtt.disconnect()
