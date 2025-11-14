#!/usr/bin/env python3
"""
Railway Startup Wrapper
Provides detailed error reporting for deployment debugging
"""
import os
import sys
import traceback
import logging
from pathlib import Path

# Configure logging to see startup issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("=== AI Trading Bot Startup ===")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Python path: {sys.path}")
        
        # Check if we're in the right directory
        current_dir = Path.cwd()
        logger.info(f"Current directory: {current_dir}")
        logger.info(f"Directory contents: {list(current_dir.iterdir())}")
        
        # Add src to path
        src_path = current_dir / "src"
        if src_path.exists():
            sys.path.insert(0, str(src_path))
            logger.info(f"Added {src_path} to Python path")
        else:
            logger.error(f"src directory not found at {src_path}")
        
        # Check environment variables
        port = os.getenv('PORT', '8000')
        logger.info(f"Using port: {port}")
        
        # Import and start the API
        logger.info("Importing FastAPI app...")
        from api.api_backend import app
        logger.info("✅ FastAPI app imported successfully")
        
        # Start with uvicorn
        logger.info("Starting uvicorn server...")
        import uvicorn
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=int(port),
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        logger.error("Full traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()