from sqlalchemy import Column, String, DECIMAL, Date
from models.base import Base

class Station(Base):
    __tablename__ = "stations"

    code = Column(String(20), primary_key=True)
    city = Column(String(50), nullable=False)
    latitude = Column(DECIMAL(9,6), nullable=False)
    longitude = Column(DECIMAL(9,6), nullable=False)
    installation_date = Column(Date, nullable=False)
