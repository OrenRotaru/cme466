from dataclasses import dataclass, field
from threading import Event
from typing import List, Optional, TYPE_CHECKING

from pydantic import BaseModel
import paho.mqtt.client as paho

if TYPE_CHECKING:
    from pytauri import AppHandle


class Person(BaseModel):
    """Request model for greet command."""
    name: str


class Greeting(BaseModel):
    """Response model for greet command."""
    message: str


class DisplayBoardMessage(BaseModel):
    """Request model for send_to_display_board command."""
    message: str


class SubscribeToMQTTBrokerResponse(BaseModel):
    """Response model for subscribe_to_mqtt_broker command."""
    subscribed: bool


class MqttMessage(BaseModel):
    """A single MQTT message received from the broker."""
    topic: str
    payload: str
    timestamp: str


class GetMqttMessagesResponse(BaseModel):
    """Response model for get_mqtt_messages command."""
    messages: List[MqttMessage]


class ClearMqttMessagesResponse(BaseModel):
    """Response model for clear_mqtt_messages command."""
    cleared: bool


# ============================================================================
# MQTT State Management
# ============================================================================

@dataclass
class MqttState:
    """
    State container for the MQTT client.
    
    PyTauri uses type(state) as the key, so we wrap the client in a dataclass
    to make it injectable into commands via Annotated[MqttState, State()].
    """
    client: paho.Client
    subscribed: bool = False
    connected: bool = False
    # Events for synchronization
    connect_event: Event = field(default_factory=Event)
    subscribe_event: Event = field(default_factory=Event)
    # Store received messages as MqttMessage dicts
    messages: List[MqttMessage] = field(default_factory=list)
    # AppHandle for emitting events to frontend (set after app is built)
    app_handle: Optional["AppHandle"] = None