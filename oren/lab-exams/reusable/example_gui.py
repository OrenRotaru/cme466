"""
Example Qt GUI using the reusable MQTTClient class.
====================================================
Demonstrates:
- Sending/receiving text messages (with optional encryption)
- Sending/receiving images (with optional encryption)
- Sending/receiving JSON data
- Real-time display of received messages

Run: python example_gui.py
"""

import sys
import signal
from pathlib import Path

from PySide6.QtWidgets import (
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
    QTabWidget,
    QGroupBox,
    QFormLayout,
    QComboBox,
    QSpinBox,
    QScrollArea,
    QFrame,
    QMessageBox,
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QPixmap

# Import our reusable MQTT client
from mqtt_client import MQTTClient, MQTTMessage, MessageType
from cryptography.fernet import Fernet


# ─── CONFIGURATION (MODIFY FOR YOUR EXAM) ──────────────────────────────────────

DEFAULT_BROKER = "broker.hivemq.com"
DEFAULT_PORT = 1883
DEFAULT_SUB_TOPIC = "cme466/exam/in"
DEFAULT_PUB_TOPIC = "cme466/exam/out"

# Generate a new key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"
DEFAULT_KEY = b"B7cOuif_4ztTXpSeeGFt7fnUGCcMdSOPxVF7Ayybwiw="


class ExampleMQTTGUI(QMainWindow):
    """
    Example GUI demonstrating the MQTTClient class features.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CME466 MQTT Client - Exam Ready")
        self.setMinimumSize(800, 700)

        # Initialize MQTT client (not connected yet)
        self.mqtt_client: MQTTClient = None

        # Store current encryption key
        self.current_key = DEFAULT_KEY

        # Setup UI
        self._setup_ui()

        # Auto-connect on startup (optional, comment out if not desired)
        # self._connect_clicked()

    def _setup_ui(self):
        """Build the user interface."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # ── Connection Settings ──
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QFormLayout(conn_group)

        self.broker_input = QLineEdit(DEFAULT_BROKER)
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(DEFAULT_PORT)

        self.sub_topic_input = QLineEdit(DEFAULT_SUB_TOPIC)
        self.pub_topic_input = QLineEdit(DEFAULT_PUB_TOPIC)

        self.key_input = QLineEdit(DEFAULT_KEY.decode())
        self.key_input.setEchoMode(QLineEdit.Password)
        self.show_key_btn = QPushButton("Show")
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.toggled.connect(self._toggle_key_visibility)

        key_layout = QHBoxLayout()
        key_layout.addWidget(self.key_input)
        key_layout.addWidget(self.show_key_btn)

        self.gen_key_btn = QPushButton("Generate New Key")
        self.gen_key_btn.clicked.connect(self._generate_key)

        conn_layout.addRow("Broker:", self.broker_input)
        conn_layout.addRow("Port:", self.port_input)
        conn_layout.addRow("Subscribe Topic:", self.sub_topic_input)
        conn_layout.addRow("Publish Topic:", self.pub_topic_input)
        conn_layout.addRow("Encryption Key:", key_layout)
        conn_layout.addRow("", self.gen_key_btn)

        # Connect/Disconnect buttons
        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._connect_clicked)
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self._disconnect_clicked)
        self.disconnect_btn.setEnabled(False)

        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")

        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.disconnect_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.status_label)

        conn_layout.addRow(btn_layout)
        main_layout.addWidget(conn_group)

        # ── Tabs for different message types ──
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # Tab 1: Text Messages
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)

        send_text_group = QGroupBox("Send Text Message")
        send_text_layout = QHBoxLayout(send_text_group)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type your message...")
        self.text_input.returnPressed.connect(self._send_text)

        self.encrypt_text_cb = QCheckBox("Encrypt")
        self.encrypt_text_cb.setChecked(True)

        self.send_text_btn = QPushButton("Send Text")
        self.send_text_btn.clicked.connect(self._send_text)

        send_text_layout.addWidget(self.text_input)
        send_text_layout.addWidget(self.encrypt_text_cb)
        send_text_layout.addWidget(self.send_text_btn)
        text_layout.addWidget(send_text_group)

        tabs.addTab(text_tab, "Text")

        # Tab 2: JSON Messages
        json_tab = QWidget()
        json_layout = QVBoxLayout(json_tab)

        send_json_group = QGroupBox("Send JSON Message")
        send_json_form = QFormLayout(send_json_group)

        self.json_key_input = QLineEdit("message")
        self.json_value_input = QLineEdit("Hello from GUI")
        self.encrypt_json_cb = QCheckBox("Encrypt")
        self.encrypt_json_cb.setChecked(True)

        self.send_json_btn = QPushButton("Send JSON")
        self.send_json_btn.clicked.connect(self._send_json)

        send_json_form.addRow("Key:", self.json_key_input)
        send_json_form.addRow("Value:", self.json_value_input)
        send_json_form.addRow("", self.encrypt_json_cb)
        send_json_form.addRow("", self.send_json_btn)
        json_layout.addWidget(send_json_group)

        tabs.addTab(json_tab, "JSON")

        # Tab 3: Image Messages
        image_tab = QWidget()
        image_layout = QVBoxLayout(image_tab)

        # Image send controls
        send_image_group = QGroupBox("Send Image")
        send_image_layout = QVBoxLayout(send_image_group)

        img_path_layout = QHBoxLayout()
        self.image_path_input = QLineEdit()
        self.image_path_input.setPlaceholderText("Select an image file...")
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_image)
        img_path_layout.addWidget(self.image_path_input)
        img_path_layout.addWidget(self.browse_btn)

        img_btn_layout = QHBoxLayout()
        self.encrypt_image_cb = QCheckBox("Encrypt")
        self.encrypt_image_cb.setChecked(True)
        self.send_image_btn = QPushButton("Send Image")
        self.send_image_btn.clicked.connect(self._send_image)
        img_btn_layout.addWidget(self.encrypt_image_cb)
        img_btn_layout.addStretch()
        img_btn_layout.addWidget(self.send_image_btn)

        send_image_layout.addLayout(img_path_layout)
        send_image_layout.addLayout(img_btn_layout)
        image_layout.addWidget(send_image_group)

        # Image receive/display area
        recv_image_group = QGroupBox("Received Image")
        recv_image_layout = QVBoxLayout(recv_image_group)

        self.image_label = QLabel("No image received yet")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet(
            "background-color: #222; border: 1px solid #555;"
        )
        self.image_label.setScaledContents(False)

        self.save_image_btn = QPushButton("Save Received Image")
        self.save_image_btn.clicked.connect(self._save_received_image)
        self.save_image_btn.setEnabled(False)

        recv_image_layout.addWidget(self.image_label)
        recv_image_layout.addWidget(self.save_image_btn)
        image_layout.addWidget(recv_image_group)

        tabs.addTab(image_tab, "Images")

        # ── Message Log ──
        log_group = QGroupBox("Message Log")
        log_layout = QVBoxLayout(log_group)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(200)

        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.log_display.clear)

        log_layout.addWidget(self.log_display)
        log_layout.addWidget(clear_btn)
        main_layout.addWidget(log_group)

        # Store received image bytes for saving
        self._received_image_bytes = None

    # ─── CONNECTION HANDLERS ───────────────────────────────────────────────────

    def _connect_clicked(self):
        """Handle connect button click."""
        broker = self.broker_input.text().strip()
        port = self.port_input.value()
        sub_topic = self.sub_topic_input.text().strip()
        pub_topic = self.pub_topic_input.text().strip()
        key_text = self.key_input.text().strip()

        # Parse encryption key
        try:
            if key_text:
                self.current_key = (
                    key_text.encode() if isinstance(key_text, str) else key_text
                )
            else:
                self.current_key = None
        except Exception as e:
            self._log(f"[ERROR] Invalid key: {e}")
            return

        # Create MQTT client
        self.mqtt_client = MQTTClient(
            broker=broker,
            port=port,
            subscribe_topics=[sub_topic] if sub_topic else [],
            publish_topic=pub_topic,
            encryption_key=self.current_key,
        )

        # Connect Qt signals from MQTT client
        self.mqtt_client.connected.connect(self._on_connected)
        self.mqtt_client.disconnected.connect(self._on_disconnected)
        self.mqtt_client.message_received.connect(self._on_message_received)
        self.mqtt_client.text_received.connect(self._on_text_received)
        self.mqtt_client.json_received.connect(self._on_json_received)
        self.mqtt_client.image_received.connect(self._on_image_received)

        # Connect to broker
        if self.mqtt_client.connect():
            self._log(f"Connecting to {broker}:{port}...")
        else:
            self._log("[ERROR] Failed to initiate connection")

    def _disconnect_clicked(self):
        """Handle disconnect button click."""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
            self.mqtt_client = None

    @Slot()
    def _on_connected(self):
        """Called when MQTT connection established."""
        self.status_label.setText("Status: Connected")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self._log("[CONNECTED] Successfully connected to broker")

    @Slot()
    def _on_disconnected(self):
        """Called when MQTT disconnected."""
        self.status_label.setText("Status: Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self._log("[DISCONNECTED] Disconnected from broker")

    # ─── MESSAGE HANDLERS ──────────────────────────────────────────────────────

    @Slot(object)
    def _on_message_received(self, msg: MQTTMessage):
        """Handle any incoming message."""
        encrypted_str = " (decrypted)" if msg.decrypted else ""
        self._log(f"[{msg.message_type.value.upper()}] {msg.topic}{encrypted_str}")

    @Slot(str, str)
    def _on_text_received(self, topic: str, text: str):
        """Handle incoming text message."""
        self._log(f"  → Text: {text}")

    @Slot(str, dict)
    def _on_json_received(self, topic: str, data: dict):
        """Handle incoming JSON message."""
        self._log(f"  → JSON: {data}")

    @Slot(str, bytes)
    def _on_image_received(self, topic: str, image_bytes: bytes):
        """Handle incoming image message."""
        self._log(f"  → Image received: {len(image_bytes)} bytes")

        # Store for saving later
        self._received_image_bytes = image_bytes
        self.save_image_btn.setEnabled(True)

        # Display image
        pixmap = QPixmap()
        if pixmap.loadFromData(image_bytes):
            scaled = pixmap.scaled(
                self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
        else:
            self.image_label.setText("Error: Could not decode image")

    # ─── SEND HANDLERS ─────────────────────────────────────────────────────────

    def _send_text(self):
        """Send a text message."""
        if not self.mqtt_client or not self.mqtt_client.is_connected():
            self._log("[ERROR] Not connected!")
            return

        text = self.text_input.text().strip()
        if not text:
            return

        encrypt = self.encrypt_text_cb.isChecked()
        self.mqtt_client.publish_text(text=text, encrypt=encrypt)
        self._log(f"[SENT] Text: {text} (encrypted={encrypt})")
        self.text_input.clear()

    def _send_json(self):
        """Send a JSON message."""
        if not self.mqtt_client or not self.mqtt_client.is_connected():
            self._log("[ERROR] Not connected!")
            return

        key = self.json_key_input.text().strip()
        value = self.json_value_input.text().strip()

        if not key:
            return

        data = {key: value}
        encrypt = self.encrypt_json_cb.isChecked()
        self.mqtt_client.publish_json(data=data, encrypt=encrypt)
        self._log(f"[SENT] JSON: {data} (encrypted={encrypt})")

    def _send_image(self):
        """Send an image file."""
        if not self.mqtt_client or not self.mqtt_client.is_connected():
            self._log("[ERROR] Not connected!")
            return

        image_path = self.image_path_input.text().strip()
        if not image_path or not Path(image_path).exists():
            self._log("[ERROR] Invalid image path!")
            return

        encrypt = self.encrypt_image_cb.isChecked()
        try:
            self.mqtt_client.publish_image(image_path=image_path, encrypt=encrypt)
            self._log(f"[SENT] Image: {image_path} (encrypted={encrypt})")
        except Exception as e:
            self._log(f"[ERROR] Failed to send image: {e}")

    # ─── UI HELPERS ────────────────────────────────────────────────────────────

    def _browse_image(self):
        """Open file dialog to select an image."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;All Files (*)",
        )
        if path:
            self.image_path_input.setText(path)

    def _save_received_image(self):
        """Save the received image to a file."""
        if not self._received_image_bytes:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            "received_image.jpg",
            "Images (*.png *.jpg *.jpeg);;All Files (*)",
        )
        if path:
            with open(path, "wb") as f:
                f.write(self._received_image_bytes)
            self._log(f"[SAVED] Image saved to: {path}")

    def _toggle_key_visibility(self, checked: bool):
        """Toggle encryption key visibility."""
        if checked:
            self.key_input.setEchoMode(QLineEdit.Normal)
            self.show_key_btn.setText("Hide")
        else:
            self.key_input.setEchoMode(QLineEdit.Password)
            self.show_key_btn.setText("Show")

    def _generate_key(self):
        """Generate a new Fernet encryption key."""
        key = Fernet.generate_key()
        self.key_input.setText(key.decode())
        self._log(f"[KEY] Generated new key: {key.decode()}")

    def _log(self, message: str):
        """Add a message to the log display."""
        self.log_display.append(message)

    def closeEvent(self, event):
        """Clean up on window close."""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        event.accept()


# ─── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Allow Ctrl+C to close the application
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)

    window = ExampleMQTTGUI()
    window.show()

    # Timer to keep Python interpreter responsive for Ctrl+C
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(500)

    sys.exit(app.exec())
