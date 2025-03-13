from datetime import date
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models.forecast import UserForecast
from schemas.forecast import UserForecastCreateSchema, UserForecastUpdateSchema, UserForecastResponseSchema

router = APIRouter(prefix="/forecasts", tags=["User Forecasts"])

#CREATE FORECAST
@router.post("/")
async def create_forecast(
    forecast: UserForecastCreateSchema, db: AsyncSession = Depends(get_db)
):

    today = date.today() 

    #check if a forecast for this city and date already exists
    existing_forecast = await db.execute(
        select(UserForecast).where(
            (UserForecast.forecast_date == today) &
            (UserForecast.city == forecast.city)
        )
    )
    if existing_forecast.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Only one forecast per city per day is allowed.")

    #add forecast
    new_forecast = UserForecast(
        forecast_id=uuid.uuid4(), 
        forecast_date=today,
        city=forecast.city,
        temperature=forecast.temperature,
        humidity=forecast.humidity,
        wind=forecast.wind
    )
    db.add(new_forecast)
    await db.commit()
    await db.refresh(new_forecast)
    return new_forecast

#UPDATE FORECAST
@router.put("/{forecast_id}", response_model=UserForecastResponseSchema)
async def update_forecast(
    forecast_id:  uuid.UUID, forecast_update: UserForecastUpdateSchema, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserForecast).where(UserForecast.forecast_id == forecast_id))
    forecast = result.scalar_one_or_none()

    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")

    #adding updates
    for key, value in forecast_update.dict(exclude_unset=True).items():
        setattr(forecast, key, value)

    await db.commit()
    await db.refresh(forecast)
    return forecast


#DELETE FORECAST
@router.delete("/{forecast_id}")
async def delete_forecast(forecast_id:  uuid.UUID, db: AsyncSession = Depends(get_db)):
    #get the forecast by ID
    result = await db.execute(select(UserForecast).where(UserForecast.forecast_id == forecast_id))
    forecast = result.scalar_one_or_none()

    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")

    #remove forecast
    await db.delete(forecast)
    await db.commit()
    return {"message": f"Forecast with ID {forecast_id} deleted successfully"}