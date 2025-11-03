from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from app.db import models
from app.db.database import engine
from app.api.routes import hazards, alerts, analytics, system
from app.core.mqtt_client import connect_mqtt, disconnect_mqtt

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup: Connect to MQTT broker
    try:
        connect_mqtt()
    except Exception as e:
        print(f"⚠ Warning: MQTT connection failed on startup: {str(e)}")
        print("⚠ Continuing without MQTT support...")
    
    yield
    
    # Shutdown: Disconnect from MQTT broker
    disconnect_mqtt()


app = FastAPI(
    title="A.V.I.D Imobilothon Backend",
    description="Backend API for road hazard detection and alerts",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(hazards.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(system.router, prefix="/api")


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": exc.errors()}
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


@app.get("/")
def root():
    return {"message": "Welcome to A.V.I.D Imobilothon Backend"}