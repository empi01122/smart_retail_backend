from pydantic import BaseModel, EmailStr
from typing import Optional

# Base schema with shared attributes
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "employee"

# Used to create a user when receiving data from Clerk webhook or frontend sync
class UserCreate(UserBase):
    clerk_id: str
    created_by_id: Optional[int] = None

# Used for reading user data (sent back to frontend)
class UserResponse(UserBase):
    id: int
    clerk_id: str
    created_by_id: Optional[int] = None
    
    class Config:
        from_attributes = True

# Used if we need to update user data (like role)
class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
