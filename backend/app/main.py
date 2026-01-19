"""
FastAPI Application Entry Point
Coffee-Berry Stores Management System
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.api.routes import stores, polygons, geospatial, franchisees, schedules, media, auth
from app.db.database import engine, Base


# Create database tables on startup (in production, use migrations)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.environment == "development":
        # Only create tables in development
        Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    pass


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Coffee-Berry Stores Management System API",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(stores.router, prefix="/api/v1/stores", tags=["Stores"])
app.include_router(polygons.router, prefix="/api/v1/polygons", tags=["Polygons"])
app.include_router(geospatial.router, prefix="/api/v1/geospatial", tags=["Geospatial"])
app.include_router(franchisees.router, prefix="/api/v1/franchisees", tags=["Franchisees"])
app.include_router(schedules.router, prefix="/api/v1/schedules", tags=["Schedules"])
app.include_router(media.router, prefix="/api/v1/media", tags=["Media"])


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Coffee-Berry Stores Management API",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Documentation disabled in production"
    }


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )
