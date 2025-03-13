from pydantic import BaseModel, Field

#IoT Sensors
class IoTSensorSchema(BaseModel):
    sensor_id: str = Field(..., max_length=20)
    station_code: str = Field(..., max_length=20)
    measurement_property: str = Field(..., pattern="^(temperature|humidity|wind)$")
