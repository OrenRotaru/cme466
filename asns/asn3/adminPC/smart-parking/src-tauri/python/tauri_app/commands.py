"""
IPC Commands for the Smart Parking app.

Each command decorated with @commands.command() becomes callable from the React frontend
via pyInvoke("command_name", { ...args }).

Request/Response flow:
1. Frontend calls: pyInvoke<ResponseType>("command_name", requestData)
2. Backend receives: async def command_name(body: RequestModel) -> ResponseModel
3. Pydantic handles serialization/deserialization automatically
"""

import json
from typing import Annotated

from pytauri import Commands, State

from tauri_app.models import (
    Person,
    Greeting,
    DisplayBoardMessage,
    SubscribeToMQTTBrokerResponse,
    GetMqttMessagesResponse,
    ClearMqttMessagesResponse,
    MqttState,
)


# MQTT Configuration
MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_PORT = 1883
MQTT_TOPIC_SUBSCRIBE = "jep453-pmi479/asn3/admin"  # Receive sensor data from RPi
MQTT_TOPIC_PUBLISH = "jep453-pmi479/asn3/rpi"      # Send commands to RPi

# Global commands registry - this will be used in __init__.py
commands: Commands = Commands()


# ============================================================================
# Commands
# ============================================================================

@commands.command()
async def greet(body: Person) -> Greeting:
    """
    Greet a person.
    
    Frontend usage:
        const response = await pyInvoke<Greeting>("greet", { name: "John" });
        console.log(response.message);  // "Hello, John! You've been greeted from Python..."
    """
    return Greeting(
        message=f"Hello, {body.name}! You've been greeted from Python!"
    )


# ============================================================================
# MQTT Commands
# ============================================================================

@commands.command()
async def subscribe_to_mqtt_broker(
    mqtt: Annotated[MqttState, State()],
) -> SubscribeToMQTTBrokerResponse:
    """
    Subscribe to the MQTT broker. Returns only after subscription is confirmed.
    
    Frontend usage:
        const response = await pyInvoke<SubscribeToMQTTBrokerResponse>("subscribe_to_mqtt_broker", {});
        console.log(response.subscribed);  // true or false
    """
    # If already subscribed, return immediately
    if mqtt.subscribed:
        print(f"Already subscribed to {MQTT_TOPIC_SUBSCRIBE}")
        return SubscribeToMQTTBrokerResponse(subscribed=True)
    
    # Clear events for fresh subscription attempt
    mqtt.connect_event.clear()
    mqtt.subscribe_event.clear()
    
    try:
        # Connect to the broker if not already connected
        if not mqtt.connected:
            print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
            mqtt.client.connect(MQTT_BROKER, MQTT_PORT)
            mqtt.client.loop_start()
            
            # Wait for connection confirmation (timeout after 10 seconds)
            if not mqtt.connect_event.wait(timeout=10.0):
                print("Connection timeout!")
                return SubscribeToMQTTBrokerResponse(subscribed=False)
        
        # Subscribe to the topic
        print(f"Subscribing to topic: {MQTT_TOPIC_SUBSCRIBE}")
        mqtt.client.subscribe(MQTT_TOPIC_SUBSCRIBE)
        
        # Wait for subscription confirmation (timeout after 10 seconds)
        if not mqtt.subscribe_event.wait(timeout=10.0):
            print("Subscription timeout!")
            return SubscribeToMQTTBrokerResponse(subscribed=False)
        
        print(f"Successfully subscribed to {MQTT_TOPIC_SUBSCRIBE}")
        return SubscribeToMQTTBrokerResponse(subscribed=True)
        
    except Exception as e:
        print(f"MQTT subscription error: {e}")
        return SubscribeToMQTTBrokerResponse(subscribed=False)


@commands.command()
async def get_mqtt_messages(
    mqtt: Annotated[MqttState, State()],
) -> GetMqttMessagesResponse:
    """
    Get all MQTT messages received so far.
    
    Frontend usage:
        const response = await pyInvoke<GetMqttMessagesResponse>("get_mqtt_messages", {});
        console.log(response.messages);
    """
    return GetMqttMessagesResponse(messages=list(mqtt.messages))


@commands.command()
async def clear_mqtt_messages(
    mqtt: Annotated[MqttState, State()],
) -> ClearMqttMessagesResponse:
    """
    Clear all stored MQTT messages.
    
    Frontend usage:
        const response = await pyInvoke<ClearMqttMessagesResponse>("clear_mqtt_messages", {});
        console.log(response.cleared);
    """
    mqtt.messages.clear()
    print("MQTT messages cleared")
    return ClearMqttMessagesResponse(cleared=True)


# ============================================================================
# Display Board Commands
# ============================================================================

@commands.command()
async def send_to_display_board(
    body: DisplayBoardMessage,
    mqtt: Annotated[MqttState, State()],
) -> None:
    """
    Send a message to the display board via MQTT.
    
    Frontend usage:
        await pyInvoke("send_to_display_board", { message: "Hello, world!" });
    """
    # Build the command payload according to the schema
    payload = json.dumps({
        "command": "display_to_console",
        "message": body.message
    })
    
    print(f"Sending message to display board: {body.message}")
    
    # Publish to MQTT topic (RPi listens on this topic)
    if mqtt.connected:
        mqtt.client.publish(MQTT_TOPIC_PUBLISH, payload)
        print(f"Published to {MQTT_TOPIC_PUBLISH}: {payload}")
    else:
        print("Warning: MQTT not connected, message not sent")
    
    return None
