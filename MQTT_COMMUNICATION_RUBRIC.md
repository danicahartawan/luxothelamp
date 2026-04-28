# LeLamp MQTT Communication Rubric

## Overview

This document defines the MQTT communication protocol for LeLamp's sensor data and expression control.

## Architecture Diagram

```
┌─────────────────────┐
│ Ultrasonic Sensor   │
│   (HC-SR04)         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ UltrasonicService   │
│ - Read distance     │
│ - Detect waves      │
└─────┬───────────┬───┘
      │           │
      ▼           ▼
┌──────────┐  ┌──────────────┐
│  Local   │  │ MQTT Service │
│ Callback │  │  Publisher   │
└──────────┘  └──────┬───────┘
                     │
                     ▼
              ┌─────────────┐
              │ MQTT Broker │
              │ (Mosquitto) │
              └──────┬──────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌────────┐  ┌─────────┐  ┌──────────┐
   │ Mobile │  │ Web App │  │ Other    │
   │  App   │  │         │  │ LeLamps  │
   └────────┘  └─────────┘  └──────────┘
```

## MQTT Topics Structure

### Published Topics (LeLamp → Broker)

| Topic | QoS | Retain | Description | Payload Format |
|-------|-----|--------|-------------|----------------|
| `lelamp/{lamp_id}/sensor/ultrasonic/distance` | 0 | No | Real-time distance readings | `{"distance_m": 0.45, "timestamp": 1234567890.123}` |
| `lelamp/{lamp_id}/sensor/ultrasonic/wave` | 1 | No | Wave detection events | `{"detected": true, "timestamp": 1234567890.123}` |
| `lelamp/{lamp_id}/status/online` | 1 | Yes | LeLamp online status | `{"online": true, "timestamp": 1234567890.123}` |
| `lelamp/{lamp_id}/expression/playing` | 0 | No | Currently playing expression | `{"expression": "excited", "timestamp": 1234567890.123}` |
| `lelamp/{lamp_id}/expression/completed` | 0 | No | Expression playback completed | `{"expression": "excited", "timestamp": 1234567890.123}` |

### Subscribed Topics (Broker → LeLamp)

| Topic | QoS | Description | Payload Format |
|-------|-----|-------------|----------------|
| `lelamp/{lamp_id}/command/play` | 1 | Play specific expression | `{"expression": "nod"}` |
| `lelamp/{lamp_id}/command/play_all` | 1 | Play all expressions sequence | `{}` |
| `lelamp/{lamp_id}/command/rgb` | 1 | Set RGB color | `{"r": 255, "g": 150, "b": 0}` |
| `lelamp/{lamp_id}/command/stop` | 1 | Stop current expression | `{}` |

## Quality of Service (QoS) Levels

- **QoS 0 (At most once)**: Distance readings, status updates
  - Fast, no guarantee, acceptable for high-frequency sensor data

- **QoS 1 (At least once)**: Wave events, commands
  - Guaranteed delivery, important for event detection

- **QoS 2 (Exactly once)**: Not used
  - Overhead not needed for this application

## Message Formats

### Distance Reading
```json
{
  "distance_m": 0.45,
  "distance_cm": 45.0,
  "timestamp": 1714335600.123,
  "sensor_status": "ok"
}
```

### Wave Detection Event
```json
{
  "detected": true,
  "timestamp": 1714335600.123,
  "trigger_type": "automatic",
  "distance_at_detection": 0.35,
  "velocity": 0.18
}
```

### Online Status (Last Will & Testament)
```json
{
  "online": true,
  "lamp_id": "lelamp",
  "version": "0.1.0",
  "timestamp": 1714335600.123
}
```

### Expression Status
```json
{
  "expression": "excited",
  "status": "playing",
  "progress": 0.5,
  "timestamp": 1714335600.123
}
```

### Command: Play Expression
```json
{
  "expression": "nod"
}
```

### Command: Play All Expressions
```json
{
  "trigger": "manual"
}
```

### Command: Set RGB
```json
{
  "r": 255,
  "g": 150,
  "b": 0
}
```

## Operating Modes

### Mode 1: Local Only (Default)
- Sensor triggers local callbacks
- No MQTT communication
- Works offline

### Mode 2: MQTT Publish Only
- Sensor publishes to MQTT
- No local expression triggering
- For data collection/monitoring

### Mode 3: Hybrid (Recommended)
- Sensor publishes to MQTT **AND** triggers locally
- Full observability + autonomous operation
- Best for production

### Mode 4: MQTT Command Only
- No automatic wave detection
- All expressions triggered via MQTT commands
- Full remote control

## Configuration

### Environment Variables (.env)
```bash
# MQTT Broker Configuration
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=lelamp
MQTT_PASSWORD=your_password_here
MQTT_USE_TLS=false

# LeLamp Configuration
LAMP_ID=lelamp_living_room
MQTT_MODE=hybrid  # local, publish, hybrid, command

# Sensor Publishing
MQTT_PUBLISH_DISTANCE=true
MQTT_PUBLISH_RATE=10  # Hz
MQTT_PUBLISH_WAVE_EVENTS=true
```

## Security Considerations

### 1. Authentication
- Use username/password authentication
- Unique credentials per LeLamp device
- Store credentials in `.env` file (not in code)

### 2. TLS/SSL Encryption
- Enable TLS for production deployments
- Use certificates for broker authentication
- Port 8883 for TLS connections

### 3. Topic Access Control
- Restrict publish permissions to device-specific topics
- Use MQTT ACL (Access Control Lists)
- Example: `lelamp_living_room` can only publish to `lelamp/lelamp_living_room/*`

### 4. Last Will & Testament (LWT)
- Set offline message on connection
- Broker publishes LWT if client disconnects unexpectedly
- Helps monitor device health

## Example Broker Setup (Mosquitto)

### Install Mosquitto
```bash
# Raspberry Pi / Debian
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients

# macOS
brew install mosquitto
```

### Basic Configuration (`/etc/mosquitto/mosquitto.conf`)
```conf
# Basic settings
listener 1883
protocol mqtt
allow_anonymous false
password_file /etc/mosquitto/passwd

# Persistence
persistence true
persistence_location /var/lib/mosquitto/

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_type all
```

### Create User
```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd lelamp
# Enter password when prompted
```

### Start Broker
```bash
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

## Testing MQTT Communication

### Subscribe to All Topics
```bash
mosquitto_sub -h localhost -t "lelamp/#" -u lelamp -P your_password -v
```

### Publish Test Command
```bash
mosquitto_pub -h localhost -t "lelamp/lelamp/command/play" \
  -u lelamp -P your_password \
  -m '{"expression": "excited"}'
```

### Monitor Distance Readings
```bash
mosquitto_sub -h localhost -t "lelamp/+/sensor/ultrasonic/distance" \
  -u lelamp -P your_password
```

### Monitor Wave Events
```bash
mosquitto_sub -h localhost -t "lelamp/+/sensor/ultrasonic/wave" \
  -u lelamp -P your_password
```

## Integration Examples

### Python Client (Subscriber)
```python
import paho.mqtt.client as mqtt
import json

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload)
    print(f"Topic: {msg.topic}")
    print(f"Data: {payload}")

client = mqtt.Client()
client.username_pw_set("lelamp", "your_password")
client.on_message = on_message
client.connect("localhost", 1883)
client.subscribe("lelamp/#")
client.loop_forever()
```

### Node.js Client (Publisher)
```javascript
const mqtt = require('mqtt');
const client = mqtt.connect('mqtt://localhost:1883', {
  username: 'lelamp',
  password: 'your_password'
});

// Trigger expression
client.publish('lelamp/lelamp/command/play', JSON.stringify({
  expression: 'excited'
}));
```

### Mobile App (React Native / Flutter)
- Use MQTT client library
- Subscribe to wave events
- Display distance readings in real-time
- Send expression commands

## Performance Considerations

### 1. Message Rate Limiting
- Distance: 10 Hz (default)
- Wave events: As detected (cooldown applied)
- Expression status: On change only

### 2. Payload Size
- Keep JSON compact
- Avoid nested objects
- Typical payload: 50-150 bytes

### 3. Network Bandwidth
- At 10 Hz distance publishing: ~1-2 KB/s
- Negligible for local networks
- Consider reducing rate for cellular connections

## Troubleshooting

### Issue: Messages not received
- Check broker is running: `sudo systemctl status mosquitto`
- Verify credentials in `.env` file
- Check topic subscription matches publishing

### Issue: High latency
- Reduce MQTT_PUBLISH_RATE
- Use QoS 0 for non-critical data
- Check network connection

### Issue: Connection drops
- Check broker logs: `/var/log/mosquitto/mosquitto.log`
- Verify firewall allows port 1883
- Implement reconnection logic

## Future Enhancements

1. **Expression Sync**: Multiple LeLamps perform synchronized expressions
2. **Gesture Library**: Publish custom gestures via MQTT
3. **Analytics**: Aggregate wave detection data
4. **Remote Configuration**: Update sensor thresholds via MQTT
5. **Voice Commands**: Integrate with voice assistant via MQTT bridge
