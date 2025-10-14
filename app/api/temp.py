# @app.post("/api/file_upload")
# async def upload(file: UploadFile = File(...), authorization: str = Header(None, alias="Authorization"),
#                  db: Session = Depends(get_db)):
#     """
#     Upload a PDF file, extract its content/metadata,
#     store it in the vector DB, save copy of original file on disk and return a summary.
#     """
#     print("Authorization file_upload:", authorization)
#     username = check_authorization(authorization)
#     if username:
#         content, file_content, meta_data = services.app_services.file_upload(username, file)
#         user_id = db.query(models.models.User.id).filter(models.models.User.username == username).scalar()
#         conversation_id = str(uuid.uuid4())
#         if all([content, file_content, meta_data]):
#             reply = services.open_ai_connection.file_upload_llm(file_content, meta_data)
#             assistant_chat_entry = Chat(
#                 user_id=user_id,
#                 conversation_id=conversation_id,
#                 role="assistant",
#                 content=reply.summary,
#                 timestamp=datetime.now(),
#                 title="chat history upload file"
#             )
#             db.add(assistant_chat_entry)
#             db.commit()
#             db.refresh(assistant_chat_entry)
#             return JSONResponse(content={"reply": reply.summary})
#         else:
#           return JSONResponse(content={"reply": content})

from PIL import Image
import pytesseract

# مسیر فایل تصویر
image_path = "/Users/omiddavoudi/Desktop/Aufenhalttitle/temp/Mietzahlung-31.03.2025.png"

# باز کردن تصویر
img = Image.open(image_path)

# استخراج متن از تصویر
text = pytesseract.image_to_string(img)

# چاپ متن استخراج‌شده
print(text)