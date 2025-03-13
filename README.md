# FastAPI Weather Backend

A **FastAPI-based backend** that collects and manages weather data from IoT sensors and user-submitted forecasts. The application is **Dockerized** and runs independently of the platform.

## Features
- Collect **real-time weather data** from IoT sensors.
- Allow users to **submit daily forecasts**.
- Compare **actual vs. predicted weather**.
- Generate a **CSV file** for historical temperature visualization.
- Uses **PostgreSQL** as the database.
- **Dockerized** for easy deployment.

---
## 📌 Project Setup

### 1️⃣ Clone the Repository
```sh
git clone https://github.com/uendar/weather-app-api.git
cd fastapi-weather-backend
```

### 2️⃣ Setup Environment Variables
Create a `.env` file in the root directory:
```sh
touch .env
```
Add the following content inside `.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:your_password@db:5432/weather_db
```

---
## 🐳 Running the Project with Docker

### 3️⃣ Build and Start the Containers
```sh
docker compose up --build
```
This will start **PostgreSQL** and the **FastAPI backend** inside Docker.

### 4️⃣ Stop the Containers
```sh
docker compose down
```
This will stop all running containers.

---
## 🛠 Running the Project Locally (Without Docker)

### 1️⃣ Install Dependencies
```sh
pip install -r requirements.txt
```

### 2️⃣ Start FastAPI Server
```sh
uvicorn main:app --reload
```

### 3️⃣ Run PostgreSQL Locally (if needed)
Make sure you have **PostgreSQL installed** and running on your system.

---
## 📂 Project Structure
```
fastapi-weather-backend/
│── migrations/         # Database migrations
│── models/             # SQLAlchemy database models
│── routes/             # API route handlers
│── schemas/            # Pydantic schemas for validation
│── services/           # Business logic services
│── .dockerignore       # Docker ignore file
│── .gitignore          # Git ignore file
│── docker-compose.yml  # Docker Compose file
│── Dockerfile          # Docker build file
│── database.py         # Database configuration
│── main.py             # FastAPI entry point
│── requirements.txt    # Python dependencies
│── README.md           # Project documentation
```

---
## 📡 API Endpoints

| Method  | Endpoint                 | Description                                      |
|---------|--------------------------|--------------------------------------------------|
| `GET`   | `/weather/{city}`        | Fetch current & predicted weather for a city    |
| `POST`  | `/forecasts`             | Submit a user weather forecast                  |
| `PUT`   | `/forecasts/{id}`        | Update an existing forecast                     |
| `DELETE`| `/forecasts/{id}`        | Delete a forecast                               |
| `GET`   | `/temperature/{city}`    | Get past weather temperature (actual & forecast)|
| `GET`   | `/temperature/{city}/download` | Download CSV with temperature data     |
| `POST`  | `/iot/start-iot`         | Start IoT data simulation                        |
| `POST`  | `/iot/stop-iot`          | Stop IoT data simulation                         |

---
## 📝 Testing API with Postman
1. Open **Postman**.
2. Import API collection using: `http://localhost:8000/docs` (FastAPI auto-generated docs).
3. Test API endpoints with **localhost:8000**.

---
## 🔗 Useful Commands

### View Container Logs:
```sh
docker logs fastapi-weather-backend
```
### Check Running Containers
```sh
docker ps
```

### View Container Logs
```sh
docker logs fastapi-weather-backend
```

### Connect to PostgreSQL Inside Docker
```sh
docker exec -it weather-db psql -U postgres -d weather_db
```

### Run Alembic Migrations
```sh
alembic upgrade head
```

---
## 🛠 Technologies Used
- **FastAPI** - Web framework
- **PostgreSQL** - Database
- **Docker** - Containerization
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server



