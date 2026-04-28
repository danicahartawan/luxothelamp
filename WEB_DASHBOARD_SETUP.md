# LeLamp Web Dashboard Setup Guide

## Overview

Control your LeLamp from any web browser! Send text commands, change colors, trigger expressions, and monitor sensor data in real-time.

**How easy is it?** ⭐⭐⭐⭐⭐ (Very Easy!)

**Time to setup:** 10 minutes

---

## Architecture

```
┌─────────────────┐
│  Web Browser    │
│  (Dashboard)    │
└────────┬────────┘
         │ WebSocket (Port 9001)
         ▼
┌─────────────────┐
│ MQTT Broker     │
│  (Mosquitto)    │
└────────┬────────┘
         │ MQTT (Port 1883)
         ▼
┌─────────────────┐
│    LeLamp       │
│ (Raspberry Pi)  │
└─────────────────┘
```

---

## Step 1: Enable WebSocket Support in Mosquitto

Browsers need WebSockets to communicate with MQTT. Let's set it up:

### Copy Configuration File

```bash
sudo cp web_dashboard/mosquitto_websocket.conf /etc/mosquitto/conf.d/websocket.conf
```

### Or manually edit Mosquitto config:

```bash
sudo nano /etc/mosquitto/mosquitto.conf
```

Add these lines:

```conf
# Standard MQTT (for LeLamp)
listener 1883
protocol mqtt

# WebSocket (for web browsers)
listener 9001
protocol websockets

# Authentication
allow_anonymous false
password_file /etc/mosquitto/passwd

# Persistence
persistence true
persistence_location /var/lib/mosquitto/

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_type all
```

### Restart Mosquitto

```bash
sudo systemctl restart mosquitto
sudo systemctl status mosquitto
```

You should see both listeners:
- Port **1883**: Standard MQTT
- Port **9001**: WebSocket

---

## Step 2: Open the Web Dashboard

### Option A: Open Locally (on Raspberry Pi)

```bash
cd /path/to/lelamp_runtime/web_dashboard
python3 -m http.server 8080
```

Then open browser: **http://localhost:8080**

### Option B: Open from Another Computer

1. **Find your Raspberry Pi's IP:**
   ```bash
   hostname -I
   # Example: 192.168.1.100
   ```

2. **Start simple web server:**
   ```bash
   cd /path/to/lelamp_runtime/web_dashboard
   python3 -m http.server 8080
   ```

3. **Open from any device on same network:**
   - Go to: **http://192.168.1.100:8080**

### Option C: Double-Click HTML File

Simply double-click `web_dashboard/index.html` to open in browser!

---

## Step 3: Connect to LeLamp

1. **In the web dashboard**, enter connection details:
   - **Broker**: `localhost` (or your Pi's IP like `192.168.1.100`)
   - **Port**: `9001` (WebSocket port)
   - **Username**: `lelamp`
   - **Password**: Your MQTT password

2. **Click "Connect"**

3. You should see:
   - Status changes to "Connected"
   - Activity log shows "Connected to MQTT broker!"
   - Distance readings start updating

---

## Step 4: Control Your Lamp!

### Send Expression Commands

1. Select an expression from dropdown (Excited, Happy Wiggle, etc.)
2. Click **"Play Expression"**
3. Watch your lamp perform!

### Change Colors

- Click any color swatch for instant color change
- Or enter custom RGB values and click **"Set Custom Color"**

### Play All Expressions

- Click **"Play All Expressions"**
- Lamp cycles through all 9 expressions

### Monitor Sensor Data

- Watch **real-time distance readings**
- See **wave detection indicator** when you wave

---

## Features

### 🎛️ Real-Time Control
- Play any expression instantly
- Change RGB colors
- Trigger full expression sequences

### 📊 Live Monitoring
- Distance sensor readings (updated 10x/second)
- Wave detection events
- Expression status updates
- Connection status

### 📱 Responsive Design
- Works on desktop, tablet, and mobile
- Beautiful gradient interface
- Real-time activity log

### 🔒 Secure
- Username/password authentication
- Encrypted WebSocket option (wss://)

---

## Advanced: Text-to-Expression Commands

Want to send text commands like "be happy" or "look excited"? Add this to the HTML:

```html
<!-- Add this to the HTML inside a card -->
<div class="card">
    <h2>💬 Text Commands</h2>
    <div class="input-group">
        <label>Send a message to LeLamp</label>
        <input type="text" id="textCommand" placeholder="e.g., 'be happy', 'look excited'">
    </div>
    <button class="button button-primary" onclick="sendTextCommand()">Send</button>
</div>

<script>
function sendTextCommand() {
    const text = document.getElementById('textCommand').value.toLowerCase();

    // Map text to expressions
    const mapping = {
        'happy': 'happy_wiggle',
        'excited': 'excited',
        'sad': 'sad',
        'curious': 'curious',
        'nod': 'nod',
        'yes': 'nod',
        'no': 'headshake',
        'shake': 'headshake',
        'shy': 'shy',
        'shock': 'shock',
        'surprised': 'shock',
        'scan': 'scanning',
        'look around': 'scanning'
    };

    // Find matching expression
    for (let [keyword, expression] of Object.entries(mapping)) {
        if (text.includes(keyword)) {
            const message = JSON.stringify({ expression: expression });
            client.publish('lelamp/lelamp/command/play', message);
            log(`Text command: "${text}" → ${expression}`);
            return;
        }
    }

    log(`No matching expression for: "${text}"`);
}
</script>
```

Now you can type:
- "be happy" → plays happy_wiggle
- "look excited" → plays excited
- "nod yes" → plays nod
- "act surprised" → plays shock

---

## Troubleshooting

### "Connection failed" Error

**Problem**: Can't connect to MQTT broker

**Solutions**:
```bash
# 1. Check Mosquitto is running
sudo systemctl status mosquitto

# 2. Check WebSocket port is open
sudo netstat -tuln | grep 9001

# 3. Test WebSocket connection
# Install websocat: sudo apt install websocat
websocat ws://localhost:9001
```

### "Authentication failed"

**Problem**: Wrong username/password

**Solutions**:
```bash
# Reset password
sudo mosquitto_passwd -c /etc/mosquitto/passwd lelamp
# Enter new password when prompted

# Restart Mosquitto
sudo systemctl restart mosquitto
```

### No sensor data appearing

**Problem**: LeLamp not publishing to MQTT

**Solutions**:
```bash
# 1. Check .env file has MQTT enabled
cat .env | grep MQTT_ENABLED
# Should show: MQTT_ENABLED=true

# 2. Check LeLamp is running
# You should see "Connected to MQTT broker" in logs

# 3. Test MQTT subscription
mosquitto_sub -h localhost -t "lelamp/#" -u lelamp -P your_password -v
```

### Can't access from another device

**Problem**: Firewall blocking ports

**Solutions**:
```bash
# Allow ports through firewall
sudo ufw allow 9001/tcp  # WebSocket
sudo ufw allow 8080/tcp  # Web server
sudo ufw reload

# OR disable firewall (for testing only!)
sudo ufw disable
```

---

## Deployment Options

### Option 1: Simple HTTP Server (Development)

```bash
cd web_dashboard
python3 -m http.server 8080
```
- ✅ Quick and easy
- ❌ Not persistent (stops when terminal closes)

### Option 2: Nginx (Production)

```bash
# Install Nginx
sudo apt install nginx

# Copy web files
sudo cp -r web_dashboard /var/www/lelamp

# Create Nginx config
sudo nano /etc/nginx/sites-available/lelamp
```

Add:
```nginx
server {
    listen 80;
    server_name _;

    root /var/www/lelamp;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/lelamp /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

Now access at: **http://your-pi-ip** (port 80, default HTTP)

### Option 3: Node.js Server with Express

Create `server.js`:
```javascript
const express = require('express');
const app = express();

app.use(express.static('web_dashboard'));

app.listen(8080, () => {
    console.log('Dashboard running on http://localhost:8080');
});
```

Run:
```bash
npm install express
node server.js
```

---

## Mobile App Integration

The same MQTT commands work from mobile apps!

### React Native Example

```javascript
import mqtt from 'react-native-mqtt';

const client = mqtt.connect('ws://192.168.1.100:9001', {
    username: 'lelamp',
    password: 'lelamp123'
});

// Play expression
const playExpression = (expression) => {
    client.publish('lelamp/lelamp/command/play',
        JSON.stringify({ expression }));
};

// Change color
const setColor = (r, g, b) => {
    client.publish('lelamp/lelamp/command/rgb',
        JSON.stringify({ r, g, b }));
};
```

### Flutter Example

```dart
import 'package:mqtt_client/mqtt_client.dart';

final client = MqttClient('192.168.1.100', '9001');
client.useWebSocket = true;

await client.connect('lelamp', 'lelamp123');

// Play expression
client.publishMessage(
    'lelamp/lelamp/command/play',
    MqttQos.atLeastOnce,
    '{"expression": "excited"}'
);
```

---

## Security Best Practices

### 1. Enable TLS/SSL for WebSocket

```bash
# Generate self-signed certificate
sudo openssl req -new -x509 -days 365 -extensions v3_ca \
    -keyout mosquitto-key.pem -out mosquitto-cert.pem

# Update Mosquitto config
listener 9001
protocol websockets
cafile /etc/mosquitto/ca_certificates/mosquitto-cert.pem
certfile /etc/mosquitto/certs/mosquitto-cert.pem
keyfile /etc/mosquitto/certs/mosquitto-key.pem
```

Update web dashboard connection:
```javascript
client = mqtt.connect(`wss://${broker}:9001`, options);  // Note: wss:// not ws://
```

### 2. Use Strong Passwords

```bash
# Generate random password
openssl rand -base64 32

# Set it
sudo mosquitto_passwd -c /etc/mosquitto/passwd lelamp
```

### 3. Restrict Network Access

```bash
# Only allow from local network
sudo ufw allow from 192.168.1.0/24 to any port 9001
```

---

## Next Steps

1. **Customize the UI**: Edit `index.html` to match your style
2. **Add voice control**: Integrate Web Speech API
3. **Create mobile app**: Use React Native or Flutter
4. **Add AI chat**: Integrate ChatGPT API for natural language control
5. **Cloud access**: Deploy dashboard to cloud (AWS, Vercel, etc.)

---

## Summary

**Difficulty**: ⭐ Very Easy!

**What you need**:
1. Mosquitto with WebSocket enabled (port 9001)
2. Web browser
3. LeLamp running with MQTT enabled

**What you get**:
- Beautiful web dashboard
- Real-time control
- Live sensor monitoring
- Works from any device
- Text-based commands (with custom mapping)

**Total setup time**: 10 minutes! 🎉

Enjoy controlling your LeLamp from anywhere!
