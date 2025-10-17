import os.path
import uuid
from datetime import datetime
from services.app_services import app, templates, get_db
import models.schemas
import services.auth, services.open_ai_connection, services.gemini_connection
from fastapi import  Request, Depends, Header, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from models.models import User, Chat, UserDocumentMeta
from sqlalchemy.orm import Session
from sqlalchemy import select, asc, desc
from services import lang_chain, summarizer
from fastapi.responses import FileResponse
from services.app_services import check_authorization
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm

origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

app.add_middleware(CORSMiddleware, allow_origins=origins,
               allow_credentials=True,allow_methods=["*"],
               allow_headers=["*"])



# @app.get("/", response_class=HTMLResponse)
# async def read_root(request: Request):
#     """
#     Render the home page with a greeting message.
#     """
#     return templates.TemplateResponse("home.html", {"request": request, "message": "Hello, World!"})



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
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT access token.
    """
    username = form_data.username
    password = form_data.password
    db_username = db.query(User.username).filter(User.username == username).scalar()
    db_hashed_password = db.query(User.hashed_password).filter(User.username == username).scalar()
    if not db_username or db_hashed_password is None:
        raise HTTPException(status_code=401, detail="Username or Password is incorrect")
    is_pass_verified = services.auth.verify_password(password, db_hashed_password)
    if not is_pass_verified:
        raise HTTPException(status_code=401, detail="Username or Password is incorrect")
    access_token = services.auth.create_access_token(data={"sub": username})
    print("access_token", access_token)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/account")
async def account(authorization: str = Header(None, alias="Authorization"),
                  db: Session = Depends(get_db)):
    """
    Render the account page for the authenticated user.
    """
    username = check_authorization(authorization)

    # lang_chain.state.update({"question": f"Today date is {current_date} I need to find every documents that their due_date"
    #                                      f"is one month later of today.each document must have different document_id."
    #                                      f"if due_date is None or null or empty do not return"})
    #retrieved_docs = lang_chain.retrieve_document(username, k=4)
    #print("retried_docs",retrieved_docs)
    retrieved_docs = lang_chain.retrieve_due_date_documents(username)
    username = check_authorization(authorization)
    if username:
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    user_firstname = db.query(models.models.User.first_name).filter(models.models.User.username == username).scalar()
    metas = {m.document_id: m for m in db.query(UserDocumentMeta).filter_by(username=username).all()}

    final_docs = []
    for doc in retrieved_docs:
        doc_id = doc["metadata"]["document_id"]
        meta = metas.get(doc_id)

        # اگر در جدول بسته شده بود → ردش کن
        if meta and meta.is_closed:
            continue

        enriched = {
            "file_name": doc["metadata"]["file_name"],
            "due_date": doc["metadata"]["due_date"],
            "document_id": doc["metadata"]["document_id"],
            "content": doc["document"],
            "is_payment": doc["metadata"].get("is_payment"),
            "is_tax_related": meta.is_tax_related if meta else False
        }
        final_docs.append(enriched)
    #print("Final Doccccccccccc", final_docs)
    #print("***********This is retrieved docs",retrieved_docs)
    return {"firstname":user_firstname, "retrieved_docs":final_docs}


@app.post("/alerts/toggle_tax/{document_id}")
async def toggle_tax_related(document_id: str,
                             authorization: str = Header(None, alias="Authorization"),
                             db: Session = Depends(get_db)):
    username = check_authorization(authorization)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    meta = db.query(UserDocumentMeta).filter_by(username=username, document_id=document_id).first()
    if not meta:
        meta = UserDocumentMeta(username=username, document_id=document_id, is_tax_related=True)
        db.add(meta)
        new_value = True
    else:
        meta.is_tax_related = not meta.is_tax_related
        new_value = meta.is_tax_related
    db.commit()
    return {"document_id": document_id, "is_tax_related": new_value}


@app.post("/alerts/close/{document_id}")
async def close_alert(document_id: str,
                      authorization: str = Header(None, alias="Authorization"),
                      db: Session = Depends(get_db)):
    username = check_authorization(authorization)
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")

    meta = db.query(UserDocumentMeta).filter_by(username=username, document_id=document_id).first()
    if not meta:
        meta = UserDocumentMeta(username=username, document_id=document_id, is_closed=True)
        db.add(meta)
    else:
        meta.is_closed = True
    db.commit()
    return {"document_id": document_id, "is_closed": True}


@app.post("/api/chat")
async def chat(request: Request, authorization: str = Header(None, alias="Authorization"),
               db: Session = Depends(get_db)):
    """
    Handle user chat requests and return an AI-generated reply.
    """
    #print("Authorization in api/chat:", authorization)
    username = check_authorization(authorization)
    if username:
        data = await request.json()
        user_message = data.get("message", "")
        user_id = db.query(models.models.User.id).filter(models.models.User.username == username).scalar()
        conversation_id = str(uuid.uuid4())
        user_chat_entry = Chat(
            user_id=user_id,
            conversation_id=conversation_id,
            role="user",
            content=user_message,
            timestamp=datetime.now(),
            title="chat history user"
        )
        db.add(user_chat_entry)
        db.commit()
        db.refresh(user_chat_entry)

        lang_chain.state.update({"question": user_message})
        #print(lang_chain.state)
        retrieved_doc = lang_chain.retrieve_document(username)
        #print("____????????????? This is retrieve doc in chat",retrieved_doc)
        lang_chain.state.update(retrieved_doc)
        reply = lang_chain.generate()
        ai_answer = reply["answer"]
        assistant_chat_entry = Chat(
            user_id=user_id,
            conversation_id=conversation_id,
            role="assistant",
            content=ai_answer,
            timestamp=datetime.now(),
            title="chat history bot"
        )
        db.add(assistant_chat_entry)
        db.commit()
        db.refresh(assistant_chat_entry)
        return JSONResponse(content={"reply": reply["answer"]})


@app.get("/api/chat/history")
async  def get_chat_history(authorization: str = Header(None, alias="Authorization"),
                         db: Session = Depends(get_db)):
        """
        Retrieve the last 10 chat conversations for the authorized user.
        """
        #print("Authorization in history of chatbot", authorization)
        username = check_authorization(authorization)
        if not username:
            raise HTTPException(status_code=401, detail="Unauthorized")

        user = db.scalar(select(User).where(User.username == username))
        if not user:
            return []  # Return an empty list if user is not found
        query = select(Chat).where(Chat.user_id == user.id).order_by(desc(Chat.timestamp)).limit(50)
        chat_entries = db.execute(query).scalars().all()
        chat_entries.reverse()
        #chat_entries = db.scalars(query).all()
        #chat_entries = sorted(user.chats, key=lambda c:c.timestamp)[:50]

        # Convert the SQLAlchemy objects to a list of dictionaries for JSON serialization
        history = [
            {
                "id": chat.id,
                "conversation_id": chat.conversation_id,
                "role": chat.role,
                "content": chat.content,
                "timestamp": chat.timestamp.isoformat(),
                "title": chat.title
            }
            for chat in chat_entries
        ]
        #print("*************This is history: ",history)
        return history


@app.post("/api/file_upload")
async def upload(file: UploadFile = File(...), authorization: str = Header(None, alias="Authorization"),
                 db: Session = Depends(get_db)):
    """
    Upload a PDF file, extract its content/metadata,
    store it in the vector DB, save copy of original file on disk and return a summary.
    """
    #print("Authorization file_upload:", authorization)
    username = check_authorization(authorization)
    if username:
        file_name = file.filename
        file_content_bytes = file.file.read()

        # Pass this byte string to a new function to process and save it.
        file_content, meta_data = services.summarizer.extract_text_and_metadata(file_content_bytes)
        reply = services.open_ai_connection.file_upload_llm(file_content, meta_data)
        #reply = services.gemini_connection.file_upload_llm_gemini(file_content, meta_data)
        content, file_content, meta_data =services.app_services.file_upload(username=username, file_name=file_name, file_content=file_content,
                                                                            file_content_bytes=file_content_bytes, meta_data=meta_data,
                                                                            due_date=reply.due_date, is_payment=reply.is_payment, is_tax_related=reply.is_tax_related)
        user_id = db.query(models.models.User.id).filter(models.models.User.username == username).scalar()
        conversation_id = str(uuid.uuid4())
        if all([content, file_content, meta_data]):
            assistant_chat_entry = Chat(
                user_id=user_id,
                conversation_id=conversation_id,
                role="assistant",
                content=reply.summary,
                timestamp=datetime.now(),
                title="chat history upload file"
            )
            db.add(assistant_chat_entry)
            db.commit()
            db.refresh(assistant_chat_entry)
            return JSONResponse(content={"reply": reply.summary})
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
    metas_from_db = (
        db.query(models.models.UserDocumentMeta)
        .filter(models.models.UserDocumentMeta.username == username)
        .all()
    )
    user_firstname = db.query(models.models.User.first_name).filter(
        models.models.User.username == username).scalar()
    metas_dict = {m.document_id: m for m in metas_from_db}
    metadata_unique_list = []

    seen_ids = set()

    for doc in all_documents["metadatas"]:
        doc_id = doc.get("document_id")
        if not doc_id or doc_id in seen_ids:
            continue
        seen_ids.add(doc_id)

        meta_data = {
            "file_name": doc.get("file_name"),
            "document_id": doc_id,
            "due_date": doc.get("due_date"),
            "is_payment": doc.get("is_payment"),
            "is_tax_related": doc.get("is_tax_related", False),
            "is_closed": False
        }
        if doc_id in metas_dict:
            meta_sql = metas_dict[doc_id]
            if meta_sql.is_tax_related is not None:
                meta_data["is_tax_related"] = meta_sql.is_tax_related
            if meta_sql.is_closed is not None:
                meta_data["is_closed"] = meta_sql.is_closed

            # فقط سندهای باز (is_closed = False)
        if not meta_data["is_closed"]:
            metadata_unique_list.append(meta_data)
        #return templates.TemplateResponse("dashboard.html",{"request": request,"firstname": user_firstname.title(), "documents": {"metadatas": metadata_unique_list}})
    return {"documents":metadata_unique_list}


@app.get("/show_pdf/{document_id}")
async def show_document(document_id:str, authorization: str = Header(None, alias="Authorization"),
                        db: Session = Depends(get_db)):
    """
    Return the requested PDF file for the authenticated user.
    """
    #print("Authorization in show_pdf:", authorization)
    #print("document_id: ",document_id)
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
        db.query(models.models.UserDocumentMeta).filter(
            (models.models.UserDocumentMeta.username == username) &
            (models.models.UserDocumentMeta.document_id == document_id)
        ).delete()

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