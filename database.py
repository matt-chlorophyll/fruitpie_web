from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Define the database URL. Uses environment variable or defaults to a local SQLite file.
# For local development, this will create a file named 'fruitpie.db' in the same directory as this script.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fruitpie.db")

# Create the SQLAlchemy engine
# The connect_args is recommended for SQLite to prevent issues with FastAPI/Uvicorn's threading.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class, which will be used to create database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for our models to inherit from
Base = declarative_base()

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 