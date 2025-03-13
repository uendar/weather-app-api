import uuid
from sqlalchemy import Column, UUID, String, DECIMAL, TIMESTAMP, Date, func
import uuid
from models.base import Base

class UserForecast(Base):
    __tablename__ = "user_forecasts"

    forecast_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) 
    forecast_date = Column(Date, nullable=False)
    city = Column(String(100), nullable=False)
    temperature = Column(DECIMAL(10,2), nullable=False)
    humidity = Column(DECIMAL(10,2), nullable=False)
    wind = Column(DECIMAL(10,2), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False) 
