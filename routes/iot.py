import asyncio
import random
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db 

from models.sensor import IoTSensor 
from models.measurement import WeatherMeasurement 

router = APIRouter(prefix="/iot", tags=["IoT"])
iot_running = False

sensor_ids = [
    {"sensor_id": "ATH-TEMP", "station_code": "ATH-001", "measurement_property": "temperature"},
    {"sensor_id": "ATH-HUMI", "station_code": "ATH-001", "measurement_property": "humidity"},
    {"sensor_id": "ATH-WIND", "station_code": "ATH-001", "measurement_property": "wind"},
    {"sensor_id": "TIR-TEMP", "station_code": "TIR-001", "measurement_property": "temperature"},
    {"sensor_id": "TIR-HUMI", "station_code": "TIR-001", "measurement_property": "humidity"},
    {"sensor_id": "TIR-WIND", "station_code": "TIR-001", "measurement_property": "wind"},
    {"sensor_id": "LON-TEMP", "station_code": "LON-001", "measurement_property": "temperature"},
    {"sensor_id": "LON-HUMI", "station_code": "LON-001", "measurement_property": "humidity"},
    {"sensor_id": "LON-WIND", "station_code": "LON-001", "measurement_property": "wind"}
]

#simulate iot data as it is device
async def simulate_iot_data(db: AsyncSession):
    global iot_running
    while iot_running:
        try:
            for sensor in sensor_ids:
                if not iot_running:
                    return

                sensor_id = sensor.get("sensor_id")
                measurement_property_type = sensor.get("measurement_property")

                if not sensor_id or not measurement_property_type:
                    continue

                result = await db.execute(select(IoTSensor).where(IoTSensor.sensor_id == sensor_id))
                sensor_exists = result.scalar_one_or_none()

                if not sensor_exists:
                    print(f"⚠️ Sensor {sensor_id} does not exist in database, skipping...")
                    continue

                #create measurement data
                if measurement_property_type == "temperature":
                    measurement_value = round(random.uniform(-30.0, 45.0), 1)
                    category = "Temperature"
                    unit = "Celsius"
                elif measurement_property_type == "humidity":
                    measurement_value = round(random.uniform(10.0, 90.0), 1)
                    category = "Humidity"
                    unit = "%"
                elif measurement_property_type == "wind":
                    measurement_value = round(random.uniform(1.0, 50.0), 1)
                    category = "Wind"
                    unit = "m/s"
                else:
                    continue

                timestamp = datetime.utcnow()

                new_measurement = WeatherMeasurement(
                    measurement_id=uuid4(),
                    sensor_id=sensor_id,
                    measurement_value=measurement_value,
                    category=category,
                    timestamp=timestamp,
                    unit=unit
                )

                db.add(new_measurement)
                #new record is persisted
                await db.flush() 

            await db.commit()  
            print(f"-- IoT Data Inserted at {datetime.utcnow()}")

        except Exception as e:
            print(f"-xx- Error in IoT Data Simulation: {e}")

        await asyncio.sleep(10)  # ✅ Sleep before the next batch


@router.post("/start-iot")
async def start_iot(background_tasks: BackgroundTasks):
    global iot_running
    if iot_running:
        raise HTTPException(status_code=400, detail="IoT simulation is already running.")

    iot_running = True
    background_tasks.add_task(start_iot_background)  
    return {"message": "IoT simulation started."}

async def start_iot_background():
    """ Starts IoT data insertion in the background """
    async for db in get_db():
        await simulate_iot_data(db)
        break 


@router.post("/stop-iot")
async def stop_iot():
    global iot_running
    iot_running = False
    return {"message": "IoT simulation stopped."}
