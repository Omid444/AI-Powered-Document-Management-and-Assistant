from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os


basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "data", "document_manager.sqlite")
# Create a database connection
engine = create_engine(f'sqlite:///{db_path}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a database session
Session = sessionmaker(bind=engine)
session = Session()

# Define the data table class's parent class
Base = declarative_base()