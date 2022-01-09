from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, SecretStr
from pydantic.fields import Field


class UserInDB(BaseModel):
    """base class modelling the database entry for reference"""

    id: str = Field(None, alias="_id")
    avatar: str
    first_name: str
    last_name: str
    email: EmailStr
    hashed_password: SecretStr
    salt: SecretStr
    encrypted_dek: SecretStr
    is_admin: bool
    is_active: bool
    created_at: datetime


# schemas for "create user"
class CreateUser(BaseModel):
    avatar: Optional[str] = "default.png"
    first_name: str
    last_name: str
    email: EmailStr
    password: SecretStr

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
        }


class CreateUserIn(BaseModel):
    avatar: str
    first_name: str
    last_name: str
    email: EmailStr
    hashed_password: SecretStr
    is_admin: Optional[bool] = False
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
        }


class CreateUserOut(BaseModel):
    id: str = Field(None, alias="_id")
    avatar: str
    first_name: str
    last_name: str
    email: EmailStr
    is_active: bool
    created_at: datetime


# schemas for "update user"
class UpdateUserProfile(BaseModel):
    avatar: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
        }


class UpdateUserProfileOut(BaseModel):
    id: str = Field(None, alias="_id")
    avatar: str
    first_name: str
    last_name: str
    email: EmailStr
    is_active: bool
    created_at: datetime


class UpdateUserPassword(BaseModel):
    current_password: SecretStr
    new_password: SecretStr

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
        }


class UpdateUserDEK(BaseModel):
    salt: SecretStr
    encrypted_dek: SecretStr

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
        }


# schemas for "get user"
class GetUserOut(BaseModel):
    id: str = Field(None, alias="_id")
    avatar: str
    first_name: str
    last_name: str
    email: EmailStr
    is_active: bool
    is_admin: bool
    created_at: datetime
