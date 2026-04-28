#!/usr/bin/env python3
"""
Test script for ultrasonic sensor wave detection.

This script allows you to test the HC-SR04 ultrasonic sensor and wave detection
without running the full LeLamp system.

Usage:
    sudo python3 lelamp/test/test_ultrasonic.py

Hardware setup:
    - HC-SR04 Ultrasonic Sensor
    - TRIG pin -> GPIO 23 (default)
    - ECHO pin -> GPIO 24 (default)
    - VCC -> 5V
    - GND -> GND
"""

import sys
import time
from lelamp.service import UltrasonicService


def on_wave_detected():
    """Callback function triggered when wave is detected"""
    print("\n" + "="*50)
    print("🌊 WAVE DETECTED! 🌊")
    print("="*50 + "\n")


def main():
    print("Ultrasonic Sensor Wave Detection Test")
    print("=" * 50)
    print("Hardware Requirements:")
    print("  - HC-SR04 ultrasonic sensor")
    print("  - TRIG pin -> GPIO 23")
    print("  - ECHO pin -> GPIO 24")
    print("  - VCC -> 5V, GND -> GND")
    print("=" * 50)
    print()

    # Create ultrasonic service
    print("Initializing ultrasonic sensor...")
    ultrasonic = UltrasonicService(
        trigger_pin=23,
        echo_pin=24,
        detection_threshold=0.5,  # Detect within 50cm
        wave_speed_threshold=0.15,  # Minimum speed for wave detection
        sample_rate=10.0,  # 10 samples per second
        callback=on_wave_detected
    )

    # Start the service
    ultrasonic.start()
    print("✓ Ultrasonic sensor monitoring started")
    print()
    print("Wave your hand in front of the sensor (within 50cm)")
    print("Press Ctrl+C to stop")
    print()

    try:
        # Main loop - display distance readings
        while True:
            distance = ultrasonic.get_current_distance()
            if distance is not None:
                distance_cm = distance * 100
                # Create a simple bar graph
                bar_length = int(min(distance_cm / 2, 50))
                bar = "█" * bar_length
                print(f"\rDistance: {distance_cm:6.2f} cm [{bar:<50}]", end="", flush=True)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nStopping ultrasonic sensor...")
        ultrasonic.stop()
        print("✓ Sensor stopped")
        print("Goodbye!")


if __name__ == "__main__":
    main()
