from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# 1  USERS
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    created_at: datetime

    class Config:
        orm_mode = True


# 2   FLOCK
class FlockCreate(BaseModel):
    name: str
    chicken_count: int
    breed: Optional[str] = None
    age_weeks: Optional[int] = None
    coop_number: Optional[int] = None

class FlockResponse(BaseModel):
    id: int
    name: str
    chicken_count: int
    breed: Optional[str]
    age_weeks: Optional[int]
    coop_number: Optional[int]
    owner_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# 3   SENSOR
class SensorReadingCreate(BaseModel):
    temperature: float
    humidity: float
    food_level: float
    water_level: float
    device_id: int

class SensorReadingResponse(BaseModel):
    id: int
    temperature: float
    humidity: float
    food_level: float
    water_level: float
    device_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# 4   FEEDING
class FeedingLogCreate(BaseModel):
    feed_type: str
    amount_kg: float
    scheduled_time: str
    flock_id: int

class FeedingLogResponse(BaseModel):
    id: int
    feed_type: str
    amount_kg: float
    scheduled_time: str
    status: str
    flock_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# 5   ALERT
class AlertResponse(BaseModel):
    id: int
    type: str
    severity: str
    message: Optional[str]
    is_resolved: bool
    flock_id: Optional[int]
    device_id: Optional[int]
    created_at: datetime

    class Config:
        orm_mode = True


# 6   HEALTH RECORD
class HealthRecordCreate(BaseModel):
    record_type: str
    description: Optional[str] = None
    veterinarian: Optional[str] = None
    flock_id: int

class HealthRecordResponse(BaseModel):
    id: int
    record_type: str
    description: Optional[str]
    veterinarian: Optional[str]
    flock_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# 7   DEVICE
class DeviceCreate(BaseModel):
    name: str
    type: str
    flock_id: int

class DeviceResponse(BaseModel):
    id: int
    name: str
    type: str
    status: str
    is_active: bool
    flock_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# 8   FINANCIAL RECORD
class FinancialRecordCreate(BaseModel):
    flock_id: int
    date: datetime
    quantity_before: int
    cost_per_chick: float = 0
    dead_chickens: int = 0
    sold_chickens: int = 0
    unit_price: float = 0
    feed_cost: float = 0
    other_cost: float = 0
    note: Optional[str] = None


class FinancialRecordResponse(BaseModel):
    id: int
    flock_id: int
    date: datetime
    quantity_before: int
    cost_per_chick: float
    dead_chickens: int
    sold_chickens: int
    unit_price: float
    feed_cost: float
    other_cost: float
    depreciation_cost: float
    revenue: float
    total_cost: float
    profit: float
    note: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
