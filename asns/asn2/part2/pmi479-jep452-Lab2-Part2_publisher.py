import paho.mqtt.client as paho
import time
import threading
import pickle
import uuid

# Configuration
ITERATIONS = 10
DELAY_BETWEEN_ITERATIONS = 1  # seconds

# list of public brokers to test
public_brokers = [
    {"host": "broker.mqttdashboard.com"},
    {"host": "test.mosquitto.org"},
    {"host": "broker.emqx.io"},
    {"host": "public.cloud.shiftr.io", "username": "public", "password": "public", "protocol": "v311"},
]
port = 1883


def publish_to_broker(broker_config):
    """Publish timestamp messages to a single broker for all iterations."""
    host = broker_config["host"]
    publish_count = 0
    connected = threading.Event()
    
    def on_connect(client, userdata, flags, reason_code, properties):
        print(f"[{host}] Connected with code {reason_code}")
        if reason_code.is_failure:
            print(f"[{host}] Connection failed: {reason_code}")
        connected.set()
    
    def on_publish(client, userdata, mid, reason_code, properties):
        nonlocal publish_count
        publish_count += 1
    
    def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
        print(f"[{host}] Disconnected")
    
    # Use MQTTv311 if specified, otherwise MQTTv5
    protocol = paho.MQTTv311 if broker_config.get("protocol") == "v311" else paho.MQTTv5
    client_id = f"pub-{uuid.uuid4().hex[:8]}" if broker_config.get("protocol") == "v311" else ""
    
    client = paho.Client(
        paho.CallbackAPIVersion.VERSION2, client_id=client_id, userdata=None, protocol=protocol
    )
    
    # Set credentials if provided
    if "username" in broker_config:
        client.username_pw_set(broker_config["username"], broker_config.get("password"))
    
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    
    try:
        print(f"[{host}] Connecting...")
        client.connect(host, port)
        client.loop_start()
        
        # Wait for connection
        if not connected.wait(timeout=10):
            print(f"[{host}] Connection timeout")
            client.loop_stop()
            return
        
        # Publish ITERATIONS messages
        for iteration in range(1, ITERATIONS + 1):
            timestamp = time.time()
            payload = {"timestamp": timestamp, "iteration": iteration}
            payload_bytes = pickle.dumps(payload)
            result = client.publish("jpor/asn2", payload_bytes, qos=1)
            result.wait_for_publish(timeout=5)
            print(f"[{host}] Published iteration {iteration}/{ITERATIONS}")
            
            if iteration < ITERATIONS:
                time.sleep(DELAY_BETWEEN_ITERATIONS)
        
        print(f"[{host}] All {ITERATIONS} iterations complete")
        client.disconnect()
        client.loop_stop()
    except Exception as e:
        print(f"[{host}] Error: {e}")
        client.loop_stop()


# Run publishers in parallel threads
print(f"Starting {ITERATIONS} iterations for each broker...\n")
threads = []
for broker in public_brokers:
    t = threading.Thread(target=publish_to_broker, args=(broker,))
    t.start()
    threads.append(t)

# Wait for all threads to complete
for t in threads:
    t.join()

print("\nAll publishers finished.")
    


