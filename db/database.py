from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import urllib.parse
from dotenv import load_dotenv
load_dotenv()
import os



# Database configurations
# Format: mysql+pymysql://user:password@host/dbname
HOST = os.getenv("HOST")
PASSWORD = os.getenv("PASSWORD")
DB_NAME = os.getenv("DB_NAME")
USER = os.getenv("USER")

# URL-encode the password to handle special characters
encoded_password = urllib.parse.quote_plus(PASSWORD)

DATABASE_URL = f"mysql+pymysql://{USER}:{encoded_password}@{HOST}/{DB_NAME}"

# We'll also need a connection to create the database if it doesn't exist
ROOT_DATABASE_URL = f"mysql+pymysql://{USER}:{encoded_password}@{HOST}/"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
