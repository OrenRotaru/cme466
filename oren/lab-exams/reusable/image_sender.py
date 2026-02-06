"""
Image Sender - Explicit control
================================
python image_sender.py photo.jpg
python image_sender.py photo.jpg --no-encrypt
"""

import sys
import time
from mqtt_simple import MQTTHelper

# ─── CONFIG ────────────────────────────────────────────────────────────────────

BROKER = "broker.hivemq.com"
TOPIC = "cme466/exam/image"
KEY = b"B7cOuif_4ztTXpSeeGFt7fnUGCcMdSOPxVF7Ayybwiw="


# ─── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Parse args
    image_path = sys.argv[1] if len(sys.argv) > 1 else "test_image.jpg"
    encrypt = "--no-encrypt" not in sys.argv

    # Create helper
    mqtt = MQTTHelper(
        broker=BROKER,
        pub_topic=TOPIC,
        key=KEY,
    )

    print(f"Sending: {image_path}")
    print(f"Topic: {TOPIC}")
    print(f"Encrypt: {encrypt}")

    mqtt.connect()
    time.sleep(1)

    # Send the image
    mqtt.send_image(path=image_path, encrypt=encrypt)

    time.sleep(1)
    mqtt.disconnect()
