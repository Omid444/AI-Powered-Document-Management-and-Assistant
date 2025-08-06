from http.client import HTTPException
from fastapi import  Request, Depends, Header, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from jose import JWTError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from fastapi import FastAPI
import models.schemas
import services.auth, services.open_ai_connection
from models.models import User
from sqlalchemy.orm import Session
from db.database import SessionLocal, session
from services.summarizer import extract_txt
import uvicorn

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


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "message": "Hello, World!"})



@app.get("/signup", response_class=HTMLResponse)
async def get_signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup")
async def signup(user: models.schemas.UserCreate, db: Session = Depends(get_db)):
    db_email = db.query(models.models.User.username).filter(models.models.User.email == user.username).scalar()
    if db_email:
        raise HTTPException(status_code=400, detail="Username already used")
    hashed_password = services.auth.hash_password(user.password)
    new_user = models.models.User(first_name= user.first_name, last_name=user.last_name, email=user.email, username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "email": user.email}


@app.post("/login")
async def login(user: models.schemas.UserLogin, db: Session = Depends(get_db)):
    db_username = db.query(models.models.User.username).filter(models.models.User.username == user.username).scalar()
    db_hashed_password = db.query(models.models.User.hashed_password).filter(models.models.User.username == user.username).scalar()
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
    print("Authorization:", authorization)
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
async def chat(request: Request, authorization: str = Header(None, alias="Authorization")):
    print("Authorization in api/chat:", authorization)
    data = await request.json()
    print(data)
    user_message = data.get("message", "")
    reply = services.open_ai_connection.ask_ai(user_message)
    return JSONResponse(content={"reply": f"{reply}"})


@app.get("/chatbot")
async def chatbot(request: Request, authorization: str = Header(None, alias="Authorization")):
    print("Authorization in chatbot:", authorization)
    return templates.TemplateResponse("chatbot.html",{"request": request})




@app.post("/api/file_upload")
async def upload(file: UploadFile = File(...)):
    text = extract_txt(file.file)
    order = (" at first explains in two or fewer lines about this text. It is a document belongs to me"
             "summarize this tex for me if document more than 10 line and. do not change text in summary"
             "to much but make it more clear and easy to understand and remember always write it "
             "in second person format")
    final_text = order + "\n" + text
    reply = services.open_ai_connection.ask_ai(final_text)
    #print(reply)
    return JSONResponse(content={"reply": reply})


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