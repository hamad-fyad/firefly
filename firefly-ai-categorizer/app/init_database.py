#!/usr/bin/env python3
"""
Database initialization script for AI Categorizer service.
This script creates the necessary database tables if they don't exist.
"""
import logging
import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database_tables():
    """Initialize database tables for AI Categorizer."""
    try:
        logger.info("Starting database initialization...")
        
        # Try to import database components
        try:
            from app.database import init_database, test_connection, create_tables, engine
            from app.model_metrics import initialize_metrics_storage
        except ImportError as e:
            logger.error(f"Failed to import database components: {str(e)}")
            return False
        
        # Check if database is available
        if not engine:
            logger.warning("Database engine not available, skipping table creation")
            return False
            
        # Test connection
        if not test_connection():
            logger.warning("Database connection failed, skipping table creation")
            return False
            
        # Create tables
        if create_tables():
            logger.info("✅ Database tables created successfully")
            
            # Initialize metrics storage
            try:
                initialize_metrics_storage()
                logger.info("✅ Metrics storage initialized")
            except Exception as e:
                logger.warning(f"Metrics storage initialization failed: {str(e)}")
                
            return True
        else:
            logger.error("❌ Failed to create database tables")
            return False
            
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False

def main():
    """Main entry point for database initialization."""
    logger.info("AI Categorizer Database Initialization")
    logger.info("=====================================")
    
    success = init_database_tables()
    
    if success:
        logger.info("✅ Database initialization completed successfully")
        sys.exit(0)
    else:
        logger.warning("⚠️ Database initialization failed, service will use file storage fallback")
        sys.exit(0)  # Don't fail startup, just use fallback

if __name__ == "__main__":
    main()