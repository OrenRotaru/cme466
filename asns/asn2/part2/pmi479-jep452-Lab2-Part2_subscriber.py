# Lab 2 - Part 2 Subscriber

import paho.mqtt.client as paho
import pickle
import time
import pandas as pd # to easily save results to a CSV file
import uuid # to generate unique client ids for v311

# Settings to connect to the public brokers.
PUBLIC_BROKERS = [
    {"host": "broker.mqttdashboard.com"},
    {"host": "test.mosquitto.org"},
    {"host": "broker.emqx.io"},
    # Needed to specify an authentication for this broker.
    {"host": "public.cloud.shiftr.io", "username": "public", "password": "public", "protocol": "v311"},
]
PORT = 1883

# Used to store message data
message_data = {}

################################### CALLBACKS #########################################################
def on_connect(client, userdata, flags, reason_code, properties):
    broker = userdata["broker"]
    print(f"[{broker}] Connected with code {reason_code}.")
    if reason_code.is_failure:
        client.disconnect()
        return
    client.subscribe("jpor/asn2")

def on_subscribe(client, userdata, mid, reason_code_list, properties):
    broker = userdata["broker"]
    print(f"[{broker}] Subscribed with code {reason_code_list}.")

def on_message(client, userdata, msg):
    broker = userdata["broker"]
    payload = pickle.loads(msg.payload)
    time_ms = (time.time() - payload["timestamp"]) * 1000
    
    message_data.setdefault(broker, {})[payload["iteration"]] = time_ms
    print(f"[{broker}] Iteration {payload['iteration']} | Time taken: {time_ms:.2f} ms")


def create_client(broker_config):
    """Create and start a client for a broker."""
    host = broker_config["host"]
    protocol = paho.MQTTv311 if broker_config.get("protocol") == "v311" else paho.MQTTv5
    # for v311, we need to specify a client id. Used the uuid package to generate a random
    # unique string for the client id.
    client_id = f"sub-{uuid.uuid4().hex[:8]}" if broker_config.get("protocol") == "v311" else ""
    
    client = paho.Client(paho.CallbackAPIVersion.VERSION2, client_id=client_id, 
                         userdata={"broker": host}, protocol=protocol)
    
    if "username" in broker_config:
        client.username_pw_set(broker_config["username"], broker_config.get("password"))
    
    # Assign callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe = on_subscribe
    
    print(f"[{host}] Connecting...")
    client.connect(host, PORT)
    client.loop_start()  # Runs network loop in background thread
    return client


def save_results():
    """Save collected data to CSV."""
    if not message_data:
        print("No messages received.")
        return
    
    all_iterations = sorted({i for data in message_data.values() for i in data})
    rows = []
    for broker, iterations in message_data.items():
        times = [iterations[i] for i in all_iterations if i in iterations]
        row = {"broker": broker}
        row.update({f"iteration_{i} (ms)": round(iterations.get(i, None), 2) if i in iterations else None 
                    for i in all_iterations})
        row["average (ms)"] = round(sum(times) / len(times), 2) if times else None
        rows.append(row)
    
    df = pd.DataFrame(rows)
    cols = ["broker"] + [f"iteration_{i} (ms)" for i in all_iterations] + ["average (ms)"]
    df[cols].to_csv("subscriber_results.csv", index=False)
    print("\nResults saved to subscriber_results.csv")


################################### MAIN FUNCTION #########################################################
if __name__ == "__main__":
    # create all the clients
    clients = [create_client(broker) for broker in PUBLIC_BROKERS]
    
    try:
        while True:
            # keep the main thread alive, otherwise program will end and kill the other threads
            # prematurely
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        for client in clients:
            client.loop_stop()
            client.disconnect()
        # save the results to a CSV file.
        save_results()