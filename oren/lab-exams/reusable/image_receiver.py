"""
Image Receiver - Explicit control
===================================
python image_receiver.py
"""

import time
from mqtt_simple import MQTTHelper
from cryptography.fernet import Fernet

# ─── CONFIG ────────────────────────────────────────────────────────────────────

BROKER = "broker.hivemq.com"
TOPIC = "cme466/exam/image"
KEY = b"7cOuif_4ztTXpSeeGFt7fnUGCcMdSOPxVF7Ayybwiw="

OUTPUT_FILE = "received_image.jpg"



# ─── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cipher_key = Fernet.generate_key()
    print(cipher_key)
    # # Create helper with key (auto-decrypts incoming messages)
    # mqtt = MQTTHelper(
    #     broker=BROKER,
    #     sub_topic=TOPIC,
    #     key=KEY,
    #     auto_decrypt=False
    # )

    # # YOUR callback - you handle the payload directly
    # def handle_message(topic: str, payload: bytes):
    #     print(f"Received {len(payload)} bytes from {topic}")

    #     decrypt = mqtt.decrypt(payload)

    #     # Save as image - YOU decide this is an image
    #     mqtt.save_image(decrypt, OUTPUT_FILE)
    #     print(f"Saved to {OUTPUT_FILE}")

    # mqtt.on_message = handle_message

    # print(f"Broker: {BROKER}")
    # print(f"Topic: {TOPIC}")
    # print("Waiting for image... (Ctrl+C to exit)")

    # mqtt.connect()

    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     mqtt.disconnect()
