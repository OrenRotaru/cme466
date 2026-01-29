# Smart Parking Admin PC (Qt/PySide6)

A Qt-based desktop application for managing a smart parking system. This application connects to an MQTT broker to receive sensor data from an RPi and send commands to it.

## Features

- **Parking Spot Status**: Display 5 parking spots with real-time occupied/available status
- **Connection Status**: Visual indicator showing MQTT connection state (disconnected/connecting/connected/error)
- **Warning Light Control**: Toggle warning light on/off
- **Sensor Log Console**: Real-time display of MQTT messages with timestamps and auto-scroll
- **Display Board Messages**: Send custom messages to the RPi display board via MQTT

## Requirements

- Python 3.13+
- PySide6 (Qt for Python)
- paho-mqtt
- pydantic

## Installation

Using `uv` (recommended):

```bash
cd asns/asn3/adminPCQt
uv sync
```

Or using pip:

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
uv run python main.py
```

Or directly:

```bash
python main.py
```

## MQTT Configuration

The application connects to the following MQTT broker:

- **Broker**: `broker.mqttdashboard.com`
- **Port**: `1883`
- **Subscribe Topic**: `jep453-pmi479/asn3/admin` (receives sensor data from RPi)
- **Publish Topic**: `jep453-pmi479/asn3/rpi` (sends commands to RPi)

## Architecture

### Python Backend (`main.py`)

- **`ParkingController`**: Main QObject controller exposing properties and slots to QML
- **`MqttWorker`**: Runs MQTT client in a separate thread, emits signals for messages and connection status
- **`LogModel`**: QAbstractListModel for displaying log entries in QML ListView

### QML Frontend (`Main.qml`)

- Declarative UI using Qt Quick and Qt Quick Controls
- Modern dark theme with accent colors
- Responsive layout using ColumnLayout and RowLayout

## Project Structure

```
adminPCQt/
├── main.py          # Python backend (controller, MQTT, models)
├── Main.qml         # QML frontend (UI)
├── pyproject.toml   # Project dependencies
├── README.md        # This file
└── uv.lock          # Dependency lock file
```
