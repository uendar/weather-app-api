from pydantic import BaseModel, Field
from datetime import datetime

# stations
class StationSchema(BaseModel):
    code: str = Field(..., max_length=20)
    city: str = Field(..., max_length=50)
    latitude: float
    longitude: float
    installation_date: datetime
