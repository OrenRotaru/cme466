# main.py — Lab Exam Boilerplate
# MQTT Subscriber + Publisher with Fernet Encryption, PyQt5 GUI
import sys, signal, json, time
import paho.mqtt.client as mqtt
from cryptography.fernet import Fernet
from PyQt5 import QtWidgets, QtCore

# Import the generated UI class (from mainwindow.ui -> mainwindow.py)
from mainwindow import Ui_MainWindow

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883

TOPIC_SUB = "cme466/lab/encrypted_in"   # Topic we SUBSCRIBE to (receive)
TOPIC_PUB = "cme466/lab/encrypted_out"  # Topic we PUBLISH to (send)

# Shared Fernet key — must match on both publisher & subscriber
# Generate a new one with:  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"
SECRET_KEY = Fernet.generate_key()       # <-- replace with a fixed key for real exam
cipher = Fernet(SECRET_KEY)

print(f"[KEY] Using key: {SECRET_KEY.decode()}")
print(f"      Copy this into publisher.py so both sides match.\n")

# ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────────

def encrypt_message(plain_text: str) -> bytes:
    """Encrypt a plain-text string → Fernet token (bytes)."""
    return cipher.encrypt(plain_text.encode("utf-8"))

def decrypt_message(token: bytes) -> str:
    """Decrypt a Fernet token (bytes) → plain-text string."""
    return cipher.decrypt(token).decode("utf-8")

def encrypt_json(data: dict) -> bytes:
    """Serialize a dict to JSON, then encrypt."""
    json_str = json.dumps(data)
    return encrypt_message(json_str)

def decrypt_json(token: bytes) -> dict:
    """Decrypt a Fernet token, then parse the JSON inside."""
    json_str = decrypt_message(token)
    return json.loads(json_str)


# ─── MAIN GUI APPLICATION ─────────────────────────────────────────────────────

class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    """
    Inherits from QMainWindow AND Ui_MainWindow.
    Signals defined at the CLASS level (required by PyQt5).
    """
    # Signal bridge — MQTT callback (background thread) → GUI (main thread)
    update_signal = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setupUi(self)               # Build the UI from the generated file
        self.setWindowTitle("Lab Exam — Encrypted MQTT")

        # Connect signal → slot
        self.update_signal.connect(self.on_data_received)

        # Connect buttons
        self.pushButton.clicked.connect(self.pushButton_clicked)
        self.pushButton_2.clicked.connect(self.pushButton_2_clicked)

        # ── MQTT setup ────────────────────────────────────
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.mqtt_on_connect
        self.client.on_message = self.mqtt_on_message

        try:
            self.client.connect(BROKER, PORT)
            self.client.loop_start()           # Non-blocking background loop
            print(f"[MQTT] Connected to {BROKER}:{PORT}")
        except Exception as e:
            print(f"[MQTT] Connection failed: {e}")

    # ── MQTT Callbacks (run on MQTT thread — do NOT touch GUI here) ──────────

    def mqtt_on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"[MQTT] on_connect rc={rc}")
        client.subscribe(TOPIC_SUB)
        print(f"[MQTT] Subscribed to: {TOPIC_SUB}")

    def mqtt_on_message(self, client, userdata, msg):
        """
        Runs on the MQTT background thread.
        Decrypt → emit signal so the GUI thread can safely update widgets.
        """
        try:
            decrypted = decrypt_message(msg.payload)

            # Try to interpret as JSON, fall back to plain text
            try:
                data = json.loads(decrypted)
                display = f"[JSON] {data}"
            except json.JSONDecodeError:
                display = f"[TEXT] {decrypted}"

            # Emit to GUI thread
            self.update_signal.emit(display)

        except Exception as e:
            self.update_signal.emit(f"[ERROR] Decryption failed: {e}")

    # ── Slot that safely updates the GUI ─────────────────────────────────────

    @QtCore.pyqtSlot(str)
    def on_data_received(self, text):
        """Called on the main/GUI thread — safe to update widgets here."""
        print(f">> {text}")
        # Example: self.ui.someLabel.setText(text)

    # ── Publishing helpers ───────────────────────────────────────────────────

    def publish_encrypted_text(self, plain_text):
        """Encrypt a string and publish to TOPIC_PUB."""
        token = encrypt_message(plain_text)
        self.client.publish(TOPIC_PUB, token)
        print(f"[PUB] Sent encrypted text to {TOPIC_PUB}")

    def publish_encrypted_json(self, data: dict):
        """Encrypt a dict (as JSON) and publish to TOPIC_PUB."""
        token = encrypt_json(data)
        self.client.publish(TOPIC_PUB, token)
        print(f"[PUB] Sent encrypted JSON to {TOPIC_PUB}")

    # ── Button callbacks ─────────────────────────────────────────────────────

    def pushButton_clicked(self):
        """Example: publish an encrypted message when button is clicked."""
        self.publish_encrypted_text("Hello from the GUI!")

    def pushButton_2_clicked(self):
        self.client.loop_stop()
        self.client.disconnect()
        sys.exit(0)


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)   # Allow Ctrl+C

    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()

    # Timer keeps the Python interpreter alive for Ctrl+C
    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(500)

    sys.exit(app.exec_())                            # PyQt5 uses exec_()
