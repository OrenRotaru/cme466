# publisher.py — Test publisher that sends encrypted messages
# Run this alongside main.py to simulate incoming encrypted data.
#
# Usage:  python publisher.py
#         Then type messages and press Enter to send.
import time, json
import paho.mqtt.client as mqtt
from cryptography.fernet import Fernet

# ─── MUST MATCH main.py's key ────────────────────────────────────────────────
# Copy the key printed by main.py when it starts, paste it here:
SECRET_KEY = b"PASTE_THE_KEY_FROM_MAIN_PY_HERE"
cipher = Fernet(SECRET_KEY)

BROKER    = "broker.hivemq.com"
PORT      = 1883
TOPIC_PUB = "cme466/lab/encrypted_in"   # This is what main.py subscribes to

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def encrypt_text(text: str) -> bytes:
    return cipher.encrypt(text.encode("utf-8"))

def encrypt_json(data: dict) -> bytes:
    return cipher.encrypt(json.dumps(data).encode("utf-8"))

# ─── MQTT SETUP ──────────────────────────────────────────────────────────────

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, PORT)
client.loop_start()

print(f"Publishing encrypted messages to: {TOPIC_PUB}")
print(f"Broker: {BROKER}:{PORT}")
print("─" * 50)

# ─── SEND LOOP ────────────────────────────────────────────────────────────────

try:
    while True:
        user_input = input("Enter message (or 'json' to send sample JSON): ")

        if user_input.strip().lower() == "json":
            # Send a sample JSON payload
            payload = {
                "user": "test_publisher",
                "message": "Hello from publisher!",
                "value": 42,
                "timestamp": time.time()
            }
            token = encrypt_json(payload)
            client.publish(TOPIC_PUB, token)
            print(f"  → Sent encrypted JSON: {payload}\n")
        else:
            # Send plain text (encrypted)
            token = encrypt_text(user_input)
            client.publish(TOPIC_PUB, token)
            print(f"  → Sent encrypted text: {user_input}\n")

except KeyboardInterrupt:
    print("\nStopping publisher...")
    client.loop_stop()
    client.disconnect()
