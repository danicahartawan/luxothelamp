# MQTT Quick Start Guide

Get up and running with MQTT communication for LeLamp in 5 minutes!

## Step 1: Install Mosquitto Broker (Raspberry Pi)

```bash
# Update package list
sudo apt-get update

# Install Mosquitto broker and clients
sudo apt-get install -y mosquitto mosquitto-clients

# Enable and start Mosquitto
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Check status
sudo systemctl status mosquitto
```

## Step 2: Configure Mosquitto

### Create Password File

```bash
# Create user 'lelamp' with password
sudo mosquitto_passwd -c /etc/mosquitto/passwd lelamp
# Enter password when prompted (e.g., "lelamp123")
```

### Edit Configuration

```bash
sudo nano /etc/mosquitto/mosquitto.conf
```

Add these lines:

```conf
# Allow connections on port 1883
listener 1883
protocol mqtt

# Require authentication
allow_anonymous false
password_file /etc/mosquitto/passwd

# Enable persistence
persistence true
persistence_location /var/lib/mosquitto/

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_type all
```

Save and restart:

```bash
sudo systemctl restart mosquitto
```

## Step 3: Configure LeLamp

### Create `.env` file

```bash
cd /path/to/lelamp_runtime
cp .env.example .env
nano .env
```

### Edit `.env` Configuration

```bash
# Enable MQTT
MQTT_ENABLED=true
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=lelamp
MQTT_PASSWORD=lelamp123  # Use your password

# LeLamp ID
LAMP_ID=lelamp

# Enable sensor publishing
MQTT_PUBLISH_DISTANCE=true
MQTT_PUBLISH_WAVE_EVENTS=true
```

## Step 4: Test MQTT Connection

### Terminal 1: Subscribe to All Topics

```bash
mosquitto_sub -h localhost -t "lelamp/#" -u lelamp -P lelamp123 -v
```

### Terminal 2: Start LeLamp

```bash
cd /path/to/lelamp_runtime
sudo uv run main.py console
```

You should see messages like:

```
lelamp/lelamp/status/online {"online": true, "lamp_id": "lelamp", "timestamp": 1234567890.123}
lelamp/lelamp/sensor/ultrasonic/distance {"distance_m": 0.45, "distance_cm": 45.0, "timestamp": 1234567890.123, "sensor_status": "ok"}
```

## Step 5: Send Commands via MQTT

### Play Specific Expression

```bash
mosquitto_pub -h localhost -t "lelamp/lelamp/command/play" \
  -u lelamp -P lelamp123 \
  -m '{"expression": "excited"}'
```

### Play All Expressions

```bash
mosquitto_pub -h localhost -t "lelamp/lelamp/command/play_all" \
  -u lelamp -P lelamp123 \
  -m '{}'
```

### Set RGB Color

```bash
# Set to red
mosquitto_pub -h localhost -t "lelamp/lelamp/command/rgb" \
  -u lelamp -P lelamp123 \
  -m '{"r": 255, "g": 0, "b": 0}'

# Set to blue
mosquitto_pub -h localhost -t "lelamp/lelamp/command/rgb" \
  -u lelamp -P lelamp123 \
  -m '{"r": 0, "g": 0, "b": 255}'
```

## Step 6: Monitor Wave Detection

### Subscribe to Wave Events Only

```bash
mosquitto_sub -h localhost -t "lelamp/+/sensor/ultrasonic/wave" \
  -u lelamp -P lelamp123
```

Wave your hand in front of the sensor and you'll see:

```json
{
  "detected": true,
  "timestamp": 1714335600.123,
  "trigger_type": "automatic",
  "distance_at_detection": 0.35,
  "velocity": 0.18
}
```

## Operating Modes

### Mode 1: MQTT Disabled (Default)
Local operation only, no MQTT communication

```bash
# In .env file
MQTT_ENABLED=false
```

### Mode 2: MQTT Publishing Only
Publishes sensor data but still triggers local expressions

```bash
MQTT_ENABLED=true
MQTT_PUBLISH_DISTANCE=true
MQTT_PUBLISH_WAVE_EVENTS=true
```

### Mode 3: MQTT Remote Control
Control LeLamp remotely via MQTT commands

```bash
MQTT_ENABLED=true
```

Then use `mosquitto_pub` commands from any device on the network!

## Troubleshooting

### Can't Connect to Broker

```bash
# Check if Mosquitto is running
sudo systemctl status mosquitto

# Check logs
sudo tail -f /var/log/mosquitto/mosquitto.log

# Test with mosquitto_pub
mosquitto_pub -h localhost -t "test" -m "hello" -u lelamp -P lelamp123
```

### Authentication Failed

```bash
# Recreate password
sudo mosquitto_passwd -c /etc/mosquitto/passwd lelamp

# Restart Mosquitto
sudo systemctl restart mosquitto
```

### No Messages Received

```bash
# Check topic subscription matches publishing
# Correct: lelamp/#
# Wrong: lelamp/sensor (too specific)

# Verify credentials in .env match Mosquitto password file
```

### Distance Not Publishing

```bash
# Enable in .env
MQTT_PUBLISH_DISTANCE=true

# Check logs
sudo uv run main.py console
# Should see: "Connected to MQTT broker"
```

## Remote Access (Optional)

### Access from Another Device

1. **Find Raspberry Pi IP address:**
   ```bash
   hostname -I
   # Example output: 192.168.1.100
   ```

2. **Update Mosquitto config for network access:**
   ```bash
   sudo nano /etc/mosquitto/mosquitto.conf
   ```

   Change:
   ```conf
   listener 1883 0.0.0.0  # Listen on all network interfaces
   ```

3. **Allow port through firewall:**
   ```bash
   sudo ufw allow 1883/tcp
   ```

4. **Connect from remote device:**
   ```bash
   mosquitto_sub -h 192.168.1.100 -t "lelamp/#" -u lelamp -P lelamp123 -v
   ```

## Python Client Example

```python
import paho.mqtt.client as mqtt
import json

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("lelamp/#")

def on_message(client, userdata, msg):
    print(f"Topic: {msg.topic}")
    print(f"Message: {msg.payload.decode()}")

client = mqtt.Client()
client.username_pw_set("lelamp", "lelamp123")
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)

# Send command
client.publish("lelamp/lelamp/command/play",
               json.dumps({"expression": "happy_wiggle"}))

client.loop_forever()
```

## Next Steps

- Read [MQTT_COMMUNICATION_RUBRIC.md](MQTT_COMMUNICATION_RUBRIC.md) for complete protocol documentation
- Integrate with mobile app or web dashboard
- Set up MQTT logging/analytics
- Add TLS encryption for production

## Useful Commands

```bash
# List all subscribed topics
mosquitto_sub -h localhost -t "#" -u lelamp -P lelamp123 -v

# Monitor distance readings
mosquitto_sub -h localhost -t "lelamp/+/sensor/ultrasonic/distance" -u lelamp -P lelamp123

# Monitor expressions playing
mosquitto_sub -h localhost -t "lelamp/+/expression/playing" -u lelamp -P lelamp123

# Test connection
mosquitto_pub -h localhost -t "test/connection" -m "ping" -u lelamp -P lelamp123 && echo "Success!"
```

---

**Congratulations!** 🎉 You now have MQTT communication set up for LeLamp!

Your lamp can now:
- Publish sensor data in real-time
- Receive remote commands
- Be monitored from any MQTT client
- Integrate with home automation systems
