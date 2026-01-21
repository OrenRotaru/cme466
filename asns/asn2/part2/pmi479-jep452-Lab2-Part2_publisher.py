import paho.mqtt.client as paho
import time
import threading
import pickle
import uuid

# Configuration
ITERATIONS = 10
DELAY_BETWEEN_ITERATIONS = 1  # seconds

# List of public brokers to test
PUBLIC_BROKERS = [
    {"host": "broker.mqttdashboard.com"},
    {"host": "test.mosquitto.org"},
    {"host": "broker.emqx.io"},
    # Needed to specify an authentication for this broker.
    {"host": "public.cloud.shiftr.io", "username": "public", "password": "public", "protocol": "v311"},
]
PORT = 1883


################################### CALLBACKS #########################################################
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"[{userdata['broker']}] Connected with code {reason_code}")
    userdata["connected"].set()


################################### PUBLISH FUNCTION #########################################################
def publish_to_broker(broker_config):
    """Publish timestamp messages to a single broker for all iterations."""
    host = broker_config["host"]
    connected = threading.Event() # used to signal when the connection is established
    
    # Use MQTTv311 if specified, otherwise MQTTv5
    protocol = paho.MQTTv311 if broker_config.get("protocol") == "v311" else paho.MQTTv5

    # for v311, we need to specify a client id
    client_id = f"pub-{uuid.uuid4().hex[:8]}" if broker_config.get("protocol") == "v311" else ""
    
    client = paho.Client(paho.CallbackAPIVersion.VERSION2, client_id=client_id, 
                         userdata={"broker": host, "connected": connected}, protocol=protocol)
    
    if "username" in broker_config:
        client.username_pw_set(broker_config["username"], broker_config.get("password"))
    
    client.on_connect = on_connect
    
    try:
        print(f"[{host}] Connecting...")
        client.connect(host, PORT)
        client.loop_start()
        
        # wait for the connected event, but setting a timeout of 10 seconds
        if not connected.wait(timeout=10):
            print(f"[{host}] Connection timeout")
            client.loop_stop()
            client.disconnect()
            return
        
        # Publish all iterations
        for iteration in range(1, ITERATIONS + 1):
            payload = pickle.dumps({"timestamp": time.time(), "iteration": iteration})
            client.publish("jpor/asn2", payload, qos=0).wait_for_publish(timeout=5)
            print(f"[{host}] Published iteration {iteration}/{ITERATIONS}")
        
        print(f"[{host}] All {ITERATIONS} iterations complete")
    except Exception as e:
        print(f"[{host}] Error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()


################################### MAIN FUNCTION #########################################################
if __name__ == "__main__":
    print(f"Starting {ITERATIONS} iterations for each broker...\n")
    
    # Run publishers in parallel threads
    threads = [threading.Thread(target=publish_to_broker, args=(broker,)) for broker in PUBLIC_BROKERS]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    print("All publishers finished.")
