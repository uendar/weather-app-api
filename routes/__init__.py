from .iot import router as iot_router
from .forecasts import router as forecasts_router
from .weather import router as weather_router
from .temperature import router as temperature_router

__all__ = ["iot_router", "forecasts_router", "weather_router", "temperature_router"]
