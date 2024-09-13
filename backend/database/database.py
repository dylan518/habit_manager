from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import sys

# Import your models
from backend.database.models import Base  # Make sure to import Base and all your models

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Load the .env file (optional)
load_dotenv()

# Determine the database file path
db_file = resource_path("database.db")
db_exists = os.path.exists(db_file)

if not db_exists:
    print(f"No existing database found at {db_file}. Creating a new SQLite database...")

# Use SQLite as the database
DATABASE_PATH = f"sqlite:///{db_file}"

# Create the SQLAlchemy engine for SQLite
engine = create_engine(DATABASE_PATH, connect_args={"check_same_thread": False})

# Create a sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# If the database didn't exist, create all tables
if not db_exists:
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
