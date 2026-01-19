import paho.mqtt.client as paho
import pickle
import time
import threading
import signal
import sys
import pandas as pd
import uuid
from datetime import datetime


public_brokers = [
    {"host": "broker.mqttdashboard.com"},
    {"host": "test.mosquitto.org"},
    {"host": "broker.emqx.io"},
    {"host": "public.cloud.shiftr.io", "username": "public", "password": "public", "protocol": "v311"},
]
port = 1883

# Track all clients for cleanup
clients = []
clients_lock = threading.Lock()

# Store message data: {broker: {iteration: time_taken_ms}}
data_lock = threading.Lock()
message_data = {}

def on_connect(client, userdata, flags, reason_code, properties):
    broker = userdata["broker"]
    print(f"[{broker}] Connected with code {reason_code}.")
    
    # Check if connection was successful before subscribing
    if reason_code.is_failure:
        print(f"[{broker}] Connection failed, disconnecting...")
        client.disconnect()
        return
    
    client.subscribe("jpor/asn2")
    print(f"[{broker}] Subscribed to jpor/asn2. Waiting for messages... (Ctrl+C to stop)")


def on_message(client, userdata, msg):
    broker = userdata["broker"]
    timestampEnd = time.time()
    
    # Parse payload (now contains timestamp and iteration)
    payload = pickle.loads(msg.payload)
    timestampStart = payload["timestamp"]
    iteration = payload["iteration"]
    
    timeTakenMs = (timestampEnd - timestampStart) * 1000  # Convert to milliseconds
    
    # Thread-safe storage by broker and iteration
    with data_lock:
        if broker not in message_data:
            message_data[broker] = {}
        message_data[broker][iteration] = timeTakenMs
    
    print(f"[{broker}] Iteration {iteration} | Time taken: {timeTakenMs:.2f} ms")

def listen_for_messages(broker_config):
    host = broker_config["host"]
    
    # Use MQTTv311 if specified, otherwise MQTTv5
    protocol = paho.MQTTv311 if broker_config.get("protocol") == "v311" else paho.MQTTv5
    client_id = f"sub-{uuid.uuid4().hex[:8]}" if broker_config.get("protocol") == "v311" else ""
    
    client = paho.Client(
        paho.CallbackAPIVersion.VERSION2, client_id=client_id, userdata={"broker": host}, protocol=protocol
    )
    
    # Set credentials if provided
    if "username" in broker_config:
        client.username_pw_set(broker_config["username"], broker_config.get("password"))
    
    with clients_lock:
        clients.append(client)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        print(f"[{host}] Connecting...")
        client.connect(host, port)
        client.loop_forever()
        print(f"[{host}] Disconnected")
    except Exception as e:
        print(f"[{host}] Connection failed: {e}")

def shutdown(signum, frame):
    print("\nShutting down...")
    with clients_lock:
        for client in clients:
            client.disconnect()
    
    # Create and display DataFrame
    with data_lock:
        if message_data:
            # Find all iterations across all brokers
            all_iterations = set()
            for broker_data in message_data.values():
                all_iterations.update(broker_data.keys())
            all_iterations = sorted(all_iterations)
            
            # Build rows for DataFrame
            rows = []
            for broker, iterations in message_data.items():
                row = {"broker": broker}
                times = []
                for i in all_iterations:
                    col_name = f"iteration_{i} (ms)"
                    if i in iterations:
                        row[col_name] = round(iterations[i], 2)
                        times.append(iterations[i])
                    else:
                        row[col_name] = None
                
                # Calculate average
                if times:
                    row["average (ms)"] = round(sum(times) / len(times), 2)
                else:
                    row["average (ms)"] = None
                rows.append(row)
            
            df = pd.DataFrame(rows)
            
            # Sort columns: broker, iteration_1, iteration_2, ..., average
            cols = ["broker"] + [f"iteration_{i} (ms)" for i in all_iterations] + ["average (ms)"]
            df = df[cols]
            
            print("\n" + "="*100)
            print("Timing Results (ms):")
            print("="*100)
            print(df.to_string(index=False))
            
            # Save to CSV
            csv_filename = "subscriber_results.csv"
            df.to_csv(csv_filename, index=False)
            print(f"\nResults saved to {csv_filename}")
        else:
            print("No messages received.")
    
    sys.exit(0)

# Register signal handler for Ctrl+C
signal.signal(signal.SIGINT, shutdown)

# create subscriber threads for each broker
threads = []
for broker in public_brokers:
    t = threading.Thread(target=listen_for_messages, args=(broker,), daemon=True)
    t.start()
    threads.append(t)

# Keep main thread alive to handle signals
for t in threads:
    t.join()