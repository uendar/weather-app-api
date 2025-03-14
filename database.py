import os
import redis.asyncio as redis
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models import Base

load_dotenv()

# PostgreSQL & Redis URLs from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://weather-redis:6379")

if not DATABASE_URL:
    raise ValueError("Missing DATABASE_URL in environment variables!")

# init PostgreSQL database connection
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# init Redis
redis_client = None


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

