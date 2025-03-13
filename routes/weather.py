from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func, and_
from datetime import date
from database import get_db
from models.measurement import WeatherMeasurement
from models.forecast import UserForecast
from schemas.weather import WeatherWidgetResponseSchema, CurrentWeatherSchema
from schemas.measurement import IoTMeasurementSchema
from schemas.forecast import UserForecastResponseSchema


from typing import Dict, Optional

router = APIRouter(prefix="/weather", tags=["Weather Widget"])


#IOT data weather + user forecast
  
@router.get("/{city}", response_model=WeatherWidgetResponseSchema)
async def get_weather_widget(city: str, db: AsyncSession = Depends(get_db)):
   

    #get the latest IoT weather data for the city
    subquery = (
        select(
            WeatherMeasurement.category,
            func.max(WeatherMeasurement.timestamp).label("latest_timestamp"),
        )
        .where(WeatherMeasurement.sensor_id.ilike(f"{city[:3].upper()}-%"))
        .group_by(WeatherMeasurement.category)
        .subquery()
    )

    #get only the most recent measurement per category
    result = await db.execute(
        select(WeatherMeasurement)
        .join(
            subquery,
            and_(
                WeatherMeasurement.category == subquery.c.category,
                WeatherMeasurement.timestamp == subquery.c.latest_timestamp,
            ),
        )
        .where(WeatherMeasurement.sensor_id.ilike(f"{city[:3].upper()}-%"))
    )

    latest_weather_data = result.scalars().all()

    #organize IoT data into response format
    weather_data_dict: Dict[str, Optional[IoTMeasurementSchema]] = {}

    for measurement in latest_weather_data:
        category = measurement.category.lower()

        #store only the latest measurement per category
        weather_data_dict[category] = IoTMeasurementSchema(
            measurement_id=measurement.measurement_id,
            sensor_id=measurement.sensor_id,
            date=measurement.timestamp,
            station=measurement.sensor_id.split("-")[0],
            info={
                "category": measurement.category,
                "measurement": measurement.measurement_value,
                "unit": measurement.unit
            }
        )

    #convert IoT data into correct response format
    current_weather = CurrentWeatherSchema(
        temperature=weather_data_dict.get("temperature"),
        humidity=weather_data_dict.get("humidity"),
        wind=weather_data_dict.get("wind")
    )

    #latest user forecast for today
    today = date.today()
    forecast_result = await db.execute(
        select(UserForecast)
        .where(UserForecast.city == city)
        .where(UserForecast.forecast_date == today)
    )
    latest_forecast = forecast_result.scalar_one_or_none()

    #conver forecast into correct format checking also missing forecast
    forecast_data = None
    if latest_forecast:
        forecast_data = UserForecastResponseSchema(
            forecast_id=latest_forecast.forecast_id,
            forecast_date=latest_forecast.forecast_date,
            city=latest_forecast.city,
            temperature=latest_forecast.temperature,
            humidity=latest_forecast.humidity,
            wind=latest_forecast.wind,
        ).model_dump()


    return WeatherWidgetResponseSchema(
        city=city,
        current_weather=current_weather if latest_weather_data else None,
        user_forecast=forecast_data
    )
