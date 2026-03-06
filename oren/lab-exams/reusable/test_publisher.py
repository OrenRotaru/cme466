"""
Test Publisher Script - Use this to test your MQTTClient and GUI.
=================================================================
Sends various message types (text, JSON, images) to test your receiver.

Usage:
    python test_publisher.py                    # Interactive mode
    python test_publisher.py --text "Hello"     # Send single text
    python test_publisher.py --image photo.jpg  # Send image
    python test_publisher.py --encrypt          # Enable encryption
"""

import sys
import time
import argparse
from pathlib import Path

from mqtt_client import MQTTClient, create_client
from cryptography.fernet import Fernet


# ─── CONFIGURATION ─────────────────────────────────────────────────────────────

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "cme466/exam/in"  # Matches the GUI's subscribe topic

# Same key as the GUI (must match for encryption to work)
SECRET_KEY = b"B7cOuif_4ztTXpSeeGFt7fnUGCcMdSOPxVF7Ayybwiw="


def main():
    parser = argparse.ArgumentParser(description="MQTT Test Publisher")
    parser.add_argument("--text", "-t", type=str, help="Send a text message")
    parser.add_argument("--json", "-j", type=str, help="Send JSON (format: key=value)")
    parser.add_argument("--image", "-i", type=str, help="Send an image file")
    parser.add_argument(
        "--encrypt", "-e", action="store_true", help="Encrypt the message"
    )
    parser.add_argument("--topic", type=str, default=TOPIC, help="Topic to publish to")
    parser.add_argument("--broker", type=str, default=BROKER, help="MQTT broker")
    parser.add_argument(
        "--no-key", action="store_true", help="Don't use encryption key"
    )
    args = parser.parse_args()

    # Create client
    key = None if args.no_key else SECRET_KEY
    client = MQTTClient(
        broker=args.broker,
        port=PORT,
        publish_topic=args.topic,
        encryption_key=key,
    )

    print(f"[TEST] Connecting to {args.broker}...")
    client.connect()
    time.sleep(1)  # Wait for connection

    if not client.is_connected():
        print("[ERROR] Failed to connect!")
        return 1

    print(f"[TEST] Connected! Publishing to: {args.topic}")
    print(f"[TEST] Encryption: {'enabled' if args.encrypt else 'disabled'}")

    try:
        # Single message mode
        if args.text:
            client.publish_text(text=args.text, encrypt=args.encrypt)
            print(f"[SENT] Text: {args.text}")

        elif args.json:
            if "=" in args.json:
                key, value = args.json.split("=", 1)
                data = {key: value}
            else:
                data = {"message": args.json}
            client.publish_json(data=data, encrypt=args.encrypt)
            print(f"[SENT] JSON: {data}")

        elif args.image:
            if not Path(args.image).exists():
                print(f"[ERROR] Image file not found: {args.image}")
                return 1
            client.publish_image(image_path=args.image, encrypt=args.encrypt)
            print(f"[SENT] Image: {args.image}")

        else:
            # Interactive mode
            print("\n=== Interactive Mode ===")
            print("Commands:")
            print("  text <message>     - Send text")
            print("  json <key>=<value> - Send JSON")
            print("  image <path>       - Send image")
            print("  encrypt on/off     - Toggle encryption")
            print("  quit               - Exit")
            print()

            encrypt = args.encrypt

            while True:
                try:
                    line = input(f"[encrypt={'on' if encrypt else 'off'}] > ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nExiting...")
                    break

                if not line:
                    continue

                parts = line.split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd == "quit" or cmd == "exit":
                    break

                elif cmd == "encrypt":
                    encrypt = arg.lower() in ("on", "true", "1", "yes")
                    print(f"[CONFIG] Encryption: {'on' if encrypt else 'off'}")

                elif cmd == "text":
                    if arg:
                        client.publish_text(text=arg, encrypt=encrypt)
                        print(f"[SENT] Text: {arg}")
                    else:
                        print("[ERROR] Usage: text <message>")

                elif cmd == "json":
                    if "=" in arg:
                        k, v = arg.split("=", 1)
                        data = {k: v}
                        client.publish_json(data=data, encrypt=encrypt)
                        print(f"[SENT] JSON: {data}")
                    else:
                        print("[ERROR] Usage: json key=value")

                elif cmd == "image":
                    if arg and Path(arg).exists():
                        client.publish_image(image_path=arg, encrypt=encrypt)
                        print(f"[SENT] Image: {arg}")
                    else:
                        print(f"[ERROR] File not found: {arg}")

                else:
                    print(f"[ERROR] Unknown command: {cmd}")

    finally:
        time.sleep(0.5)  # Let messages send
        client.disconnect()
        print("[TEST] Done!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
