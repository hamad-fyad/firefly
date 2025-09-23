import os
import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://firefly_user:firefly_password@localhost:5432/firefly_metrics"
)

# For AWS RDS, use this format:
# DATABASE_URL = "postgresql://username:password@your-rds-endpoint.region.rds.amazonaws.com:5432/database_name"

# Create SQLAlchemy engine
try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=300
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    engine = None
    SessionLocal = None

Base = declarative_base()

class ModelMetrics(Base):
    """Table for storing model training metrics."""
    __tablename__ = "model_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    metrics = Column(JSON, nullable=False)  # Store accuracy, precision, recall, f1_score
    training_size = Column(Integer, nullable=False)
    test_size = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class PredictionLogs(Base):
    """Table for storing individual prediction logs."""
    __tablename__ = "prediction_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    description = Column(Text, nullable=False)
    predicted_category = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    actual_category = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

def get_database_session():
    """Get database session with error handling."""
    if not SessionLocal:
        logger.error("Database not initialized")
        return None
    
    try:
        session = SessionLocal()
        return session
    except Exception as e:
        logger.error(f"Failed to create database session: {str(e)}")
        return None

def create_tables():
    """Create database tables if they don't exist."""
    if not engine:
        logger.error("Database engine not available")
        return False
        
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        return False

def test_connection() -> bool:
    """Test database connection."""
    if not engine:
        return False
        
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False

# AWS RDS specific functions
def setup_aws_rds():
    """Setup AWS RDS connection with proper configuration."""
    aws_settings = {
        'host': os.getenv('AWS_RDS_HOST', 'your-rds-endpoint.region.rds.amazonaws.com'),
        'port': os.getenv('AWS_RDS_PORT', '5432'),
        'database': os.getenv('AWS_RDS_DATABASE', 'firefly_metrics'),
        'username': os.getenv('AWS_RDS_USERNAME', 'firefly_user'),
        'password': os.getenv('AWS_RDS_PASSWORD', 'firefly_password'),
        'region': os.getenv('AWS_REGION', 'eu-west-1')
    }
    
    # Construct AWS RDS URL
    aws_database_url = (
        f"postgresql://{aws_settings['username']}:{aws_settings['password']}"
        f"@{aws_settings['host']}:{aws_settings['port']}/{aws_settings['database']}"
    )
    
    logger.info(f"AWS RDS Configuration: {aws_settings['host']}")
    return aws_database_url

def init_database():
    """Initialize database on startup."""
    logger.info("Initializing database...")
    
    # Test connection first
    if test_connection():
        logger.info("Database connection successful")
        # Create tables
        if create_tables():
            logger.info("Database initialization complete")
            return True
    
    logger.warning("Database initialization failed, falling back to file storage")
    return False