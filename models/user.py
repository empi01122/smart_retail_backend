from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    clerk_id = Column(String, unique=True, index=True, nullable=True) # ID from Clerk Auth (nullable for pre-authorized invite)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default="employee") # "technician", "proprietor", or "employee"
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True) # self-referential
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"), nullable=True) # None for technician
    
    # Relationships
    enterprise = relationship("Enterprise")
    created_users = relationship("User", backref="created_by", remote_side=[id])
