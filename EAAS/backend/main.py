from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import register
from routes.rooms import room_creation
from routes.websockets import websocket
from utils.logging_config import get_logger

# Initialize logger for main application
logger = get_logger("main")

app = FastAPI(
    title="EAAS",
    description="Backend API for Escrow as A service WebAPP",
    version="1.0.0",
)

# Log application startup
logger.info("Starting EAAS")

origins = [
    "http://localhost",
    "http://localhost:5173",
    "https://eaas.vercel.app",
]  # TODO: Change this
logger.info(f"Configuring CORS with origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with logging
logger.info("Registering API routes")

app.include_router(register.router, prefix="/api")
logger.debug("Registered user_creation router at /api")

app.include_router(websocket.router, prefix="/api")
logger.debug("Registered websocket router at /api")

app.include_router(room_creation.router, prefix="/api")
logger.debug("Registered room_creation router at /api")

logger.info("Application startup completed successfully")
