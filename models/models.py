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
    documents = relationship("Document", back_populates="owner")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String)
    #file_path = Column(String)
    summary = Column(String)
    tags = Column(JSON)
    is_payment = Column(Integer, nullable=True)
    is_tax_related = Column(Boolean, default=False)
    due_date = Column(Date, nullable=True)
    doc_date = Column(Date, nullable=True)
    # vice_versa relationship
    owner = relationship("User", back_populates="documents")
