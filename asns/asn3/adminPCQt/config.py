"""
Configuration constants for the Smart Parking Admin application.
"""

# =============================================================================
# MQTT Configuration
# =============================================================================
MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_PORT = 1883
MQTT_TOPIC_SUBSCRIBE = "jep453-pmi479/asn3/admin"  # Receive sensor data from RPi
MQTT_TOPIC_PUBLISH = "jep453-pmi479/asn3/rpi"      # Send commands to RPi
