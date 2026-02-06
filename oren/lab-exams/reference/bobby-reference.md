# Lab Exam Command Cheat Sheet: IoT, MQTT, & GUI

## 1. MQTT (Paho) - The Network Layer

### Basic Setup (Sender & Receiver)
```python
import paho.mqtt.client as mqtt

# 1. Initialize Client (Version 2 is standard now)
# clean_session=False is for Persistent Sessions (receive msgs sent while offline)
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "Client_ID_Unique", clean_session=True)

# 2. Last Will (Must be set BEFORE connect)
# If I crash, the broker publishes this automatically
client.will_set("topic/status", "Unexpected Disconnect", qos=1, retain=True)

# 3. Connect & Loop
client.connect("test.mosquitto.org", 1883, 60)
client.loop_start() # Use loop_forever() if script has no other loop (like GUI)

```

### Callbacks (Receiver)

```python
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected!")
        # Subscribe here to ensure re-subscription on reconnect
        client.subscribe("topic/data", qos=1)

def on_message(client, userdata, msg):
    payload = msg.payload.decode() # Decode binary to string
    topic = msg.topic
    
    # Check for Retained (History) vs Live
    if msg.retain:
        print("[HISTORY] " + payload)
    else:
        print("[LIVE] " + payload)

client.on_connect = on_connect
client.on_message = on_message

```

### Publishing (Sender)

```python
# QoS 0 = Fire & Forget | QoS 1 = At Least Once | QoS 2 = Exactly Once
# Retain=True = "Sticky Note" (New subscribers see this immediately)
info = client.publish("topic/data", "Hello World", qos=1, retain=False)
info.wait_for_publish() # Essential for scripts that exit immediately after sending

```

---

## 2. PyQt5 - The GUI Layer

### Basic Boilerplate (main.py)

```python
import sys
from PyQt5 import QtWidgets, QtCore, QtGui
import main_window_ui # Import your converted .ui file

class MyGUI(QtWidgets.QMainWindow, main_window_ui.Ui_MainWindow):
    # DEFINE SIGNALS HERE (Thread Safety)
    update_signal = QtCore.pyqtSignal(str) 

    def __init__(self):
        super().__init__()
        self.setupUi(self) # Load the design
        
        # Connect Signals
        self.update_signal.connect(self.update_label_safe)
        self.myButton.clicked.connect(self.handle_click)

    def handle_click(self):
        print("Button Clicked")

    def update_label_safe(self, text):
        self.myLabel.setText(text)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyGUI()
    window.show()
    
    # Enable Ctrl+C support
    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)
    
    sys.exit(app.exec_())

```

### Common Widgets

```python
# Label
self.statusLabel.setText("Status: ON")
text = self.statusLabel.text()

# Text Edit (Multi-line)
content = self.msgBox.toPlainText()
self.msgBox.append("New Log Entry") # Adds to bottom

# Line Edit (Single line input)
name = self.inputBox.text()

# Radio Button
if self.radioOption1.isChecked():
    print("Option 1 Selected")

# Checkbox
if self.checkEnable.isChecked():
    print("Enabled")

# Progress Bar
self.progressBar.setValue(75) # 0 to 100

```

### Advanced: QGraphicsView (Images)

*Used when Designer has a `QGraphicsView` widget.*

```python
def display_image(self, graphics_view_widget, pixmap):
    scene = QtWidgets.QGraphicsScene()
    item = QtWidgets.QGraphicsPixmapItem(pixmap)
    scene.addItem(item)
    graphics_view_widget.setScene(scene)
    graphics_view_widget.fitInView(item, QtCore.Qt.KeepAspectRatio)

# Usage:
pix = QtGui.QPixmap("image.jpg")
self.display_image(self.myGraphicsView, pix)

```

---

## 3. Data Processing & Security

### Encryption (Fernet)

```python
from cryptography.fernet import Fernet

KEY = b'Your_Key_Here_Must_Match_On_Both_Sides=' 
cipher = Fernet(KEY)

# Encrypt (String -> Encrypted Bytes)
raw_text = "Secret Message"
token = cipher.encrypt(raw_text.encode('utf-8'))

# Decrypt (Encrypted Bytes -> String)
decrypted_bytes = cipher.decrypt(token)
clean_text = decrypted_bytes.decode('utf-8')

```

### JSON & Base64 (Sending Complex Data)

*Standard pipeline: Image -> Base64 -> JSON -> Encrypt -> MQTT*

```python
import json
import base64

# 1. Image to Base64 String
with open("image.jpg", "rb") as f:
    img_bytes = f.read()
b64_str = base64.b64encode(img_bytes).decode('utf-8')

# 2. Pack JSON
payload = {
    "text": "Here is the photo",
    "image": b64_str,
    "timestamp": time.time()
}
json_str = json.dumps(payload)

# 3. Receiver Unpacking
data = json.loads(json_str)
img_original_bytes = base64.b64decode(data['image'])

# Load bytes into Pixmap (PyQt)
pix = QtGui.QPixmap()
pix.loadFromData(img_original_bytes)

```

---

## 4. Raspberry Pi Hardware & Logic

### GPIOZero (Simple)

```python
from gpiozero import LED, Button

led = LED(17)
btn = Button(27)

led.on()
led.off()
led.toggle()

if btn.is_pressed:
    print("Button Pushed")

```

### OpenCV (Camera)

```python
import cv2
import numpy as np

# 1. Capture Image
cap = cv2.VideoCapture(0)
ret, frame = cap.read() # frame is a numpy array (BGR)

# 2. Convert to Bytes for Sending
_, buffer = cv2.imencode('.jpg', frame)
byte_data = buffer.tobytes()

# 3. Receiving & Decoding (No GUI)
nparr = np.frombuffer(byte_data, np.uint8)
img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

```

---

## 5. Plotting (Matplotlib in PyQt)

### Setup Class

```python
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self):
        fig = Figure()
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

```

### Updating the Plot

```python
# 1. Circular Buffer Logic (Keep last 20 points)
self.data_y = self.data_y[1:]  # Drop oldest
self.data_y.append(new_val)    # Add newest

# 2. Redraw
self.canvas.axes.cla() # Clear old lines
self.canvas.axes.plot(self.data_x, self.data_y, 'r-')
self.canvas.axes.grid(True)
self.canvas.draw()

```

---

## 6. Exam Logic Patterns

### Heartbeat (Dead Man's Switch)

*Turns status RED if no message received for 3 seconds.*

```python
# In __init__
self.timer = QtCore.QTimer()
self.timer.timeout.connect(self.check_pulse)
self.timer.start(1000)
self.last_msg_time = time.time()

# In on_message
self.last_msg_time = time.time() # Reset clock

# Check Function
def check_pulse(self):
    if time.time() - self.last_msg_time > 3.0:
        self.statusLabel.setStyleSheet("background-color: red;")

```