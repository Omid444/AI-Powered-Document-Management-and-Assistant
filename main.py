from db.database import engine, Base
from models.models import User
from dotenv import load_dotenv
from app.api.app import app
import uvicorn
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


# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)