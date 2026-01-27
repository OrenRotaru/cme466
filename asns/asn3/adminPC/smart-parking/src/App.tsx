import { useState, useRef, useEffect } from "react";
import { pyInvoke } from "tauri-plugin-pytauri-api";
import { listen, UnlistenFn } from "@tauri-apps/api/event";
import "./App.css";

// Types for MQTT responses
interface MqttMessage {
  topic: string;
  payload: string;
  timestamp: string;
}

interface SubscribeResponse {
  subscribed: boolean;
}

interface LogEntry {
  id: number;
  timestamp: string;
  message: string;
}

type ConnectionStatus = "disconnected" | "connecting" | "connected" | "error";

function App() {
  const [parkingSpots, setParkingSpots] = useState<boolean[]>([
    false,
    false,
    false,
    false,
    true,
  ]);

  const [warningLight, setWarningLight] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [displayMessage, setDisplayMessage] = useState("");
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("disconnected");
  
  const logEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // Connect to MQTT broker on app launch
  useEffect(() => {
    const connectToMqtt = async () => {
      setConnectionStatus("connecting");
      try {
        const response = await pyInvoke<SubscribeResponse>("subscribe_to_mqtt_broker", {});
        if (response.subscribed) {
          setConnectionStatus("connected");
        } else {
          setConnectionStatus("error");
        }
      } catch (error) {
        console.error("Failed to connect to MQTT:", error);
        setConnectionStatus("error");
      }
    };

    connectToMqtt();
  }, []);

  // Listen for MQTT messages via Tauri events (instead of polling)
  useEffect(() => {
    let unlisten: UnlistenFn | undefined;

    const setupListener = async () => {
      unlisten = await listen<MqttMessage>("mqtt-message", (event) => {
        const msg = event.payload;
        const logEntry: LogEntry = {
          id: Date.now(),
          timestamp: new Date(msg.timestamp).toLocaleTimeString(),
          message: msg.payload,
        };
        setLogs((prev) => [...prev, logEntry]);
      });
    };

    setupListener();

    // Cleanup listener on unmount
    return () => {
      if (unlisten) {
        unlisten();
      }
    };
  }, []);

  // Clear logs from both frontend and backend
  const clearLogs = async () => {
    try {
      await pyInvoke("clear_mqtt_messages", {});
      setLogs([]);
    } catch (error) {
      console.error("Failed to clear messages:", error);
    }
  };

  const toggleSpot = (index: number) => {
    setParkingSpots((prev) => {
      const newSpots = [...prev];
      newSpots[index] = !newSpots[index];
      return newSpots;
    });
  };

  const handleWarningOn = () => {
    setWarningLight(true);
  };

  const handleWarningOff = () => {
    setWarningLight(false);
  };

  const handleSendMessage = () => {
    if (displayMessage.trim()) {
      // TODO: Send to display board via MQTT
      setDisplayMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const availableSpots = parkingSpots.filter((spot) => !spot).length;

  // Connection status indicator helper
  const getStatusText = () => {
    switch (connectionStatus) {
      case "disconnected": return "Disconnected";
      case "connecting": return "Connecting...";
      case "connected": return "Connected";
      case "error": return "Connection Error";
    }
  };

  return (
    <div className="dashboard">
      <div className="texture"></div>
      
      {/* Connection Status Indicator */}
      <div className={`connection-status ${connectionStatus}`}>
        <div className="status-dot"></div>
        <span className="status-text">{getStatusText()}</span>
      </div>
      
      <div className="content">
        {/* Top Row - Parking Spots */}
        <div className="row parking-row">
          <div className="parking-info">
            <span className="big-number">{availableSpots}</span>
            <span className="info-label">spots free</span>
          </div>
          
          <div className="spots-container">
            {parkingSpots.map((isOccupied, index) => (
              <div
                key={index}
                className={`spot ${isOccupied ? "occupied" : "available"}`}
                onClick={() => toggleSpot(index)}
              >
                <span className="spot-num">{index + 1}</span>
                <div className={`spot-light ${isOccupied ? "red" : "green"}`}></div>
              </div>
            ))}
          </div>
        </div>

        {/* Middle Row - Warning + Console */}
        <div className="row middle-row">
          {/* Warning Control */}
          <div className="warning-area">
            <div className={`light-indicator ${warningLight ? "on" : "off"}`}>
              <div className="light-bulb"></div>
            </div>
            <div className="warning-controls">
              <button
                className={`ctrl-btn ${warningLight ? "active" : ""}`}
                onClick={handleWarningOn}
              >
                warn on
              </button>
              <button
                className={`ctrl-btn ${!warningLight ? "active" : ""}`}
                onClick={handleWarningOff}
              >
                warn off
              </button>
            </div>
          </div>

          {/* Console */}
          <div className="console-area">
            <div className="console-header">
              <span className="console-label">sensor log</span>
              <button className="clear-btn" onClick={clearLogs}>clear</button>
            </div>
            <div className="console-output">
              {logs.map((log) => (
                <div key={log.id} className="log-line">
                  <span className="log-time">{log.timestamp}</span>
                  <span className="log-text">{log.message}</span>
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          </div>
        </div>

        {/* Bottom Row - Message Input */}
        <div className="row message-row">
          <div className="message-area">
            <span className="input-label">display board</span>
            <div className="input-container">
              <textarea
                className="msg-input"
                placeholder="Enter message for display..."
                value={displayMessage}
                onChange={(e) => setDisplayMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={2}
              />
              <button
                className="send-btn"
                onClick={handleSendMessage}
                disabled={!displayMessage.trim()}
              >
                send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
