from datetime import timedelta
from datetime import date, timedelta
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import desc
from database import get_db, get_redis
from models.forecast import UserForecast
from schemas.forecast import UserForecastCreateSchema, UserForecastResponseSchema, UserForecastUpdateSchema
from uuid import UUID
from decimal import Decimal
from typing import List


router = APIRouter(prefix="/forecasts", tags=["User Forecasts"])

# serializer for UUID, Decimal, Date


def custom_json_serializer(obj):
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(
        f"Object of type {obj.__class__.__name__} is not JSON serializable")


# fetch 3-7 latest forecasts for a city
@router.get("/", response_model=List[UserForecastResponseSchema])
async def get_forecasts(
    city: str = Query(..., title="City Name",
                      description="Fetch forecasts for this city"),
    limit: int = Query(3, ge=3, le=7, title="Limit",
                       description="Number of forecasts to retrieve (default: 3, range: 3-7)"),
    db: AsyncSession = Depends(get_db)
):
    redis_client = await get_redis()
    cache_key = f"forecasts:{city.lower()}:{limit}"

    # check redis cache
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    # querry forecasts from DB
    query = (
        select(UserForecast)
        .where(UserForecast.city == city)
        .order_by(desc(UserForecast.forecast_date))
        .limit(limit)
    )
    result = await db.execute(query)
    forecasts = result.scalars().all()

    if not forecasts:
        raise HTTPException(
            status_code=404, detail=f"No forecasts found for {city}")

    # serialize response data
    response_data = [UserForecastResponseSchema.model_validate(
        f).model_dump() for f in forecasts]

    # store redis 5 min
    await redis_client.setex(cache_key, 300, json.dumps(response_data, default=custom_json_serializer))

    return response_data


# create new forecast
@router.post("/", response_model=UserForecastResponseSchema)
async def create_forecast(forecast: UserForecastCreateSchema, db: AsyncSession = Depends(get_db)):
    today = date.today()
    tomorrow = today + timedelta(days=1)

    # check if a forecast for this city & date already exists
    existing_forecast = await db.execute(
        select(UserForecast)
        .where(UserForecast.forecast_date == tomorrow)
        .where(UserForecast.city == forecast.city)
    )
    existing_forecast = existing_forecast.scalar_one_or_none()

    if existing_forecast:
        raise HTTPException(
            status_code=400, detail="Only one forecast per city is allowed for the next coming day.")

    # new forecast
    new_forecast = UserForecast(
        forecast_id=str(uuid.uuid4()),
        forecast_date=tomorrow,
        city=forecast.city,
        temperature=forecast.temperature,
        humidity=forecast.humidity,
        wind=forecast.wind
    )
    db.add(new_forecast)
    await db.commit()
    await db.refresh(new_forecast)

    redis_client = await get_redis()

    # invalidate forecast cache
    forecast_pattern = f"forecasts:{forecast.city.lower()}:*"
    forecast_keys = await redis_client.keys(forecast_pattern)
    if forecast_keys:
        await redis_client.delete(*forecast_keys)

    # check if weather exists
    weather_cache_key = f"weather:{forecast.city.lower()}"
    cached_weather = await redis_client.get(weather_cache_key)

    if cached_weather:
        weather_data = json.loads(cached_weather)

        # update user_forecast if it exists inside weather cache
        if "user_forecast" in weather_data:
            weather_data["user_forecast"] = {
                "forecast_id": str(new_forecast.forecast_id),
                "forecast_date": new_forecast.forecast_date.isoformat(),
                "city": new_forecast.city,
                "temperature": new_forecast.temperature,
                "humidity": new_forecast.humidity,
                "wind": new_forecast.wind
            }

            # store updated data
            await redis_client.setex(
                weather_cache_key,
                timedelta(minutes=10).seconds,  # Cache expiration time
                json.dumps(weather_data, default=custom_json_serializer)
            )

    return new_forecast

# update an existing forecast
@router.put("/{forecast_id}", response_model=UserForecastResponseSchema)
async def update_forecast(
    forecast_id: UUID,
    forecast_update: UserForecastUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    redis_client = await get_redis()

    # fetch existing forecast from db
    result = await db.execute(select(UserForecast).where(UserForecast.forecast_id == forecast_id))
    forecast = result.scalar_one_or_none()

    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")

    # partial update for field sent
    for key, value in forecast_update.dict(exclude_unset=True).items():
        setattr(forecast, key, value)

    await db.commit()
    await db.refresh(forecast)

    # invalidate redis cache
    forecast_cache_pattern = f"forecasts:{forecast.city.lower()}:*"
    forecast_keys = await redis_client.keys(forecast_cache_pattern)
    if forecast_keys:
        await redis_client.delete(*forecast_keys)

    # check and update redis data
    weather_cache_key = f"weather:{forecast.city.lower()}"
    cached_weather = await redis_client.get(weather_cache_key)

    if cached_weather:
        weather_data = json.loads(cached_weather)

        # check if cached forecast is the same one being updated
        if weather_data.get("user_forecast") and weather_data["user_forecast"]["forecast_id"] == str(forecast_id):
            weather_data["user_forecast"].update({
                "temperature": forecast.temperature,
                "humidity": forecast.humidity,
                "wind": forecast.wind,
                "forecast_date": forecast.forecast_date.isoformat(),
            })

            await redis_client.setex(
                weather_cache_key, timedelta(minutes=10).seconds,
                json.dumps(weather_data, default=custom_json_serializer)
            )

    return forecast

# Remove a forecast
@router.delete("/{forecast_id}")
async def delete_forecast(forecast_id: UUID, db: AsyncSession = Depends(get_db)):

    redis_client = await get_redis()

    result = await db.execute(select(UserForecast).where(UserForecast.forecast_id == forecast_id))
    forecast = result.scalar_one_or_none()

    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")

    city = forecast.city

    await db.delete(forecast)
    await db.commit()

    # check if this deleted forecast is stored
    weather_cache_key = f"weather:{city.lower()}"
    cached_weather = await redis_client.get(weather_cache_key)

    if cached_weather:
        weather_data = json.loads(cached_weather)

        # remove cached forecast data if stored and data  is the one being deleted
        if weather_data.get("user_forecast") and weather_data["user_forecast"]["forecast_id"] == str(forecast_id):
            await redis_client.delete(weather_cache_key)

    # delete all cached
    forecast_cache_pattern = f"forecasts:{city.lower()}:*"
    forecast_cache_keys = await redis_client.keys(forecast_cache_pattern)
    if forecast_cache_keys:
        await redis_client.delete(*forecast_cache_keys)

    return {"message": f"Forecast with ID {forecast_id} deleted successfully"}