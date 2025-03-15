from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import iot_router, forecasts_router, weather_router, temperature_router
from database import init_db

app = FastAPI()


# enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routes
app.include_router(iot_router)
app.include_router(forecasts_router)
app.include_router(weather_router)
app.include_router(temperature_router)

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/")
def read_root():
    return {"message": "FastAPI Weather Backend is Running!"}
