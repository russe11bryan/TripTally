# Pydantic request/ response model for user
from typing import Optional
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: str

class UserUpdate(BaseModel):
    """Schema for updating user profile fields."""
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    contact_number: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    display_name: str
    class Config:
        from_attributes = True
