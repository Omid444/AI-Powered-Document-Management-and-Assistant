from jose import JWTError
from fastapi import  HTTPException
from pathlib import Path
from services.lang_chain import create_source_key
from services.auth import verify_token
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI
from db.database import SessionLocal


app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent  #Back to root of project
app.mount("/static", StaticFiles(directory=BASE_DIR/"static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR/"templates")


def get_db():
    """
    Creates a new database session and ensures it is properly closed after use.

    This function is intended to be used as a dependency in FastAPI routes.
    It yields a SQLAlchemy session (`db`) that can be used to interact with the database.
    After the request is completed, the session is automatically closed to free resources.

    Yields:
        Session: An active SQLAlchemy session instance.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_file_path(user_name, file_name):
    user_dir = BASE_DIR / "uploads" /user_name
    user_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(file_name).suffix
    file_path = user_dir / f"{create_source_key(username=user_name, file_name=file_name)}"
    return file_path



def save_file(file, file_path):

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file, buffer)# type: ignore
            return "File Saved"
    except PermissionError:
        reply = "Permission denied."
        return reply
    except Exception as e :
        reply = f"Error occurred while copying file. details:{e}"
        return reply



def check_authorization(authorization):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]

    try:
        username = verify_token(token)
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username

    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")