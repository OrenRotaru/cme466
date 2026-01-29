"""
Main ViewModel for the Smart Parking application.
Exposes properties and slots for QML to interact with.
"""

import json

from PySide6.QtCore import QObject, Property, Signal, Slot, QThread

from config import MQTT_TOPIC_PUBLISH
from models import LogModel
from services import MqttService


class ParkingViewModel(QObject):
    """
    Main ViewModel for the Smart Parking application.
    Exposes properties and slots for QML to interact with.
    """

    # Signals for property changes
    connectionStatusChanged = Signal()
    parkingSpotsChanged = Signal()
    warningLightChanged = Signal()
    displayMessageChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # State
        self._connection_status = "disconnected"
        self._parking_spots = [False, False, False, False, True]  # True = occupied
        self._warning_light = False
        self._display_message = ""

        # Log model
        self._log_model = LogModel(self)

        # MQTT service
        self._mqtt_service = MqttService()
        self._mqtt_thread = QThread()
        self._mqtt_service.moveToThread(self._mqtt_thread)

        # Connect signals
        self._mqtt_service.messageReceived.connect(self._on_mqtt_message)
        self._mqtt_service.connectionStatusChanged.connect(
            self._on_connection_status_changed
        )
        self._mqtt_thread.started.connect(self._mqtt_service.connect_to_broker)

        # Start MQTT thread
        self._mqtt_thread.start()

    # -------------------------------------------------------------------------
    # Properties for QML
    # -------------------------------------------------------------------------

    @Property(str, notify=connectionStatusChanged)
    def connectionStatus(self):
        return self._connection_status

    @Property(list, notify=parkingSpotsChanged)
    def parkingSpots(self):
        return self._parking_spots

    @Property(int, notify=parkingSpotsChanged)
    def availableSpots(self):
        return sum(1 for spot in self._parking_spots if not spot)

    @Property(bool, notify=warningLightChanged)
    def warningLight(self):
        return self._warning_light

    @Property(str, notify=displayMessageChanged)
    def displayMessage(self):
        return self._display_message

    @displayMessage.setter
    def displayMessage(self, value):
        if self._display_message != value:
            self._display_message = value
            self.displayMessageChanged.emit()

    @Property(QObject, constant=True)
    def logModel(self):
        return self._log_model

    # -------------------------------------------------------------------------
    # Slots for QML
    # -------------------------------------------------------------------------

    @Slot(int)
    def toggleSpot(self, index: int):
        """Toggle the occupied state of a parking spot."""
        if 0 <= index < len(self._parking_spots):
            self._parking_spots[index] = not self._parking_spots[index]
            self.parkingSpotsChanged.emit()

    @Slot(int, result=bool)
    def isSpotOccupied(self, index: int) -> bool:
        """Check if a specific parking spot is occupied."""
        if 0 <= index < len(self._parking_spots):
            return self._parking_spots[index]
        return False

    @Slot()
    def setWarningOn(self):
        """Turn the warning light on."""
        if not self._warning_light:
            self._warning_light = True
            self.warningLightChanged.emit()

    @Slot()
    def setWarningOff(self):
        """Turn the warning light off."""
        if self._warning_light:
            self._warning_light = False
            self.warningLightChanged.emit()

    @Slot()
    def clearLogs(self):
        """Clear all log entries."""
        self._log_model.clear_entries()

    @Slot(str)
    def setDisplayMessage(self, message: str):
        """Update the display message text."""
        self.displayMessage = message

    @Slot()
    def sendDisplayMessage(self):
        """Send the current display message to the RPi via MQTT."""
        message = self._display_message.strip()
        if message:
            payload = json.dumps({"command": "display_to_console", "message": message})
            self._mqtt_service.publish(MQTT_TOPIC_PUBLISH, payload)
            self.displayMessage = ""

    # -------------------------------------------------------------------------
    # Internal slots
    # -------------------------------------------------------------------------

    @Slot(str, str)
    def _on_mqtt_message(self, timestamp: str, payload: str):
        """Handle received MQTT messages."""
        self._log_model.add_entry(timestamp, payload)

    @Slot(str)
    def _on_connection_status_changed(self, status: str):
        """Handle connection status changes."""
        self._connection_status = status
        self.connectionStatusChanged.emit()

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def cleanup(self):
        """Clean up resources before exit."""
        self._mqtt_service.stop()
        self._mqtt_thread.quit()
        self._mqtt_thread.wait()
