import time
from mqtt_simple import MQTTHelper
from cryptography.fernet import Fernet

BROKER = "test.mosquitto.org"
MSG_TOPIC = "cme466_group1_mess"
CIPHER_TOPIC = "cme466_group1_key"

KEY = b'CeEvYpk0j71pOuK5Cc5snyYK8v2mxN-ZwtLdOWjiPW0='
MESSAGE = "gAAAAABphmb1MKaESfkz7JwCw_Ba_GjCTzxMRg5fktKbYNMfP8pEug3K-vW8jFZDqiNtTKTGtl0z7hOl2sMz8iuOHpraAR-GEJdEulTFvlM9lmhf-kHbJqmeyVkoJgGMvPEJol1wW3aMSSTJzm9KOQ4zbHOD7khzOH5vnT1APepLJ_z-gabTluCqbvayNfEffeZ6hqqJkfVjUnzn4zPnw6i2_PuhcTKXit-Jj0Vsbg6VThnn18Pk9tQyZwEby453LFFSc9jcritEByLE7GJH85EFlMcRWApwcbg0JmKKp2ftBQDdbPHOmhcPI3ey7K7WqhjjnuJ6T-zmI2r3V6YoTIj2dTjqGSqI3hfppw_cG9TeI0u1QFZYbcYlciETkhq-Afv38QlvRIoe-R8wRIuNz2KvokptYSEoIUJmSfiuUSnE4ImaV9KMDhE="


if __name__ == "__main__":
    cipher = Fernet(KEY)
    print(cipher)

    mqtt = MQTTHelper(broker=BROKER, 
    sub_topic=MSG_TOPIC, 
    auto_decrypt=False, key=KEY)

    def handle_message(topic: str, payload: bytes):
        print(f"Received {len(payload)} bytes from {topic}")
        print(payload)

        payload_str = payload.decode("utf-8")
        if payload_str.startswith("b'") and payload_str.endswith("'"):
            payload_str = payload_str[2:-1]
        actual_payload = payload_str.encode("utf-8")

        out_message = mqtt.decrypt(actual_payload)
        # out_message = payload
        print(mqtt.parse_text(out_message))

    mqtt.on_message = handle_message

    print(f"Broker: {BROKER}")
    print(f"Topic: {CIPHER_TOPIC}")
    print("Waiting for cipher")

    mqtt.connect()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        mqtt.disconnect()
