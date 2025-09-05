import os.path
import models.schemas
import services.auth, services.open_ai_connection
import shutil
from fastapi import  Request, Depends, Header, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from jose import JWTError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from fastapi import FastAPI
from models.models import User
from sqlalchemy.orm import Session
from db.database import SessionLocal, session
from services.summarizer import extract_text_and_metadata
from services import lang_chain
from fastapi.responses import FileResponse

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent.parent #Back to root of project
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
    file_path = user_dir / f"{lang_chain.create_source_key(username=user_name, file_name=file_name)}"
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
        username = services.auth.verify_token(token)
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username

    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")






@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "message": "Hello, World!"})



@app.get("/signup", response_class=HTMLResponse)
async def get_signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup")
async def signup(user: models.schemas.UserCreate, db: Session = Depends(get_db)):
    print("something here")
    db_email = db.query(User.email).filter(User.email == user.email).scalar()
    db_username = db.query(User.username).filter(User.username == user.username).scalar()
    if db_email:
        raise HTTPException(status_code=400, detail="Email already used")
    if db_username:
        raise HTTPException(status_code=400, detail="Username already used")
    hashed_password = services.auth.hash_password(user.password)
    new_user = User(first_name=user.first_name, last_name=user.last_name, email=user.email, username=user.username, hashed_password=hashed_password)
    print("new_user",new_user)
    db.add(new_user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(new_user)
    return {"message": "User created successfully", "email": user.email}


@app.post("/login")
async def login(user: models.schemas.UserLogin, db: Session = Depends(get_db)):
    db_username = db.query(User.username).filter(User.username == user.username).scalar()
    db_hashed_password = db.query(User.hashed_password).filter(User.username == user.username).scalar()
    if not db_username or db_hashed_password is None:
        raise HTTPException(status_code=401, detail="Username or Password is incorrect")
    is_pass_verified = services.auth.verify_password(user.password, db_hashed_password)
    if not is_pass_verified:
        raise HTTPException(status_code=401, detail="Username or Password is incorrect")
    access_token = services.auth.create_access_token(data={"sub": user.username})
    print("access_token", access_token)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/account")
async def account(request: Request, authorization: str = Header(None, alias="Authorization"), db: Session = Depends(get_db)):
    #user_firstname = db.query(models.models.User).filter(models.models.User.username == user.username)
    print("Authorization in account:", authorization)
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]

    try:
        username = services.auth.verify_token(token)
        print("Email from token:", username)
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")
    user_firstname = db.query(models.models.User.first_name).filter(models.models.User.username == username).scalar()
    return templates.TemplateResponse("account.html", {"request": request, "firstname": user_firstname.title()})



@app.post("/api/chat")
async def chat(request: Request, authorization: str = Header(None, alias="Authorization"), db: Session = Depends(get_db)):
    print("Authorization in api/chat:", authorization)
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]

    try:
        username = services.auth.verify_token(token)
        user_id = db.query(User.id).filter(User.username == username).scalar()
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        data = await request.json()
        print(data)
        user_message = data.get("message", "")
        #reply = services.open_ai_connection.ask_ai(user_message)
        lang_chain.state.update({"question": user_message})
        print(lang_chain.state)
        retrieved_doc = lang_chain.retrieve_document(username)
        print(retrieved_doc)
        lang_chain.state.update(retrieved_doc)
        reply = lang_chain.generate()
        print(reply)
        return JSONResponse(content={"reply": f"{reply["answer"]}"})
    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")


@app.get("/chatbot")
async def chatbot(request: Request, authorization: str = Header(None, alias="Authorization")):
    print("Authorization in chatbot:", authorization)
    return templates.TemplateResponse("chatbot.html",{"request": request})



@app.post("/api/file_upload")
async def upload(file: UploadFile = File(...), authorization: str = Header(None, alias="Authorization"), db: Session = Depends(get_db)):
    print("Authorization file_upload:", authorization)
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]

    try:
        username = services.auth.verify_token(token)
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        file_name = file.filename
        file_content, meta_data = extract_text_and_metadata(file.file)
        is_file_duplicate = lang_chain.check_for_duplicate_document(username, file_content)
        if is_file_duplicate:
            return JSONResponse(content={"reply": "Your file is already exist in database,\n"
                                                  "Do you have any question about it,\n"
                                                  "Please let me know"})
        reply = services.open_ai_connection.file_upload_llm(file_content, meta_data)
        file_path = create_file_path(username, file_name)
        file.file.seek(0)
        is_filed_saved  = save_file(file.file,file_path)
        if is_filed_saved != "File Saved":
            return JSONResponse(content={"reply": is_filed_saved})

        lang_chain.turn_txt_to_vector(username=username, raw_document=file_content, file_name=file_name, file_path=file_path)

        return JSONResponse(content={"reply": reply["summary"]})

    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")


@app.get("/dashboard")
async def show_dashboard(request: Request, authorization: str = Header(None, alias="Authorization"),
                         db: Session = Depends(get_db)):
    print("Authorization in dashboard:", authorization)
    username = check_authorization(authorization)
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    v_db = lang_chain.get_user_store(username)
    all_documents = v_db.get(where={"username": username})
    metadata_unique_list = []

    for doc in all_documents["metadatas"]:
        doc_id_temp = ""
        meta_data = {"file_name": doc.get("file_name"), "document_id": doc.get("document_id")}
        print("this is metadata:", meta_data)
        print("metadata_unique_list:", metadata_unique_list)
        if meta_data not in metadata_unique_list:
            metadata_unique_list.append(meta_data)

    user_firstname = db.query(models.models.User.first_name).filter(
            models.models.User.username == username).scalar()
    return templates.TemplateResponse("dashboard.html",{"request": request,"firstname": user_firstname.title(), "documents": {"metadatas": metadata_unique_list}})



@app.get("/show_pdf/{document_id}")
async def show_document(document_id:str, request: Request, authorization: str = Header(None, alias="Authorization"),
                        db: Session = Depends(get_db)):
    print("Authorization in show_pdf:", authorization)
    print("document_id: ",document_id)
    username = check_authorization(authorization)
    if username:
        v_db = lang_chain.get_user_store(username)
        filters = {
            "$and": [
                {"username": {"$eq": username}},
                {"document_id": {"$eq": document_id}},
            ]
        }
        document = v_db.get(
            where=filters
        )
        print("file_path: ",document["metadatas"][0]["file_path"])
        file_path = document["metadatas"][0]["file_path"]
        #return templates.TemplateResponse("dashboard.html", {"request": request, "document": "This is test"})
        try:
            return FileResponse(
                file_path,
                media_type="application/pdf"
            )
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found")


@app.delete("/delete_pdf/{document_id}")
async def show_document(document_id:str, request: Request, authorization: str = Header(None, alias="Authorization"),
                        db: Session = Depends(get_db)):
    print("Authorization in delete_pdf:", authorization)
    print("document_id: ",document_id)
    username = check_authorization(authorization)
    if username:
        v_db = lang_chain.get_user_store(username)
        filters = {
            "$and": [
                {"username": {"$eq": username}},
                {"document_id": {"$eq": document_id}},
            ]
        }
        document = v_db.get(
            where=filters
        )

        v_db.delete(where=filters)
        print("file_path: ",document["metadatas"][0]["file_path"])
        file_path = document["metadatas"][0]["file_path"]
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return
            else:
                raise HTTPException(status_code=404, detail="File not found")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")




@app.get("/items")
async def read_items(request: Request, authorization: str = Header(None, alias="Authorization")):
    print(authorization)
    return templates.TemplateResponse("test.html",{"request": request})


# @app.get("/items/")
# async def read_item(skip: int = 0, limit: int = 10):
#     return fake_items_db[skip : skip + limit]

# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)

# uvicorn app.api.app:app --reload