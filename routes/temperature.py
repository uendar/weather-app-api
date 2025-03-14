import json
import csv
import io
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from datetime import date, timedelta, datetime
from database import get_db, get_redis
from models.measurement import WeatherMeasurement
from models.forecast import UserForecast
from schemas.temperature import TemperatureVisualizationSchema
import redis.asyncio as redis
from uuid import UUID
from decimal import Decimal
from typing import Dict, Optional
router = APIRouter(prefix="/temperature", tags=["Temperature Visualization"])


def custom_json_serializer(obj):
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime) or isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(
        f"Object of type {obj.__class__.__name__} is not JSON serializable")



#get actual (IoT) and predicted (forecast) temperature data
@router.get("/{city}", response_model=TemperatureVisualizationSchema)
async def get_city_temperature(
    city: str,
    days: int = Query(5, ge=1, le=15), 
    db: AsyncSession = Depends(get_db),
):
    redis_client = await get_redis()
    cache_key = f"temperature:{city.lower()}:{days}"

    # check redis
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)


    start_date = date.today() - timedelta(days=days)

    #actual IoT temperature (latest per day, no averaging)
    iot_subquery = (
        select(
            func.date(WeatherMeasurement.timestamp).label("date"),
            func.max(WeatherMeasurement.timestamp).label("latest_timestamp") 
        )
        .where(WeatherMeasurement.sensor_id.ilike(f"{city[:3].upper()}-%"))
        .where(WeatherMeasurement.category == "Temperature")
        .where(WeatherMeasurement.timestamp >= start_date)
        .group_by(func.date(WeatherMeasurement.timestamp))
        .subquery()
    )

    iot_result = await db.execute(
        select(
            WeatherMeasurement.timestamp,
            WeatherMeasurement.measurement_value.label("actual_temperature")
        )
        .join(
            iot_subquery,
            (WeatherMeasurement.timestamp == iot_subquery.c.latest_timestamp)
        )
        .order_by(WeatherMeasurement.timestamp.desc())  
    )

    iot_temperatures = {row.timestamp.date(): row.actual_temperature for row in iot_result}

    #get user predicted temperature (latest per day, no averaging)
    forecast_result = await db.execute(
        select(
            UserForecast.forecast_date,
            UserForecast.temperature.label("predicted_temperature")  
        )
        .where(UserForecast.city == city)
        .where(UserForecast.forecast_date >= start_date)
        .group_by(UserForecast.forecast_date, UserForecast.temperature)
        .order_by(UserForecast.forecast_date.desc())
    )
    forecast_temperatures = {row.forecast_date: row.predicted_temperature for row in forecast_result}

    #combine IoT and forecast data
    temperature_data = []
    for day_offset in range(days):
        temp_date = date.today() - timedelta(days=day_offset)
        temperature_data.append({
            "date": temp_date,
            "current_temperature": iot_temperatures.get(temp_date, None),
            "predicted_temperature": forecast_temperatures.get(temp_date, None)
        })

    response_data = {
        "city": city,
        "temperature_history": temperature_data
    }

    # store in Redis
    await redis_client.setex(cache_key, timedelta(minutes=10).seconds, json.dumps(response_data, default=custom_json_serializer))

    return response_data


#CSV file containing temperature data (actual & predicted)
@router.get("/{city}/download", response_class=Response)
async def download_city_temperature_csv(
    city: str,
    days: int = Query(5, ge=1, le=15),  
    db: AsyncSession = Depends(get_db)
):
    start_date = date.today() - timedelta(days=days)

    #actual IoT temperature (raw values per day)
    iot_result = await db.execute(
        select(
            func.date(WeatherMeasurement.timestamp).label("date"),
            WeatherMeasurement.measurement_value.label("actual_temperature")  
        )
        .where(WeatherMeasurement.sensor_id.ilike(f"{city[:3].upper()}-%"))
        .where(WeatherMeasurement.category == "Temperature")
        .where(WeatherMeasurement.timestamp >= start_date)
        .group_by(func.date(WeatherMeasurement.timestamp), WeatherMeasurement.measurement_value)
        .order_by(func.date(WeatherMeasurement.timestamp).desc())
    )
    iot_temperatures = {row.date: row.actual_temperature for row in iot_result}

    #get user-predicted temperature (raw values per day)
    forecast_result = await db.execute(
        select(
            UserForecast.forecast_date,
            UserForecast.temperature.label("predicted_temperature") 
        )
        .where(UserForecast.city == city)
        .where(UserForecast.forecast_date >= start_date)
        .group_by(UserForecast.forecast_date, UserForecast.temperature)
        .order_by(UserForecast.forecast_date.desc())
    )
    forecast_temperatures = {row.forecast_date: row.predicted_temperature for row in forecast_result}

    #merge data into CSV format
    csv_data = [["Date", "Current Temperature", "Predicted Temperature"]]
    for day_offset in range(days):
        temp_date = date.today() - timedelta(days=day_offset)
        csv_data.append([
            temp_date,
            iot_temperatures.get(temp_date, ""),
            forecast_temperatures.get(temp_date, "")
        ])

    #write CSV file
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(csv_data)
    output.seek(0)

    #CSV file
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{city}_temperature_history.csv"'}
    )
