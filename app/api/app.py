import os.path
from services.app_services import app, templates, get_db
import models.schemas
import services.auth, services.open_ai_connection
import shutil
from fastapi import  Request, Depends, Header, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from models.models import User
from sqlalchemy.orm import Session
from services.summarizer import extract_text_and_metadata
from services import lang_chain
from fastapi.responses import FileResponse
from services.app_services import check_authorization, create_file_path, save_file





@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Render the home page with a greeting message.
    """
    return templates.TemplateResponse("home.html", {"request": request, "message": "Hello, World!"})



@app.get("/signup", response_class=HTMLResponse)
async def get_signup_page(request: Request):
    """
    Render the signup page template.
    """
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup")
async def signup(user: models.schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.

    Validates email/username uniqueness, hashes the password,
    and stores the new user in the database.
    """
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
    """
    Authenticate a user and return a JWT access token.
    """
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
async def account(request: Request, authorization: str = Header(None, alias="Authorization"),
                  db: Session = Depends(get_db)):
    """
    Render the account page for the authenticated user.
    """
    print("Authorization in account:", authorization)
    username = check_authorization(authorization)
    if username:
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    user_firstname = db.query(models.models.User.first_name).filter(models.models.User.username == username).scalar()
    return templates.TemplateResponse("account.html", {"request": request, "firstname": user_firstname.title()})



@app.post("/api/chat")
async def chat(request: Request, authorization: str = Header(None, alias="Authorization"),
               db: Session = Depends(get_db)):
    """
    Handle user chat requests and return an AI-generated reply.
    """
    print("Authorization in api/chat:", authorization)
    username = check_authorization(authorization)
    if username:
        data = await request.json()
        user_message = data.get("message", "")
        lang_chain.state.update({"question": user_message})
        print(lang_chain.state)
        retrieved_doc = lang_chain.retrieve_document(username)
        lang_chain.state.update(retrieved_doc)
        reply = lang_chain.generate()
        return JSONResponse(content={"reply": reply["answer"]})



@app.get("/chatbot")
async def chatbot(request: Request, authorization: str = Header(None, alias="Authorization")):
    """
    Render the chatbot page template.
    """
    print("Authorization in chatbot:", authorization)
    return templates.TemplateResponse("chatbot.html",{"request": request})



@app.post("/api/file_upload")
async def upload(file: UploadFile = File(...), authorization: str = Header(None, alias="Authorization"),
                 db: Session = Depends(get_db)):
    """
    Upload a PDF file, extract its content/metadata,
    store it in the vector DB, save copy of original file on disk and return a summary.
    """
    print("Authorization file_upload:", authorization)
    username = check_authorization(authorization)
    if username:
        content, file_content, meta_data = services.app_services.file_upload(username, file)
        if all([content, file_content, meta_data]):
            reply = services.open_ai_connection.file_upload_llm(file_content, meta_data)
            return JSONResponse(content={"reply": reply["summary"]})
        else:
          return JSONResponse(content={"reply": content})


@app.get("/dashboard")
async def show_dashboard(request: Request, authorization: str = Header(None, alias="Authorization"),
                         db: Session = Depends(get_db)):
    """
    Render the user dashboard with uploaded document list.
    """
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
    """
    Return the requested PDF file for the authenticated user.
    """
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
    """
    Delete a user's PDF by document_id.

    Removes metadata from the vector DB and deletes the file from disk.
    Requires valid Authorization header.
    """
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


@app.post("/dashboard/upload_pdf")
async def upload_file_button(file: UploadFile = File(...),authorization: str = Header(None, alias="Authorization"),
        db: Session = Depends(get_db)):

    print("Authorization upload_file_button:", authorization)
    username = check_authorization(authorization)
    if username:
        content, file_content, meta_data = services.app_services.file_upload(username, file)
        if all([content, file_content, meta_data]):
            return {"message": "File uploaded successfully", "file_name": file.filename}
        else:
            return {"message": "File already exist in database", "file_name": file.filename}
    raise HTTPException(status_code=400, detail="File upload failed")


# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)

# uvicorn app.api.app:app --reload