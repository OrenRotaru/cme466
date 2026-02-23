import sys
import signal
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QDialog, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5 import uic

from mqtt_simple import MQTTHelper


BROKER = "test.mosquitto.org"
SUB_TOPIC = "cme466_lab_exam_pmi479"
PUB_TOPIC = "cme466_lab_exam_pmi479"

DEFAULT_IMAGE = "default.jpg"
USASK_IMAGE = "usask.jpg"


class PictureDialog(QDialog):

    message_signal = pyqtSignal(str, bytes)  # topic, payload

    def __init__(self):
        super().__init__()

        ui_path = Path(__file__).parent / "picture.ui"
        uic.loadUi(ui_path, self)

        self.image_label = self.findChild(QLabel, "imageLabel")
        self.status_label = self.findChild(QLabel, "statusLabel")

        self.message_signal.connect(self._on_message_received)

        self._load_image(DEFAULT_IMAGE)

        # Setup MQTT
        self.mqtt = MQTTHelper(
            broker=BROKER,
            sub_topic=SUB_TOPIC,
            pub_topic=PUB_TOPIC,
            auto_decrypt=False,
        )

        self.mqtt.on_message = lambda t, p: self.message_signal.emit(t, p)
        self.mqtt.connect()

        self.status_label.setText("Connected - Waiting for messages...")

    def _load_image(self, image_name: str):
        """Load and display an image, scaled to 800x600."""
        try:
            image_path = Path(__file__).parent / image_name
            pixmap = QPixmap(str(image_path))

            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    800, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled)
                print(f"Loaded image: {image_name}")
            else:
                self.status_label.setText(f"Error: Could not load {image_name}")
                print(f"Error: Could not load {image_name}")
        except Exception as e:
            self.status_label.setText(f"Error loading {image_name}: {e}")
            print(f"Error loading {image_name}: {e}")

    @pyqtSlot(str, bytes)
    def _on_message_received(self, topic: str, payload: bytes):
        """
        Handle received message (called from signal, safe for GUI).
        """
        try:
            message = payload.decode("utf-8").strip()
            print(f"[RECV] {topic}: '{message}'")

            msg_lower = message.lower()

            if msg_lower == "usask":
                self._load_image(USASK_IMAGE)
                self.mqtt.send_text("Be What the World Needs!")
                self.status_label.setText("Sent: Be What the World Needs!")
                print("Sent ack: Be What the World Needs!")

            elif msg_lower == "default":
                self._load_image(DEFAULT_IMAGE)
                self.mqtt.send_text("Have a great weekend!")
                self.status_label.setText("Sent: Have a great weekend!")
                print("Sent ack: Have a great weekend!")

            else:
                print(f"Unknown command: {message}")
                self.status_label.setText(f"Unknown command: {message}")

        except Exception as e:
            print(f"Error handling message: {e}")
            self.status_label.setText(f"Error: {e}")

    def closeEvent(self, event):
        """Clean up on window close."""
        if self.mqtt:
            self.mqtt.disconnect()
        event.accept()



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)

    window = PictureDialog()
    window.show()

    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(500)

    sys.exit(app.exec_())
