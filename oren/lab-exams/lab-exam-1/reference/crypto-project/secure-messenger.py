import sys
import json
import paho.mqtt.client as mqtt
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                               QTextEdit, QLineEdit, QPushButton, QLabel)
from PySide6.QtCore import Signal, Slot, QObject
from cryptography.fernet import Fernet

# --- CONFIGURATION ---
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC_SUB = "lab/exam/encrypted_in"
TOPIC_PUB = "lab/exam/encrypted_out"

# Hardcoded key for the exam scenario (In reality, keep this secret)
# This key matches the one in the test script below.
SECRET_KEY = b'8yLwb2yS-b1uY_2u3vj4Q9n6t8s7r1a2b3c4d5e6f7g=' 

class MqttWorker(QObject):
    """
    Handles MQTT connections in a non-blocking way.
    Emits a signal when a message is received so the GUI can update safely.
    """
    message_received = Signal(str)

    def __init__(self):
        super().__init__()
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_message = self.on_message
        self.cipher = Fernet(SECRET_KEY)

    def connect_broker(self):
        try:
            self.client.connect(BROKER, PORT, 60)
            self.client.subscribe(TOPIC_SUB)
            self.client.loop_start() # Run MQTT in background thread
            print(f"Connected to {BROKER}, subscribed to {TOPIC_SUB}")
        except Exception as e:
            print(f"Connection failed: {e}")

    def on_message(self, client, userdata, msg):
        """
        1. Receive payload
        2. Decrypt
        3. Detect format (JSON vs Text)
        4. Emit signal to GUI
        """
        try:
            encrypted_payload = msg.payload
            
            # -- DECRYPTION STEP --
            decrypted_bytes = self.cipher.decrypt(encrypted_payload)
            decrypted_str = decrypted_bytes.decode('utf-8')

            # -- FORMAT CHECK STEP --
            # Try to parse as JSON, otherwise treat as plain text
            try:
                data = json.loads(decrypted_str)
                display_text = f"[JSON] User: {data.get('user', 'Unknown')} | Msg: {data.get('message', '')}"
            except json.JSONDecodeError:
                display_text = f"[TEXT] {decrypted_str}"

            # Send safe string to GUI
            self.message_received.emit(display_text)

        except Exception as e:
            print(f"Decryption Error: {e}")
            self.message_received.emit(f"[ERROR] Could not decrypt message")

    def publish_message(self, text_message):
        """
        Encrypts and publishes a plain text message.
        """
        try:
            # Encrypt
            token = self.cipher.encrypt(text_message.encode('utf-8'))
            # Publish
            self.client.publish(TOPIC_PUB, token)
            print(f"Published encrypted message to {TOPIC_PUB}")
        except Exception as e:
            print(f"Publish Error: {e}")

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = MqttWorker()
        self.init_ui()
        
        # Connect the worker signal to the GUI slot
        self.worker.message_received.connect(self.update_log)
        self.worker.connect_broker()

    def init_ui(self):
        self.setWindowTitle("Secure MQTT Client")
        self.resize(400, 500)
        layout = QVBoxLayout()

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setPlaceholderText("Decrypted messages will appear here...")
        layout.addWidget(QLabel("Received Messages (Decrypted):"))
        layout.addWidget(self.log_display)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type message to encrypt & send...")
        layout.addWidget(QLabel("Send Message:"))
        layout.addWidget(self.input_field)

        self.send_btn = QPushButton("Encrypt & Send")
        self.send_btn.clicked.connect(self.handle_send)
        layout.addWidget(self.send_btn)

        self.setLayout(layout)

    @Slot(str)
    def update_log(self, text):
        self.log_display.append(text)

    def handle_send(self):
        msg = self.input_field.text()
        if msg:
            self.worker.publish_message(msg)
            self.log_display.append(f">> Sent: {msg}")
            self.input_field.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())