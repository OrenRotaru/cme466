"""
Smart Parking Tauri App - Python Backend

This module initializes the Tauri app and registers IPC command handlers.
Commands are defined in commands.py
"""

import json
from datetime import datetime

from anyio.from_thread import start_blocking_portal
from pytauri import builder_factory, context_factory, Manager, Emitter
from os import environ

import paho.mqtt.client as paho

# Import commands from the commands module
from tauri_app.commands import commands
from tauri_app.models import MqttState, MqttMessage



if environ.get("PYTAURI_DEBUG_PY") == "1":
    import debugpy  # pyright: ignore[reportMissingTypeStubs]

    debugpy.listen(5678)
    print("Waiting for debugger to attach...")
    # debugpy.wait_for_client()


if environ.get("PYTAURI_DEBUG_RS") == "1":
    import codelldb

    codelldb.debug(host="localhost", port=9552, token="secret")


def create_mqtt_client(mqtt_state: MqttState) -> paho.Client:
    """
    Create and configure the MQTT client with callbacks.
    
    The callbacks update the shared MqttState and signal events
    for synchronization with async commands.
    """
    
    def on_connect(client, userdata, flags, reason_code, properties):
        """Called when connected to the broker."""
        print(f"MQTT Connected with code: {reason_code}")
        mqtt_state.connected = True
        mqtt_state.connect_event.set()
    
    def on_subscribe(client, userdata, mid, reason_codes, properties):
        """Called when subscription is confirmed."""
        print(f"MQTT Subscription confirmed (mid: {mid})")
        mqtt_state.subscribed = True
        mqtt_state.subscribe_event.set()
    
    def on_message(client, userdata, msg):
        """Called when a message is received."""
        # Decode payload bytes to string
        payload_str = msg.payload.decode("utf-8") if isinstance(msg.payload, bytes) else str(msg.payload)
        timestamp = datetime.now().isoformat()
        print(f"MQTT Message received on {msg.topic}: {payload_str}")
        
        message = MqttMessage(
            topic=msg.topic,
            payload=payload_str,
            timestamp=timestamp,
        )
        mqtt_state.messages.append(message)
        
        # Emit event to frontend if app_handle is available
        if mqtt_state.app_handle is not None:
            try:
                # Emit the message as a JSON string event
                Emitter.emit_str(
                    mqtt_state.app_handle,
                    "mqtt-message",
                    json.dumps(message.model_dump()),
                )
            except Exception as e:
                print(f"Failed to emit event: {e}")
    
    def on_disconnect(client, userdata, flags, reason_code, properties):
        """Called when disconnected from the broker."""
        print(f"MQTT Disconnected with code: {reason_code}")
        mqtt_state.connected = False
        mqtt_state.subscribed = False
    
    # Set up callbacks
    mqtt_state.client.on_connect = on_connect
    mqtt_state.client.on_subscribe = on_subscribe
    mqtt_state.client.on_message = on_message
    mqtt_state.client.on_disconnect = on_disconnect
    
    return mqtt_state.client


def main() -> int:
    """
    Main entry point for the Tauri Python backend.
    
    Sets up the async portal and builds the Tauri app with the command handlers.
    """
    # Create MQTT client instance (following the pattern from asn2)
    client = paho.Client(
        paho.CallbackAPIVersion.VERSION2,
        client_id="server-sub",
        userdata=None,
        protocol=paho.MQTTv5,
    )
    
    # Create MQTT state container
    mqtt_state = MqttState(client=client)
    
    # Configure the client with callbacks
    create_mqtt_client(mqtt_state)
    
    with start_blocking_portal("asyncio") as portal:
        app = builder_factory().build(
            context=context_factory(),
            invoke_handler=commands.generate_handler(portal),
        )

        # Register the MQTT state so commands can access it via State injection
        Manager.manage(app, mqtt_state)
        
        # Store the app handle so we can emit events from MQTT callbacks
        mqtt_state.app_handle = app.handle()
        print("MQTT state registered. Ready to accept subscription requests.")

        exit_code = app.run_return()
        
        # Cleanup: disconnect MQTT client on exit
        if mqtt_state.connected:
            print("Disconnecting MQTT client...")
            mqtt_state.client.loop_stop()
            mqtt_state.client.disconnect()
        
        return exit_code