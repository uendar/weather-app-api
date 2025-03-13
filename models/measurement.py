import uuid
from sqlalchemy import Column, String, DECIMAL, TIMESTAMP, ForeignKey, UUID
from datetime import datetime
import uuid
from models.base import Base

class WeatherMeasurement(Base):
    __tablename__ = "weather_measurements"

    measurement_id = Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    sensor_id = Column(String(20), ForeignKey("iot_sensors.sensor_id", ondelete="CASCADE"), nullable=False)
    measurement_value = Column(DECIMAL(10,2), nullable=False)
    category = Column(String(50), nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    unit = Column(String(20), nullable=False)
