from sqlalchemy import Column, String, ForeignKey
from models.base import Base

class IoTSensor(Base):
    __tablename__ = "iot_sensors"

    sensor_id = Column(String(20), primary_key=True)
    station_code = Column(String(20), ForeignKey("stations.code", ondelete="CASCADE"), nullable=False)
    measurement_property = Column(String(20), nullable=False)
