from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Date, JSON, DateTime, Float, Text
from sqlalchemy.orm import relationship
from db.database import Base
from datetime import datetime
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, index=True, nullable=False)

    #documents = relationship("Document", back_populates="user", lazy="selectin")
    chats = relationship("Chat", back_populates="user", lazy="selectin")

class Chat(Base):
    __tablename__ = "chatbot_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(String, index=True)  # New: Unique ID for each conversation
    role = Column(String(100))  # "user" or "assistant"
    content = Column(Text)  # Combines user_text and chatbot_answer
    timestamp = Column(DateTime)  # Precise date and time
    title = Column(String(255))  # Retained

    user = relationship("User", back_populates="chats")


class UserDocumentMeta(Base):
    __tablename__ = "user_document_meta"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=False)
    document_id = Column(String, index=True, nullable=False)
    is_tax_related = Column(Boolean, default=False)
    is_closed = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.now())
    
# class Document(Base):
#     __tablename__ = "documents"
#
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
#     title = Column(String(255), nullable=True)
#     summary = Column(Text, nullable=True)
#     is_payment = Column(Float, nullable=True)
#     is_tax_related = Column(Boolean, nullable=True)
#     due_date = Column(Date, nullable=True)
#     doc_date = Column(Date, nullable=True)
#
#     user = relationship("User", back_populates="documents", lazy="joined")
