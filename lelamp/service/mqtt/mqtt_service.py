import json
import time
import logging
from typing import Optional, Callable, Dict, Any
import threading

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logging.warning("paho-mqtt not available, MQTTService will run in simulation mode")

from ..base import ServiceBase, Priority


class MQTTService(ServiceBase):
    """
    Service for MQTT communication.

    Publishes sensor data, receives commands, and manages MQTT connection.
    Follows the ServiceBase pattern for consistency with other services.
    """

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        lamp_id: str = "lelamp",
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = False,
        keepalive: int = 60,
    ):
        super().__init__("mqtt")

        self.broker_host = broker_host
        self.broker_port = broker_port
        self.lamp_id = lamp_id
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.keepalive = keepalive

        # MQTT client
        self.client: Optional[mqtt.Client] = None
        self.connected = threading.Event()

        # Command callbacks
        self.command_callbacks: Dict[str, Callable] = {}

        # Topic templates
        self.topics = {
            "distance": f"lelamp/{lamp_id}/sensor/ultrasonic/distance",
            "wave": f"lelamp/{lamp_id}/sensor/ultrasonic/wave",
            "online": f"lelamp/{lamp_id}/status/online",
            "expression_playing": f"lelamp/{lamp_id}/expression/playing",
            "expression_completed": f"lelamp/{lamp_id}/expression/completed",
            "command_play": f"lelamp/{lamp_id}/command/play",
            "command_play_all": f"lelamp/{lamp_id}/command/play_all",
            "command_rgb": f"lelamp/{lamp_id}/command/rgb",
            "command_stop": f"lelamp/{lamp_id}/command/stop",
        }

        if MQTT_AVAILABLE:
            self._init_client()
        else:
            self.logger.warning("Running in simulation mode (no MQTT)")

    def _init_client(self):
        """Initialize MQTT client with callbacks"""
        try:
            self.client = mqtt.Client(client_id=f"{self.lamp_id}_{int(time.time())}")

            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            # Set authentication
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)

            # Set TLS
            if self.use_tls:
                self.client.tls_set()

            # Set Last Will & Testament (LWT)
            lwt_payload = json.dumps({
                "online": False,
                "lamp_id": self.lamp_id,
                "timestamp": time.time()
            })
            self.client.will_set(
                self.topics["online"],
                payload=lwt_payload,
                qos=1,
                retain=True
            )

            self.logger.info(f"MQTT client initialized for lamp_id: {self.lamp_id}")

        except Exception as e:
            self.logger.error(f"Failed to initialize MQTT client: {e}")
            self.client = None

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            self.logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.connected.set()

            # Publish online status
            self.publish_online_status(True)

            # Subscribe to command topics
            self._subscribe_commands()
        else:
            self.logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
            self.connected.clear()

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        self.logger.warning(f"Disconnected from MQTT broker, return code: {rc}")
        self.connected.clear()

        if rc != 0:
            self.logger.info("Unexpected disconnection, will auto-reconnect")

    def _on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            payload = json.loads(msg.payload.decode())
            self.logger.debug(f"Received message on topic {msg.topic}: {payload}")

            # Dispatch to event handler
            self.dispatch("message_received", {"topic": msg.topic, "payload": payload})

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode message payload: {e}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    def _subscribe_commands(self):
        """Subscribe to all command topics"""
        command_topics = [
            (self.topics["command_play"], 1),
            (self.topics["command_play_all"], 1),
            (self.topics["command_rgb"], 1),
            (self.topics["command_stop"], 1),
        ]

        for topic, qos in command_topics:
            self.client.subscribe(topic, qos)
            self.logger.info(f"Subscribed to {topic}")

    def start(self):
        """Start MQTT service and connect to broker"""
        super().start()

        if not self.client:
            self.logger.warning("MQTT client not initialized, running in simulation mode")
            return

        try:
            self.client.connect(self.broker_host, self.broker_port, self.keepalive)
            self.client.loop_start()
            self.logger.info("MQTT client loop started")
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")

    def stop(self, timeout: float = 5.0):
        """Stop MQTT service and disconnect from broker"""
        if self.client and self.connected.is_set():
            # Publish offline status
            self.publish_online_status(False)

            # Disconnect
            self.client.loop_stop()
            self.client.disconnect()
            self.logger.info("Disconnected from MQTT broker")

        super().stop(timeout)

    def handle_event(self, event_type: str, payload: Any):
        """Handle service events"""
        if event_type == "publish_distance":
            self._publish_distance(payload)
        elif event_type == "publish_wave":
            self._publish_wave(payload)
        elif event_type == "publish_expression_playing":
            self._publish_expression_status(payload, "playing")
        elif event_type == "publish_expression_completed":
            self._publish_expression_status(payload, "completed")
        elif event_type == "message_received":
            self._handle_message(payload)
        else:
            self.logger.warning(f"Unknown event type: {event_type}")

    def _publish_distance(self, data: Dict[str, Any]):
        """Publish distance reading"""
        if not self.connected.is_set():
            return

        payload = json.dumps({
            "distance_m": data.get("distance_m", 0.0),
            "distance_cm": data.get("distance_m", 0.0) * 100,
            "timestamp": time.time(),
            "sensor_status": "ok"
        })

        self.client.publish(self.topics["distance"], payload, qos=0)
        self.logger.debug(f"Published distance: {payload}")

    def _publish_wave(self, data: Dict[str, Any]):
        """Publish wave detection event"""
        if not self.connected.is_set():
            return

        payload = json.dumps({
            "detected": True,
            "timestamp": time.time(),
            "trigger_type": data.get("trigger_type", "automatic"),
            "distance_at_detection": data.get("distance", 0.0),
            "velocity": data.get("velocity", 0.0)
        })

        self.client.publish(self.topics["wave"], payload, qos=1)
        self.logger.info(f"Published wave event: {payload}")

    def _publish_expression_status(self, expression: str, status: str):
        """Publish expression status (playing/completed)"""
        if not self.connected.is_set():
            return

        topic = self.topics[f"expression_{status}"]
        payload = json.dumps({
            "expression": expression,
            "timestamp": time.time()
        })

        self.client.publish(topic, payload, qos=0)
        self.logger.debug(f"Published expression {status}: {expression}")

    def _handle_message(self, data: Dict[str, Any]):
        """Handle received MQTT message"""
        topic = data.get("topic")
        payload = data.get("payload", {})

        # Route to appropriate callback
        if topic == self.topics["command_play"]:
            self._handle_command_play(payload)
        elif topic == self.topics["command_play_all"]:
            self._handle_command_play_all(payload)
        elif topic == self.topics["command_rgb"]:
            self._handle_command_rgb(payload)
        elif topic == self.topics["command_stop"]:
            self._handle_command_stop(payload)

    def _handle_command_play(self, payload: Dict[str, Any]):
        """Handle play expression command"""
        expression = payload.get("expression")
        if expression and "play_expression" in self.command_callbacks:
            self.logger.info(f"Received command to play expression: {expression}")
            self.command_callbacks["play_expression"](expression)

    def _handle_command_play_all(self, payload: Dict[str, Any]):
        """Handle play all expressions command"""
        if "play_all_expressions" in self.command_callbacks:
            self.logger.info("Received command to play all expressions")
            self.command_callbacks["play_all_expressions"]()

    def _handle_command_rgb(self, payload: Dict[str, Any]):
        """Handle RGB color command"""
        r = payload.get("r", 255)
        g = payload.get("g", 255)
        b = payload.get("b", 255)

        if "set_rgb" in self.command_callbacks:
            self.logger.info(f"Received command to set RGB: ({r}, {g}, {b})")
            self.command_callbacks["set_rgb"](r, g, b)

    def _handle_command_stop(self, payload: Dict[str, Any]):
        """Handle stop expression command"""
        if "stop_expression" in self.command_callbacks:
            self.logger.info("Received command to stop expression")
            self.command_callbacks["stop_expression"]()

    def register_callback(self, command: str, callback: Callable):
        """Register callback for MQTT command"""
        self.command_callbacks[command] = callback
        self.logger.info(f"Registered callback for command: {command}")

    def publish_distance_reading(self, distance_m: float):
        """Publish distance reading from sensor"""
        self.dispatch("publish_distance", {"distance_m": distance_m}, Priority.LOW)

    def publish_wave_event(self, distance: float = 0.0, velocity: float = 0.0):
        """Publish wave detection event"""
        self.dispatch("publish_wave", {
            "distance": distance,
            "velocity": velocity,
            "trigger_type": "automatic"
        }, Priority.HIGH)

    def publish_expression_playing(self, expression: str):
        """Publish expression now playing"""
        self.dispatch("publish_expression_playing", expression, Priority.NORMAL)

    def publish_expression_completed(self, expression: str):
        """Publish expression completed"""
        self.dispatch("publish_expression_completed", expression, Priority.NORMAL)

    def publish_online_status(self, online: bool):
        """Publish online/offline status"""
        if not self.client:
            return

        payload = json.dumps({
            "online": online,
            "lamp_id": self.lamp_id,
            "timestamp": time.time()
        })

        self.client.publish(self.topics["online"], payload, qos=1, retain=True)
        self.logger.info(f"Published online status: {online}")

    def wait_for_connection(self, timeout: float = 10.0) -> bool:
        """Wait for MQTT connection to be established"""
        return self.connected.wait(timeout)
