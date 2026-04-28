import time
import threading
import logging
from typing import Optional, Callable
from collections import deque

try:
    from gpiozero import DistanceSensor
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("gpiozero not available, UltrasonicService will run in simulation mode")

from ..base import ServiceBase, Priority


class UltrasonicService(ServiceBase):
    """
    Service for HC-SR04 ultrasonic sensor wave detection.

    Continuously monitors distance and detects hand wave gestures.
    When a wave is detected, triggers a callback function.
    """

    def __init__(
        self,
        trigger_pin: int = 23,
        echo_pin: int = 24,
        detection_threshold: float = 0.3,  # meters - detect changes within 30cm
        wave_speed_threshold: float = 0.15,  # m/s - minimum speed to count as wave
        callback: Optional[Callable] = None,
        sample_rate: float = 10.0,  # Hz - samples per second
    ):
        super().__init__("ultrasonic")

        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.detection_threshold = detection_threshold
        self.wave_speed_threshold = wave_speed_threshold
        self.sample_rate = sample_rate
        self.callback = callback

        # Wave detection state
        self.distance_history = deque(maxlen=10)  # Keep last 10 readings
        self.last_wave_time = 0
        self.wave_cooldown = 2.0  # seconds between wave detections

        # Sensor initialization
        self.sensor: Optional[DistanceSensor] = None
        self._sensor_thread: Optional[threading.Thread] = None
        self._sensor_running = threading.Event()

        if GPIO_AVAILABLE:
            try:
                self.sensor = DistanceSensor(echo=echo_pin, trigger=trigger_pin, max_distance=2.0)
                self.logger.info(f"Ultrasonic sensor initialized on pins TRIG={trigger_pin}, ECHO={echo_pin}")
            except Exception as e:
                self.logger.error(f"Failed to initialize ultrasonic sensor: {e}")
                self.sensor = None
        else:
            self.logger.warning("Running in simulation mode (no GPIO)")

    def set_callback(self, callback: Callable):
        """Set the callback function to trigger when wave is detected."""
        self.callback = callback
        self.logger.info("Wave detection callback registered")

    def start(self):
        """Start the service and begin monitoring sensor."""
        super().start()

        # Start sensor monitoring thread
        self._sensor_running.set()
        self._sensor_thread = threading.Thread(target=self._monitor_sensor, daemon=True)
        self._sensor_thread.start()
        self.logger.info("Ultrasonic sensor monitoring started")

    def stop(self, timeout: float = 5.0):
        """Stop the service and sensor monitoring."""
        self._sensor_running.clear()
        if self._sensor_thread and self._sensor_thread.is_alive():
            self._sensor_thread.join(timeout=1.0)

        if self.sensor:
            self.sensor.close()

        super().stop(timeout)

    def _monitor_sensor(self):
        """Background thread that continuously reads from the sensor."""
        sleep_time = 1.0 / self.sample_rate

        while self._sensor_running.is_set():
            try:
                distance = self._read_distance()

                if distance is not None:
                    self.distance_history.append((time.time(), distance))

                    # Check for wave pattern
                    if self._detect_wave():
                        current_time = time.time()

                        # Check cooldown
                        if current_time - self.last_wave_time > self.wave_cooldown:
                            self.last_wave_time = current_time
                            self.logger.info("Wave detected!")

                            # Trigger callback
                            if self.callback:
                                try:
                                    self.callback()
                                except Exception as e:
                                    self.logger.error(f"Error in wave callback: {e}")

                time.sleep(sleep_time)

            except Exception as e:
                self.logger.error(f"Error reading sensor: {e}")
                time.sleep(sleep_time)

    def _read_distance(self) -> Optional[float]:
        """Read distance from sensor in meters."""
        if self.sensor:
            try:
                return self.sensor.distance
            except Exception as e:
                self.logger.debug(f"Sensor read error: {e}")
                return None
        else:
            # Simulation mode - return random distance
            import random
            return random.uniform(0.1, 1.0)

    def _detect_wave(self) -> bool:
        """
        Detect wave pattern from distance history.

        A wave is detected when:
        1. Distance changes rapidly (high speed)
        2. Within detection threshold range
        3. Shows back-and-forth motion pattern
        """
        if len(self.distance_history) < 5:
            return False

        # Convert to lists for analysis
        times = [t for t, d in self.distance_history]
        distances = [d for t, d in self.distance_history]

        # Check if any reading is within detection threshold
        min_distance = min(distances)
        if min_distance > self.detection_threshold:
            return False

        # Calculate velocities (change in distance over time)
        velocities = []
        for i in range(1, len(distances)):
            dt = times[i] - times[i-1]
            dd = distances[i] - distances[i-1]
            if dt > 0:
                velocity = abs(dd / dt)
                velocities.append(velocity)

        if not velocities:
            return False

        # Check for rapid movement (wave motion)
        max_velocity = max(velocities)
        if max_velocity < self.wave_speed_threshold:
            return False

        # Check for direction changes (back-and-forth motion)
        direction_changes = 0
        for i in range(1, len(distances) - 1):
            d_prev = distances[i] - distances[i-1]
            d_next = distances[i+1] - distances[i]

            # Direction change detected
            if d_prev * d_next < 0:
                direction_changes += 1

        # Need at least 1 direction change for wave pattern
        return direction_changes >= 1

    def handle_event(self, event_type: str, payload: any):
        """Handle service events."""
        if event_type == "set_callback":
            self.set_callback(payload)
        elif event_type == "get_distance":
            # Return current distance reading
            if self.distance_history:
                _, distance = self.distance_history[-1]
                self.logger.debug(f"Current distance: {distance:.2f}m")
        else:
            self.logger.warning(f"Unknown event type: {event_type}")

    def get_current_distance(self) -> Optional[float]:
        """Get the most recent distance reading."""
        if self.distance_history:
            _, distance = self.distance_history[-1]
            return distance
        return None
