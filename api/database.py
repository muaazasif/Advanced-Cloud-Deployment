from sqlmodel import create_engine, Session, SQLModel
from .models import Task
import os

# Use environment variable for database URL, fallback to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
