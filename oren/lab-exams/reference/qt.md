# Lab Exam Reference: Qt GUI (PySide6 vs PySide2)

## 1. The Boilerplate Code
The main difference is the import names and the execution command (`exec` vs `exec_`).

### **PySide6 (Qt 6) - Recommended**
```python
import sys
from PySide6.QtWidgets import QApplication, QWidget

app = QApplication(sys.argv)

window = QWidget()
window.show()

sys.exit(app.exec()) # Notice: .exec()


PySide2 (Qt 5)
```python
import sys
from PySide2.QtWidgets import QApplication, QWidget

app = QApplication(sys.argv)

window = QWidget()
window.show()

sys.exit(app.exec_()) # Notice: .exec_() (underscore because exec was a keyword in Py2)
```

4. Signals & Slots (Crucial for MQTT)

NEVER update the GUI directly from an MQTT callback. It will crash. Use Signals.

from PySide6.QtCore import QObject, Signal, Slot

# 1. Define the Signal in your Worker class
class MqttWorker(QObject):
    message_received = Signal(str) # Define signal that carries a string

    def on_message(self, client, userdata, msg):
        # 2. Emit the signal with data
        self.message_received.emit(msg.payload.decode())

# 3. Connect in your Main Window
class MainWindow(QWidget):
    def __init__(self):
        self.worker = MqttWorker()
        # Connect signal to a UI function
        self.worker.message_received.connect(self.update_gui)

    # 4. Define the Slot (The function that updates UI)
    @Slot(str)
    def update_gui(self, message):
        self.text_box.append(message)

5. Displaying an Image (from Byte Array)

If you receive an encrypted image via MQTT, here is how to show it in a QLabel.

```python
from PySide6.QtGui import QPixmap, QImage

def display_image(self, byte_data):
    # 1. Create QImage from bytes
    image = QImage.fromData(byte_data)
    
    # 2. Convert to Pixmap
    pixmap = QPixmap.fromImage(image)
    
    # 3. Set to Label
    self.image_label.setPixmap(pixmap)
    self.image_label.setScaledContents(True) # Fit to window
```

### **Full Example: Converting .ui to Python (The "Safe" Way)**
If you prefer not to load the `.ui` file dynamically and want to see the Python code generated from it (useful for debugging):

**Command Line:**
* **PySide6:** `pyside6-uic form.ui -o ui_form.py`
* **PySide2:** `pyside2-uic form.ui -o ui_form.py`

**Usage in Script:**
```python
import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from ui_form import Ui_MainWindow  # Import the generated class

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self) # This builds the UI widgets

        # Access widgets via self.ui
        self.ui.pushButton.clicked.connect(self.clicked_button)

    def clicked_button(self):
        print("Button was clicked!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```


How to Use the Converted File

The generated file (e.g., ui_your_file.py) contains a Python class (usually named Ui_MainWindow or Ui_Form). You simply import this class and set it up in your main script.

This code works for BOTH PySide6 and PySide2:

```python
import sys
# CHANGE THIS IMPORT depending on your version:
from PySide6.QtWidgets import QApplication, QMainWindow 
# from PySide2.QtWidgets import QApplication, QMainWindow

# IMPORT THE CONVERTED FILE
from ui_your_file import Ui_MainWindow 

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        
        # 1. Create an instance of the UI class
        self.ui = Ui_MainWindow()
        
        # 2. Setup the UI (connects all the widgets to this window)
        self.ui.setupUi(self)

        # 3. Access widgets using "self.ui.widgetName"
        # Example: Connect a button named "sendButton"
        self.ui.sendButton.clicked.connect(self.handle_click)

    def handle_click(self):
        # Example: Get text from a lineEdit named "inputField"
        text = self.ui.inputField.text()
        print(f"User typed: {text}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```