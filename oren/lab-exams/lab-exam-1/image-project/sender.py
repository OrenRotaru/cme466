# sender.py — Reads an image file, encrypts it, and publishes via MQTT.
#
# Usage:  python sender.py                     (sends "test_image.jpg")
#         python sender.py path/to/photo.png   (sends that file)
import sys, time
import paho.mqtt.client as mqtt
from cryptography.fernet import Fernet

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883
TOPIC  = "cme466/lab/encrypted_image"

# Shared key — must match the receiver's key
SECRET_KEY = b"B7cOuif_4ztTXpSeeGFt7fnUGCcMdSOPxVF7Ayybwiw="
cipher = Fernet(SECRET_KEY)

DEFAULT_IMAGE = "beaver.jpg"


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def encrypt_image(image_bytes: bytes) -> bytes:
    """Encrypt raw image bytes → Fernet token (bytes)."""
    return cipher.encrypt(image_bytes)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Pick image file from command-line arg or default
    image_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IMAGE

    # 1. Read image
    try:
        with open(image_path, "rb") as f:
            raw_bytes = f.read()
        print(f"[FILE] Read {image_path}: {len(raw_bytes)} bytes")
    except FileNotFoundError:
        print(f"Error: file '{image_path}' not found.")
        print(f"Place an image named '{DEFAULT_IMAGE}' in this folder, or pass a path as argument.")
        sys.exit(1)

    # 2. Encrypt
    encrypted = encrypt_image(raw_bytes)
    print(f"[CRYPTO] Encrypted: {len(encrypted)} bytes")

    # 3. Publish via MQTT
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER, PORT)
    client.loop_start()

    info = client.publish(TOPIC, encrypted)
    info.wait_for_publish()
    print(f"[MQTT] Published encrypted image to {TOPIC}")

    time.sleep(1)
    client.loop_stop()
    client.disconnect()
    print("[DONE]")
