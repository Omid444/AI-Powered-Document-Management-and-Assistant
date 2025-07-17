from db.database import engine, Base
from models.models import User
from dotenv import load_dotenv
import os

# load from .env
load_dotenv()

# reading API Key
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    print(f"My API Key is: {api_key[:5]}******")  # only first part shown
else:
    print("API key not found. Check your .env file.")


# create tables (for dev)
Base.metadata.create_all(bind=engine)


