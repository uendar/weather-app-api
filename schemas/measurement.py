import uuid
from pydantic import BaseModel, Field
from datetime import datetime

# structure from IoT response
class IoTMeasurementInfoSchema(BaseModel):
    category: str
    measurement: float
    unit: str

class IoTMeasurementSchema(BaseModel):
    measurement_id: uuid.UUID
    sensor_id: str
    date: datetime
    station: str
    info: IoTMeasurementInfoSchema

class WeatherMeasurementSchema(BaseModel):
    measurement_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    sensor_id: str = Field(..., max_length=20)
    measurement_value: float
    category: str = Field(..., pattern="^(Temperature|Humidity|Wind)$")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    unit: str = Field(..., max_length=20)
