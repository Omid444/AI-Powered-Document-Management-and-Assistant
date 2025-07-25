from http.client import HTTPException
from typing import Annotated

from fastapi import FastAPI, Request, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse
from jose import JWTError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from fastapi import FastAPI
import models.schemas
import services.auth
from models.models import User
from sqlalchemy.orm import Session
from db.database import SessionLocal, session
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
    db_email = db.query(models.models.User.email).filter(models.models.User.email == user.email).scalar()
    if db_email:
        raise HTTPException(status_code=400, detail="Email already used")
    hashed_password = services.auth.hash_password(user.password)
    new_user = models.models.User(first_name= user.first_name, last_name=user.last_name, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "email": user.email}


@app.post("/login")
async def login(user: models.schemas.UserLogin, db: Session = Depends(get_db)):
    db_email = db.query(models.models.User.email).filter(models.models.User.email == user.email).scalar()
    db_hashed_password = db.query(models.models.User.hashed_password).filter(models.models.User.email == user.email).scalar()
    if not db_email or db_hashed_password is None:
        raise HTTPException(status_code=401, detail="Email or Password is incorrect")
    is_pass_verified = services.auth.verify_password(user.password, db_hashed_password)
    if not is_pass_verified:
        raise HTTPException(status_code=401, detail="Email or Password is incorrect")
    access_token = services.auth.create_access_token(data={"sub": user.email})
    print("access_token", access_token)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/account")
async def account(request: Request, authorization: str = Header(None, alias="Authorization")):
    print("Authorization:", authorization)
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]

    try:
        email = services.auth.verify_token(token)
        print("Email from token:", email)
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")

    return templates.TemplateResponse("account.html", {"request": request, "email": email})



@app.get("/items")
async def read_items(request: Request, authorization: str = Header(None, alias="Authorization")):
    print(authorization)
    return templates.TemplateResponse("test.html",{"request": request})
# @app.get("/users/me")
# async def read_user_me():
#     return {"user_id": "the current user"}
#
#
# @app.get("/users/{user_id}")
# async def read_user(user_id: str):
#     return {"user_id": user_id}
#
#
#
# @app.get("/items/")
# async def read_item(skip: int = 0, limit: int = 10):
#     return fake_items_db[skip : skip + limit]

# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)

# uvicorn app.api.app:app --reload