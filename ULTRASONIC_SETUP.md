# Ultrasonic Sensor Wave Detection Setup

This guide explains how to set up and use the ultrasonic sensor wave detection feature for LeLamp.

## Overview

The ultrasonic sensor feature allows LeLamp to detect hand wave gestures and automatically play all expression animations in sequence. This creates an interactive experience where users can trigger animations without voice commands.

## Hardware Requirements

### HC-SR04 Ultrasonic Sensor

You'll need:
- 1x HC-SR04 Ultrasonic Distance Sensor
- 4x Female-to-Female jumper wires
- Access to Raspberry Pi GPIO pins

### Wiring Diagram

```
HC-SR04          Raspberry Pi
--------         ------------
VCC      →       5V (Pin 2 or 4)
TRIG     →       GPIO 23 (Pin 16)
ECHO     →       GPIO 24 (Pin 18)
GND      →       GND (Pin 6, 9, 14, 20, 25, 30, 34, or 39)
```

**Important:** The HC-SR04 ECHO pin outputs 5V, but Raspberry Pi GPIO pins are 3.3V tolerant. For safer operation, consider using a voltage divider (2x resistors: 1kΩ and 2kΩ) on the ECHO pin.

## Software Setup

### 1. Install Dependencies

The ultrasonic sensor requires the `gpiozero` library, which is included in the hardware dependencies:

```bash
# Install hardware dependencies
uv pip install -e ".[hardware]"
```

### 2. Configuration

The ultrasonic sensor is automatically initialized in both `main.py` and `smooth_animation.py` with these default settings:

```python
UltrasonicService(
    trigger_pin=23,           # GPIO pin for TRIG
    echo_pin=24,             # GPIO pin for ECHO
    detection_threshold=0.5,  # Detect waves within 50cm
    wave_speed_threshold=0.15, # Minimum speed (m/s) for wave detection
    sample_rate=10.0         # Read sensor 10 times per second
)
```

### 3. Customizing Detection Parameters

You can adjust these parameters in `main.py` or `smooth_animation.py`:

#### `detection_threshold` (default: 0.5 meters)
- Maximum distance to detect hand waves
- Smaller values = must wave closer to sensor
- Larger values = detect from farther away
- Range: 0.02 to 2.0 meters

#### `wave_speed_threshold` (default: 0.15 m/s)
- Minimum hand movement speed to count as a wave
- Higher values = need faster hand movement
- Lower values = more sensitive, may trigger accidentally
- Range: 0.05 to 0.5 m/s

#### `sample_rate` (default: 10.0 Hz)
- How often to read from the sensor
- Higher values = more responsive but more CPU usage
- Lower values = less CPU but might miss quick waves
- Range: 5.0 to 20.0 Hz

#### `wave_cooldown` (default: 2.0 seconds)
- Minimum time between wave detections
- Prevents accidental double-triggers
- Adjust in `ultrasonic_service.py`

### 4. Changing GPIO Pins

If you need to use different GPIO pins, edit the initialization in `main.py` and `smooth_animation.py`:

```python
self.ultrasonic_service = UltrasonicService(
    trigger_pin=YOUR_TRIG_PIN,  # Change to your TRIG pin
    echo_pin=YOUR_ECHO_PIN,     # Change to your ECHO pin
    # ... other parameters
)
```

## Testing the Sensor

### Quick Test

Run the standalone test script to verify your sensor is working:

```bash
sudo python3 lelamp/test/test_ultrasonic.py
```

You should see:
1. Distance readings in real-time
2. A bar graph showing proximity
3. "WAVE DETECTED!" message when you wave your hand

### Troubleshooting

**No distance readings:**
- Check wiring connections
- Verify GPIO pin numbers match your setup
- Ensure sensor has 5V power
- Try swapping TRIG and ECHO pins (common mistake)

**False wave detections:**
- Increase `wave_speed_threshold` value
- Decrease `detection_threshold` value
- Check for nearby moving objects (fans, curtains, pets)

**Missed wave detections:**
- Decrease `wave_speed_threshold` value
- Increase `detection_threshold` value
- Wave faster and more deliberately
- Ensure hand is within detection range

**"gpiozero not available" warning:**
- Install hardware dependencies: `uv pip install -e ".[hardware]"`
- If testing on non-Raspberry Pi, the service runs in simulation mode

## How It Works

### Wave Detection Algorithm

The system detects waves by analyzing distance patterns:

1. **Continuous Monitoring**: Reads distance 10 times per second
2. **Distance History**: Keeps last 10 readings (1 second of data)
3. **Proximity Check**: Only triggers if hand is within threshold distance
4. **Speed Analysis**: Calculates velocity of hand movement
5. **Pattern Recognition**: Detects back-and-forth motion (direction changes)
6. **Cooldown**: Prevents re-triggering for 2 seconds

A wave is confirmed when:
- Hand is within detection threshold (default 50cm)
- Movement speed exceeds threshold (default 0.15 m/s)
- At least one direction change detected (back-and-forth motion)

### Expression Sequence

When a wave is detected, LeLamp will:

1. **Light Change**: Turn bright yellow/orange (excited color)
2. **Play All Expressions**: Run through all 9 expressions:
   - nod
   - excited
   - curious
   - happy_wiggle
   - headshake
   - sad
   - scanning
   - shock
   - shy
3. **Color Changes**: Random colors between each expression
4. **Return to Normal**: White light after sequence completes

Total sequence duration: ~54 seconds (9 expressions × 6 seconds each)

## Running LeLamp with Ultrasonic

### Start with Discrete Animation Mode

```bash
sudo uv run main.py console
```

### Start with Smooth Animation Mode

```bash
sudo uv run smooth_animation.py console
```

Both modes include ultrasonic wave detection by default!

## Disabling Ultrasonic Sensor

If you want to run LeLamp without the ultrasonic sensor, comment out these lines in `main.py` or `smooth_animation.py`:

```python
# Initialize ultrasonic sensor service
# self.ultrasonic_service = UltrasonicService(...)
# self.ultrasonic_service.set_callback(self._on_wave_detected)
# self.ultrasonic_service.start()
```

## Advanced: Custom Wave Callbacks

You can customize what happens when a wave is detected by editing the `_on_wave_detected()` method in `main.py` or `smooth_animation.py`:

```python
def _on_wave_detected(self):
    """Custom behavior on wave detection"""
    # Your custom code here
    # Examples:
    # - Play specific expression only
    # - Trigger TTS announcement
    # - Change to specific color
    # - Log to file
    # - Send notification
    pass
```

## Safety Notes

- Always use `sudo` when running scripts that access GPIO
- Disconnect power before changing wiring
- Consider using a voltage divider on ECHO pin for 3.3V safety
- Don't connect/disconnect sensor while system is powered
- Keep sensor dry and away from liquids

## References

- [HC-SR04 Datasheet](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf)
- [Raspberry Pi GPIO Pinout](https://pinout.xyz)
- [gpiozero Documentation](https://gpiozero.readthedocs.io/)
