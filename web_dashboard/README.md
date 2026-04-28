# LeLamp Web Dashboard

Beautiful, real-time web interface to control your LeLamp via MQTT.

## Quick Start

### 1. Enable WebSocket in Mosquitto

```bash
sudo cp mosquitto_websocket.conf /etc/mosquitto/conf.d/websocket.conf
sudo systemctl restart mosquitto
```

### 2. Start Web Server

```bash
python3 -m http.server 8080
```

### 3. Open Browser

Go to: **http://localhost:8080**

Or from another device: **http://YOUR_PI_IP:8080**

### 4. Connect

- **Broker**: localhost (or your Pi's IP)
- **Port**: 9001
- **Username**: lelamp
- **Password**: your_mqtt_password

## Features

✨ **Real-Time Control**
- Play expressions
- Change RGB colors
- Trigger expression sequences

📊 **Live Monitoring**
- Distance sensor readings
- Wave detection events
- Expression status
- Activity log

📱 **Responsive Design**
- Works on desktop, tablet, mobile
- Beautiful gradient UI
- Smooth animations

## Files

- `index.html` - Main dashboard (standalone, no build required!)
- `mosquitto_websocket.conf` - Mosquitto WebSocket configuration
- `README.md` - This file

## Full Documentation

See [WEB_DASHBOARD_SETUP.md](../WEB_DASHBOARD_SETUP.md) for:
- Detailed setup instructions
- Text-to-command examples
- Mobile app integration
- Troubleshooting guide
- Security best practices

## How Easy Is It?

**Difficulty**: ⭐ Very Easy!

**Setup Time**: 10 minutes

**Requirements**:
- Mosquitto with WebSocket (port 9001)
- Any modern web browser
- LeLamp with MQTT enabled

That's it! No npm, no build process, no complex dependencies. Just open the HTML file and control your lamp! 🎉
