"""
This module defines the database connection
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = f"postgresql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=1,
    max_overflow=4,
    connect_args={
        "application_name": "lawplus-langgraph-agent"
    },
)
Session = sessionmaker(bind=engine)

__all__ = ["Session"]