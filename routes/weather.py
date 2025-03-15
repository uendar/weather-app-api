import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func, and_
from sqlalchemy.orm import aliased
from datetime import date, timedelta, datetime
from database import get_db, get_redis
from models.measurement import WeatherMeasurement
from models.forecast import UserForecast
from schemas.weather import WeatherWidgetResponseSchema, CurrentWeatherSchema
from schemas.measurement import IoTMeasurementSchema
from schemas.forecast import UserForecastResponseSchema
from typing import Dict, Optional
from uuid import UUID
from decimal import Decimal

router = APIRouter(prefix="/weather", tags=["Weather Widget"])

# serialize JSON objects
def custom_json_serializer(obj):
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(
        f"Object of type {obj.__class__.__name__} is not JSON serializable")


# IoT data + user forecast with Redis caching
@router.get("/{city}", response_model=WeatherWidgetResponseSchema)
async def get_weather_widget(
    city: str,
    db: AsyncSession = Depends(get_db)
):
    redis_client = await get_redis()
    cache_key = f"weather:{city.lower()}"
    user_forecast_alias = aliased(UserForecast)

    # check Redis cache first
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)


    # fetch latest IoT weather data
    subquery = (
        select(
            WeatherMeasurement.category,
            func.max(WeatherMeasurement.timestamp).label("latest_timestamp"),
        )
        .where(WeatherMeasurement.sensor_id.ilike(f"{city[:3].upper()}-%"))
        .group_by(WeatherMeasurement.category)
        .subquery()
    )

    result = await db.execute(
        select(WeatherMeasurement)
        .join(
            subquery,
            and_(
                WeatherMeasurement.category == subquery.c.category,
                WeatherMeasurement.timestamp == subquery.c.latest_timestamp,
            ),
        )
        .join(
            user_forecast_alias,
            user_forecast_alias.city == city
        )
        .where(WeatherMeasurement.sensor_id.ilike(f"{city[:3].upper()}-%"))
    )

    latest_weather_data = result.scalars().all()
    weather_data_dict: Dict[str, Optional[IoTMeasurementSchema]] = {}

    for measurement in latest_weather_data:
        category = measurement.category.lower()
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

    # fetch latest user forecast for today
    today = date.today()
    tomorrow = today + timedelta(days=1)

    forecast_result = await db.execute(
        select(UserForecast)
        .where(UserForecast.city == city)
        .where(UserForecast.forecast_date == tomorrow)
    )
    latest_forecast = forecast_result.scalar_one_or_none()

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

    #  final response
    response_data = WeatherWidgetResponseSchema(
        city=city,
        current_weather=current_weather if latest_weather_data else None,
        user_forecast=forecast_data
    ).model_dump()

    # store in Redis for 10min
    await redis_client.setex(cache_key, timedelta(minutes=10).seconds, json.dumps(response_data, default=custom_json_serializer))

    return response_data
