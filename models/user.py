from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    clerk_id = Column(String, unique=True, index=True, nullable=False) # ID from Clerk Auth
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default="employee") # "admin" or "employee"
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True) # self-referential
    
    # Relationship to see who created whom
    created_users = relationship("User", backref="created_by", remote_side=[id])
