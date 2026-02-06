# ui_app/main_pc.py
import sys, signal, pickle
import paho.mqtt.client as paho
from PySide2.QtWidgets import QApplication, QMainWindow
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile, QObject, Signal, Slot, QTimer

# Configuration Parameters
BROKER = "broker.mqttdashboard.com"
TOPIC_DATA = "jpor/asn3/data"
TOPIC_CMD  = "jpor/asn3/commands"

# Styles for GUI elements
STYLE_OCCUPIED = "background-color: #ffcccc; color: red; font-weight: bold;"
STYLE_EMPTY    = "background-color: #ccffcc; color: green; font-weight: bold;"
STYLE_button_ON   = "background-color: red; color: white; font-weight: bold;"

# Helper class to bridge the MQTT thread and the UI thread
class MqttSignaler(QObject):
    data_received = Signal(dict)

class ParkingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load UI File for the main GUI window
        ui_file = QFile("ui_app/parking.ui")
        if not ui_file.open(QFile.ReadOnly):
            print("Could not open UI file")
            sys.exit(-1)
        
        self.ui = QUiLoader().load(ui_file, self)
        ui_file.close()
        self.ui.show()

        # Setup Signal Bridge
        self.signaler = MqttSignaler()
        self.signaler.data_received.connect(self.update_gui)
        
        # Setup MQTT Client
        self.client = paho.Client(paho.CallbackAPIVersion.VERSION2, protocol=paho.MQTTv5)
        self.client.on_connect = self.on_connect_callback
        self.client.on_message = self.on_message_callback
        
        try:
            self.client.connect(BROKER, 1883)
            self.client.loop_start()
            print("System Ready. Ctrl+C to exit.")
        except Exception as e:
            print(f"Connection Failed: {e}")

        # Connect Buttons to Functions
        self.ui.button_warn_on.clicked.connect(self.button_warn_on_clicked)
        self.ui.button_warn_off.clicked.connect(self.button_warn_off_clicked)
        self.ui.button_send_msg.clicked.connect(self.button_send_msg_clicked)

        # List of Parking Spot Checkbox elements
        self.spots = [
            self.ui.checkbox_spot1,
            self.ui.checkbox_spot2,
            self.ui.checkbox_spot3,
            self.ui.checkbox_spot4,
            self.ui.checkbox_spot5
        ]

    # MQTT Connect Callback
    def on_connect_callback(self, client, userdata, flags, reason_code, properties):
        print(f"Connected: {reason_code}")
        client.subscribe(TOPIC_DATA)

    # MQTT Message Callback
    def on_message_callback(self, client, userdata, msg):
        try:
            # Deserialize data and send to GUI
            data = pickle.loads(msg.payload)
            self.signaler.data_received.emit(data)
        except:
            pass

    # Helper to publish data
    def send_data(self, data):
        payload = pickle.dumps(data)
        self.client.publish(TOPIC_CMD, payload)

    # GUI Update Function
    @Slot(dict)
    def update_gui(self, data):
        # Update Sensor (Directly check and set)
        if "sensor_data" in data:
            self.ui.label_sensor_data.setText(f"Ultrasonic: {data['sensor_data']} cm")

        # Update Parking Spots (Assuming data always exists)
        spot_status_list = data.get("parking_spots", []) # .get to avoid KeyError

        for i in range(len(self.spots)):
            # Only update if we have data for this spot
            if i < len(spot_status_list):

                # Check if occupied and update checkbox state
                is_occupied = (spot_status_list[i] == 1)
                self.spots[i].setChecked(is_occupied)

                # Update text and style
                if is_occupied:
                    self.spots[i].setText(f"{i+1}: Occupied")
                    self.spots[i].setStyleSheet(STYLE_OCCUPIED)
                else:
                    self.spots[i].setText(f"{i+1}: Empty")
                    self.spots[i].setStyleSheet(STYLE_EMPTY)

    # Button Click Handler Functions

    # Warn On Button
    def button_warn_on_clicked(self):
        self.send_data({"command": "WARN_ON"})
        self.ui.button_warn_on.setStyleSheet(STYLE_button_ON)
        self.ui.button_warn_off.setStyleSheet("")

    # Warn Off Button
    def button_warn_off_clicked(self):
        self.send_data({"command": "WARN_OFF"})
        self.ui.button_warn_on.setStyleSheet("")
        self.ui.button_warn_off.setStyleSheet("")

    # Send Message Button
    def button_send_msg_clicked(self):
        text_to_send = self.ui.input_message.text()
        self.send_data({"command": "DISPLAY_MSG", "text": text_to_send})
        self.ui.input_message.clear()

if __name__ == "__main__":

    # Ensure Ctrl+C works to exit the application
    signal.signal(signal.SIGINT, signal.SIG_DFL) # SIG_DFL ensures the program can be interrupted
    app = QApplication(sys.argv)
    window = ParkingApp()
    
    # Timer to keep Python interpreter active for Ctrl+C
    # Periodically switches back to python interpreter to check for signals
    timer = QTimer()
    timer.start(500) 
    
    sys.exit(app.exec_())
