# receiver.py — Receives an encrypted image via MQTT, decrypts it,
#                saves it to a file, and displays it in a PyQt5 GUI.
import sys, signal
import paho.mqtt.client as mqtt
from cryptography.fernet import Fernet
from PyQt5 import QtWidgets, QtCore, QtGui

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883
TOPIC  = "cme466/lab/encrypted_image"

# Shared key — must match the sender's key
# Generate one with:  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"
SECRET_KEY = b"B7cOuif_4ztTXpSeeGFt7fnUGCcMdSOPxVF7Ayybwiw="
cipher = Fernet(SECRET_KEY)

OUTPUT_FILENAME = "received_image.jpg"


# ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────────

def decrypt_image(encrypted_data: bytes) -> bytes:
    """Decrypt Fernet-encrypted bytes → raw image bytes."""
    return cipher.decrypt(encrypted_data)


# ─── GUI ──────────────────────────────────────────────────────────────────────

class ImageReceiver(QtWidgets.QMainWindow):
    """PyQt5 window that subscribes to MQTT, decrypts images, and displays them."""

    # Signal to bridge MQTT thread → GUI thread
    image_received = QtCore.pyqtSignal(bytes)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Encrypted Image Receiver")
        self.resize(640, 520)

        # ── Central widget & layout ──
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Status label
        self.status_label = QtWidgets.QLabel("Waiting for encrypted image...")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Image display label
        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background: #222;")
        layout.addWidget(self.image_label)

        # Connect signal → slot
        self.image_received.connect(self.display_image)

        # ── MQTT setup ──
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        try:
            self.client.connect(BROKER, PORT)
            self.client.loop_start()
            print(f"[MQTT] Connected to {BROKER}:{PORT}")
            print(f"[MQTT] Subscribed to: {TOPIC}")
        except Exception as e:
            print(f"[MQTT] Connection failed: {e}")
            self.status_label.setText(f"Connection failed: {e}")

    # ── MQTT callbacks (background thread — do NOT touch GUI) ────────────────

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"[MQTT] on_connect rc={rc}")
        client.subscribe(TOPIC)

    def on_message(self, client, userdata, msg):
        """Decrypt the image and emit signal to GUI thread."""
        print(f"[MQTT] Received encrypted payload: {len(msg.payload)} bytes")
        try:
            # 1. Decrypt
            image_bytes = decrypt_image(msg.payload)
            print(f"[MQTT] Decrypted image: {len(image_bytes)} bytes")

            # 2. Save to file
            with open(OUTPUT_FILENAME, "wb") as f:
                f.write(image_bytes)
            print(f"[MQTT] Saved image to {OUTPUT_FILENAME}")

            # 3. Emit to GUI thread
            self.image_received.emit(image_bytes)

        except Exception as e:
            print(f"[ERROR] Decryption failed: {e}")

    # ── GUI slot (main thread — safe to update widgets) ──────────────────────

    @QtCore.pyqtSlot(bytes)
    def display_image(self, image_bytes: bytes):
        """Load decrypted image bytes into the QLabel."""
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(image_bytes)

        if pixmap.isNull():
            self.status_label.setText("Error: could not decode image data")
            return

        # Scale to fit the label while keeping aspect ratio
        scaled = pixmap.scaled(
            self.image_label.size(),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)
        self.status_label.setText(
            f"Image received! ({pixmap.width()}x{pixmap.height()}) — saved to {OUTPUT_FILENAME}"
        )

    # ── Cleanup ──────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self.client.loop_stop()
        self.client.disconnect()
        event.accept()


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QtWidgets.QApplication(sys.argv)
    window = ImageReceiver()
    window.show()

    # Keep Python interpreter alive for Ctrl+C
    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(500)

    sys.exit(app.exec_())
