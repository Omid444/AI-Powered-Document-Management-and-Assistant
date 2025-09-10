from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Date, JSON
from sqlalchemy.orm import relationship
from db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, index=True, nullable=False)
    #documents = relationship("Document", back_populates="owner")


# class Chat(Base):
#     __tablename__ = "chatbot_history"
#
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
#     conversation_id = Column(String, index=True)  # New: Unique ID for each conversation
#     role = Column(String)  # New: "user" or "assistant"
#     content = Column(String)  # New: Combines user_text and chatbot_answer
#     timestamp = Column(DateTime)  # New: Precise date and time
#     title = Column(String)  # Retained
#     # vice_versa relationship
#     #owner = relationship("User", back_populates="documents")
