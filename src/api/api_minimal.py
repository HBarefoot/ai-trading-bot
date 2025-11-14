"""
Minimal API Backend for Testing Deployment
This is a simplified version to ensure basic deployment works
"""
from fastapi import FastAPI
from datetime import datetime
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Trading Bot API - Minimal",
    description="Minimal version for deployment testing",
    version="3.0.0-minimal"
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AI Trading Bot API - Minimal", 
        "version": "3.0.0-minimal",
        "status": "online",
        "timestamp": datetime.now()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway deployment"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now(),
        "service": "AI Trading Bot API - Minimal",
        "version": "3.0.0-minimal"
    }

@app.get("/api/status")
async def get_status():
    """Get system status - minimal version"""
    return {
        "status": "running",
        "timestamp": datetime.now(),
        "trading_engine": "stopped",
        "paper_trading": True,
        "mode": "MINIMAL DEPLOYMENT TEST",
        "exchange": "disconnected", 
        "data_feed": "inactive"
    }

@app.on_event("startup")
async def startup_event():
    """Minimal startup - no complex dependencies"""
    logger.info("Minimal API started successfully!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)