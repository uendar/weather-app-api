import uuid
from typing import Optional
from pydantic import BaseModel, Field
from datetime import date

# user-submitted forecasts
class UserForecastCreateSchema(BaseModel):
    city: str = Field(..., max_length=100)
    temperature: float
    humidity: float = Field(..., ge=0, le=100)
    wind: float = Field(..., ge=0)

class UserForecastUpdateSchema(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = Field(None, ge=0, le=100)
    wind: Optional[float] = Field(None, ge=0)

class UserForecastResponseSchema(UserForecastCreateSchema):
    forecast_id: uuid.UUID
    forecast_date: date

    class Config:
        from_attributes = True
