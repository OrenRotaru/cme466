"""
Example PyQt5 GUI using MQTTHelper
===================================
Demonstrates how to use mqtt_simple.py in a Qt application.

Features:
- Connect/disconnect
- Send text, JSON, images
- Receive and display messages
- Encryption toggle
- QoS selection

Run: python example_pyqt5_gui.py
"""

import sys
import signal
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QFormLayout,
    QComboBox,
    QSpinBox,
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QPixmap

from mqtt_simple import MQTTHelper


# ─── CONFIGURATION ─────────────────────────────────────────────────────────────

DEFAULT_BROKER = "broker.hivemq.com"
DEFAULT_PORT = 1883
DEFAULT_SUB_TOPIC = "cme466/exam/in"
DEFAULT_PUB_TOPIC = "cme466/exam/out"
DEFAULT_KEY = b"B7cOuif_4ztTXpSeeGFt7fnUGCcMdSOPxVF7Ayybwiw="


# ─── MAIN WINDOW ───────────────────────────────────────────────────────────────


class MainWindow(QMainWindow):
    """
    PyQt5 GUI using MQTTHelper.

    Key concept: MQTT callbacks run in a background thread.
    We use Qt signals to safely update the GUI from the main thread.
    """

    # Signals to bridge MQTT thread -> GUI thread
    message_signal = pyqtSignal(str, bytes)  # topic, payload
    connected_signal = pyqtSignal()
    disconnected_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MQTT Client - PyQt5 Example")
        self.setMinimumSize(600, 700)

        self.mqtt: MQTTHelper = None
        self.current_key = DEFAULT_KEY

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Build the UI."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # ── Connection Settings ──
        conn_group = QGroupBox("Connection")
        conn_layout = QFormLayout(conn_group)

        self.broker_input = QLineEdit(DEFAULT_BROKER)
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(DEFAULT_PORT)

        self.sub_topic_input = QLineEdit(DEFAULT_SUB_TOPIC)
        self.pub_topic_input = QLineEdit(DEFAULT_PUB_TOPIC)
        self.key_input = QLineEdit(DEFAULT_KEY.decode())

        conn_layout.addRow("Broker:", self.broker_input)
        conn_layout.addRow("Port:", self.port_input)
        conn_layout.addRow("Subscribe Topic:", self.sub_topic_input)
        conn_layout.addRow("Publish Topic:", self.pub_topic_input)
        conn_layout.addRow("Encryption Key:", self.key_input)

        # Connect/Disconnect buttons
        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setEnabled(False)
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")

        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.disconnect_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.status_label)
        conn_layout.addRow(btn_layout)

        layout.addWidget(conn_group)

        # ── Send Text ──
        text_group = QGroupBox("Send Text")
        text_layout = QHBoxLayout(text_group)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type message...")
        self.encrypt_cb = QCheckBox("Encrypt")
        self.encrypt_cb.setChecked(True)

        self.qos_combo = QComboBox()
        self.qos_combo.addItems(["QoS 0", "QoS 1", "QoS 2"])

        self.retain_cb = QCheckBox("Retain")
        self.send_text_btn = QPushButton("Send")

        text_layout.addWidget(self.text_input)
        text_layout.addWidget(self.encrypt_cb)
        text_layout.addWidget(self.qos_combo)
        text_layout.addWidget(self.retain_cb)
        text_layout.addWidget(self.send_text_btn)

        layout.addWidget(text_group)

        # ── Send JSON ──
        json_group = QGroupBox("Send JSON")
        json_layout = QHBoxLayout(json_group)

        self.json_key_input = QLineEdit("sensor")
        self.json_key_input.setFixedWidth(100)
        self.json_value_input = QLineEdit("42")
        self.json_value_input.setFixedWidth(100)
        self.send_json_btn = QPushButton("Send JSON")

        json_layout.addWidget(QLabel("Key:"))
        json_layout.addWidget(self.json_key_input)
        json_layout.addWidget(QLabel("Value:"))
        json_layout.addWidget(self.json_value_input)
        json_layout.addStretch()
        json_layout.addWidget(self.send_json_btn)

        layout.addWidget(json_group)

        # ── Send Image ──
        image_group = QGroupBox("Send Image")
        image_layout = QHBoxLayout(image_group)

        self.image_path_input = QLineEdit()
        self.image_path_input.setPlaceholderText("Select image...")
        self.browse_btn = QPushButton("Browse")
        self.send_image_btn = QPushButton("Send Image")

        image_layout.addWidget(self.image_path_input)
        image_layout.addWidget(self.browse_btn)
        image_layout.addWidget(self.send_image_btn)

        layout.addWidget(image_group)

        # ── Received Image Display ──
        recv_image_group = QGroupBox("Received Image")
        recv_image_layout = QVBoxLayout(recv_image_group)

        self.image_label = QLabel("No image received")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(200)
        self.image_label.setStyleSheet("background: #222; border: 1px solid #555;")

        recv_image_layout.addWidget(self.image_label)
        layout.addWidget(recv_image_group)

        # ── Message Log ──
        log_group = QGroupBox("Message Log")
        log_layout = QVBoxLayout(log_group)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(150)

        self.clear_btn = QPushButton("Clear Log")
        log_layout.addWidget(self.log_display)
        log_layout.addWidget(self.clear_btn)

        layout.addWidget(log_group)

    def _connect_signals(self):
        """Connect Qt signals to slots."""
        # Button clicks
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        self.disconnect_btn.clicked.connect(self._on_disconnect_clicked)
        self.send_text_btn.clicked.connect(self._on_send_text)
        self.send_json_btn.clicked.connect(self._on_send_json)
        self.browse_btn.clicked.connect(self._on_browse)
        self.send_image_btn.clicked.connect(self._on_send_image)
        self.clear_btn.clicked.connect(self.log_display.clear)
        self.text_input.returnPressed.connect(self._on_send_text)

        # MQTT thread -> GUI thread signals
        self.message_signal.connect(self._on_message_received)
        self.connected_signal.connect(self._on_connected)
        self.disconnected_signal.connect(self._on_disconnected)

    # ─── CONNECTION ────────────────────────────────────────────────────────────

    def _on_connect_clicked(self):
        """Handle connect button."""
        broker = self.broker_input.text().strip()
        port = self.port_input.value()
        sub_topic = self.sub_topic_input.text().strip()
        pub_topic = self.pub_topic_input.text().strip()
        key_text = self.key_input.text().strip()

        # Parse key
        self.current_key = key_text.encode() if key_text else None

        # Create MQTTHelper
        self.mqtt = MQTTHelper(
            broker=broker,
            port=port,
            sub_topic=sub_topic,
            pub_topic=pub_topic,
            key=self.current_key,
            auto_decrypt=True,
            sub_qos=1,
        )

        # Set callbacks - these emit signals to update GUI safely
        self.mqtt.on_message = lambda t, p: self.message_signal.emit(t, p)
        self.mqtt.on_connect = lambda: self.connected_signal.emit()
        self.mqtt.on_disconnect = lambda: self.disconnected_signal.emit()

        # Connect
        self.mqtt.connect()
        self._log("Connecting...")

    def _on_disconnect_clicked(self):
        """Handle disconnect button."""
        if self.mqtt:
            self.mqtt.disconnect()
            self.mqtt = None

    @pyqtSlot()
    def _on_connected(self):
        """Called when MQTT connected (from signal)."""
        self.status_label.setText("Connected")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self._log("Connected!")

    @pyqtSlot()
    def _on_disconnected(self):
        """Called when MQTT disconnected (from signal)."""
        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self._log("Disconnected")

    # ─── RECEIVING MESSAGES ────────────────────────────────────────────────────

    @pyqtSlot(str, bytes)
    def _on_message_received(self, topic: str, payload: bytes):
        """
        Handle received message (called from signal, safe for GUI).
        YOU decide how to handle the payload here.
        """
        self._log(f"[RECV] {topic}: {len(payload)} bytes")

        # Try to parse as text
        try:
            text = self.mqtt.parse_text(payload)
            self._log(f"  -> Text: {text}")
            return
        except:
            pass

        # Try to parse as JSON
        try:
            data = self.mqtt.parse_json(payload)
            self._log(f"  -> JSON: {data}")
            return
        except:
            pass

        # Assume it's an image - display it
        self._display_image(payload)
        self._log(f"  -> Image displayed")

    def _display_image(self, image_bytes: bytes):
        """Display image bytes in the image label."""
        pixmap = QPixmap()
        if pixmap.loadFromData(image_bytes):
            scaled = pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)
        else:
            self.image_label.setText("Could not decode image")

    # ─── SENDING MESSAGES ──────────────────────────────────────────────────────

    def _on_send_text(self):
        """Send text message."""
        if not self.mqtt or not self.mqtt.is_connected():
            self._log("[ERROR] Not connected!")
            return

        text = self.text_input.text().strip()
        if not text:
            return

        encrypt = self.encrypt_cb.isChecked()
        qos = self.qos_combo.currentIndex()
        retain = self.retain_cb.isChecked()

        self.mqtt.send_text(text, encrypt=encrypt, qos=qos, retain=retain)
        self._log(f"[SENT] Text: {text}")
        self.text_input.clear()

    def _on_send_json(self):
        """Send JSON message."""
        if not self.mqtt or not self.mqtt.is_connected():
            self._log("[ERROR] Not connected!")
            return

        key = self.json_key_input.text().strip()
        value = self.json_value_input.text().strip()

        # Try to convert value to number
        try:
            value = float(value)
            if value.is_integer():
                value = int(value)
        except:
            pass

        data = {key: value}
        encrypt = self.encrypt_cb.isChecked()
        qos = self.qos_combo.currentIndex()

        self.mqtt.send_json(data, encrypt=encrypt, qos=qos)
        self._log(f"[SENT] JSON: {data}")

    def _on_browse(self):
        """Open file dialog to select image."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp);;All Files (*)",
        )
        if path:
            self.image_path_input.setText(path)

    def _on_send_image(self):
        """Send image file."""
        if not self.mqtt or not self.mqtt.is_connected():
            self._log("[ERROR] Not connected!")
            return

        path = self.image_path_input.text().strip()
        if not path or not Path(path).exists():
            self._log("[ERROR] Invalid image path!")
            return

        encrypt = self.encrypt_cb.isChecked()
        qos = self.qos_combo.currentIndex()

        self.mqtt.send_image(path=path, encrypt=encrypt, qos=qos)
        self._log(f"[SENT] Image: {path}")

    # ─── HELPERS ───────────────────────────────────────────────────────────────

    def _log(self, message: str):
        """Add message to log display."""
        self.log_display.append(message)

    def closeEvent(self, event):
        """Clean up on window close."""
        if self.mqtt:
            self.mqtt.disconnect()
        event.accept()


# ─── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Allow Ctrl+C to close
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # Timer to keep Python responsive for Ctrl+C
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(500)

    sys.exit(app.exec_())
