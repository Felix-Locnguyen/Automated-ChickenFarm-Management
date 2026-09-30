from sqlalchemy.orm import Session
from ...models.device import Device
from ..01_mqtt.handler import MQTTHandler
import logging

logger = logging.getLogger(__name__)

class CommandExecutor:
    def __init__(self, db: Session, mqtt_handler: MQTTHandler):
        self.db = db
        self.mqtt = mqtt_handler

    def send_command(self, device_id: int, command: str, params: dict = None):
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device:
            logger.error(f"Device {device_id} not found")
            return False

        topic = f"farm/device/{device_id}/command"
        payload = {
            "command": command,
            "device_type": device.type,
            "params": params or {}
        }

        if self.mqtt.connected:
            self.mqtt.publish(topic, payload)
            logger.info(f"Sent command '{command}' to device {device_id}")
            return True
        else:
            logger.warning(f"MQTT not connected, cannot send command to device {device_id}")
            return False

    def toggle_device(self, device_id: int):
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return False

        new_state = not device.is_active
        command = "ON" if new_state else "OFF"

        success = self.send_command(device_id, command)
        if success:
            device.is_active = new_state
            device.status = "online" if new_state else "offline"
            self.db.commit()

        return success

    def set_fan_speed(self, device_id: int, speed: int):
        return self.send_command(device_id, "SET_SPEED", {"speed": speed})

    def set_feeder_amount(self, device_id: int, amount_kg: float):
        return self.send_command(device_id, "FEED", {"amount_kg": amount_kg})
