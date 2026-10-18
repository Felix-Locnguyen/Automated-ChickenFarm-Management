from sqlalchemy.orm import Session
from ...models.device import Device
from ...models.flock import Flock
import logging

logger = logging.getLogger(__name__)

class DeviceManager:
    def __init__(self, db: Session):
        self.db = db

    def register_device(self, name: str, device_type: str, flock_id: int):
        flock = self.db.query(Flock).filter(Flock.id == flock_id).first()
        if not flock:
            logger.error(f"Flock {flock_id} not found")
            return None

        device = Device(name=name, type=device_type, flock_id=flock_id, status="offline")
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        logger.info(f"Registered device: {device.name} (id={device.id})")
        return device

    def get_device(self, device_id: int):
        return self.db.query(Device).filter(Device.id == device_id).first()

    def get_devices_by_flock(self, flock_id: int):
        return self.db.query(Device).filter(Device.flock_id == flock_id).all()

    def update_device_status(self, device_id: int, status: str):
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if device:
            device.status = status
            self.db.commit()
            logger.info(f"Updated device {device_id} status to {status}")
        return device

    def remove_device(self, device_id: int):
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if device:
            self.db.delete(device)
            self.db.commit()
            logger.info(f"Removed device {device_id}")
            return True
        return False

    def get_all_active_devices(self):
        return self.db.query(Device).filter(Device.is_active == True).all()
