from typing import Optional
from pydantic import BaseModel
from schemas.measurement import IoTMeasurementSchema
from schemas.forecast import UserForecastResponseSchema

#returning grouped IoT weather data
class CurrentWeatherSchema(BaseModel):
    temperature: Optional[IoTMeasurementSchema] = None
    humidity: Optional[IoTMeasurementSchema] = None
    wind: Optional[IoTMeasurementSchema] = None

class WeatherWidgetResponseSchema(BaseModel):
    city: str
    current_weather: Optional[CurrentWeatherSchema] = None
    user_forecast: Optional[UserForecastResponseSchema] = None
