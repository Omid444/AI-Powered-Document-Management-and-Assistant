from io import BytesIO
from jose import JWTError
from fastapi import HTTPException, UploadFile
from pathlib import Path
from services.lang_chain import create_source_key
from services.auth import verify_token
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI
from db.database import SessionLocal
from services.summarizer import extract_text_and_metadata
from services.lang_chain import check_for_duplicate_document, turn_txt_to_vector

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



def save_file(file_bytes, file_path):
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes)
        return "File Saved"
    except PermissionError:
        return "Permission denied."
    except Exception as e:
        return f"Error occurred while copying file: {e}"


# def insert_document():
#     """Insert document properties in documents table."""



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


def file_upload(username, file_name, file_content,
                file_content_bytes, meta_data,
                due_date, is_payment, is_tax_related):


    # Check for duplicate document
    is_file_duplicate = check_for_duplicate_document(username, file_content)
    if is_file_duplicate:
        content =  "Your file is already exist in database,\n" \
                   "Do you have any question about it,\n" \
                   "Please let me know"
        return content, None, None

    file_path = create_file_path(username, file_name)

    # Pass the byte string to the save function.
    is_file_saved = save_file(file_content_bytes, file_path)
    if is_file_saved != "File Saved":
        content = is_file_saved
        return content, None, None
    try:
        content = is_file_saved
        turn_txt_to_vector(username=username, raw_document=file_content, file_name=file_name, file_path=file_path,
                           due_date=due_date, is_payment=is_payment, is_tax_related=is_tax_related)
        return content, file_content, meta_data
    except Exception as e:
        content = "Error occurred in vector DB."
        return content, None, None
