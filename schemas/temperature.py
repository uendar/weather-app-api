from typing import List, Optional
from pydantic import BaseModel
from datetime import date

class TemperatureRecordSchema(BaseModel):
    date: date
    current_temperature: Optional[float]
    predicted_temperature: Optional[float]

class TemperatureVisualizationSchema(BaseModel):
    city: str
    temperature_history: List[TemperatureRecordSchema]
