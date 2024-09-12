import subprocess
import os
import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Update the import statement
from models import Base

def is_postgres_running():
    try:
        subprocess.run(["pgrep", "-x", "postgres"], check=True, stdout=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def is_database_accessible():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        return False

    try:
        conn = psycopg2.connect(database_url)
        conn.close()
        return True
    except psycopg2.OperationalError:
        return False

def run_setup_script():
    script_path = "backend/database/startup.sh"
    if not os.path.exists(script_path):
        print(f"Error: {script_path} not found.")
        return False

    try:
        subprocess.run(["bash", script_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running setup script: {e}")
        return False

def create_tables():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("Error: DATABASE_URL not found in .env file.")
        return False

    try:
        engine = create_engine(database_url)
        Base.metadata.create_all(engine)
        print("Database tables created successfully.")
        return True
    except SQLAlchemyError as e:
        print(f"Error creating database tables: {e}")
        return False

def main():
    if not is_postgres_running():
        print("PostgreSQL is not running. Starting setup process...")
        if run_setup_script():
            print("Setup completed successfully.")
        else:
            print("Setup failed. Please check the error messages above.")
            return
    elif not is_database_accessible():
        print("PostgreSQL is running, but the database is not accessible. Running setup script...")
        if run_setup_script():
            print("Setup completed successfully.")
        else:
            print("Setup failed. Please check the error messages above.")
            return
    else:
        print("PostgreSQL is running and the database is accessible.")

    print("Creating database tables...")
    if create_tables():
        print("Database setup completed successfully.")
    else:
        print("Failed to create database tables. Please check the error messages above.")

if __name__ == "__main__":
    main()