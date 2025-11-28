from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth
from .database import init_db
from .config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Password Reset API",
    description="Backend API for forgot password functionality",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Build list of allowed origins
allowed_origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative dev port
]

# Add production frontend URL if configured
if settings.FRONTEND_URL:
    allowed_origins.append(settings.FRONTEND_URL)
    logger.info(f"Added FRONTEND_URL to CORS: {settings.FRONTEND_URL}")

# In production, also allow common Render URL patterns
if settings.ENVIRONMENT == "production":
    allowed_origins.extend([
        "https://*.onrender.com",
    ])

logger.info(f"CORS allowed origins: {allowed_origins}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # Set to False to allow wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Password Reset API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}
