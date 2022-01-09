import json
import traceback
from base64 import b64encode
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any

import bcrypt
from config import config
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.logger import logger
from fastapi.param_functions import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError
from pydantic.fields import Field

from .users.db import UserDBManager
from .users.schemas import UpdateUserDEK, UserInDB

SECRET_KEY = config.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_TIMEOUT = config.ACCESS_TOKEN_EXPIRE_TIMEOUT


class JWTTokenData(BaseModel):
    id: str = Field(None, alias="_id")


oauth2_schema = OAuth2PasswordBearer(tokenUrl="login")
db = UserDBManager()

# jwt
def create_access_token(data: dict, expiry_minutes: int = ACCESS_TOKEN_EXPIRE_TIMEOUT) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> dict:
    try:
        decoded = jwt.decode(token=token, key=SECRET_KEY, algorithms=[ALGORITHM])
        token_data = JWTTokenData(**decoded)
    except (JWTError, ValidationError):
        raise HTTPException(
            detail="could not validate credentials",
            status_code=status.HTTP_403_FORBIDDEN,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


# user scope
async def get_current_user(token: str = Depends(oauth2_schema)) -> UserInDB:
    token_data = verify_access_token(token)
    user = await db.get_user_by_id(token_data.id)
    if not user:
        raise HTTPException(
            detail="user not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return UserInDB(**user)


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    if not current_user.is_active:
        raise HTTPException(
            detail="inactive user",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return current_user


async def get_current_admin_user(
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserInDB:
    if not current_user.is_admin:
        raise HTTPException(
            detail="user doesn't have enough privilages",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return current_user


# login
def hash_pw(password: str) -> str:
    return bcrypt.hashpw(b64encode(sha256(password.encode("utf-8")).digest()), bcrypt.gensalt()).decode("utf-8")


def check_pw_hash(password: str, pw_hash: str) -> bool:
    return bcrypt.checkpw(b64encode(sha256(password.encode("utf-8")).digest()), pw_hash.encode("utf-8"))


# data encryption
def generate_encrypted_dek(password: str, salt: str = None, dek: str = None, wrapping_key: str = None) -> set:
    salt = bcrypt.gensalt() if salt is None else salt.encode("utf-8")
    dek = Fernet.generate_key() if dek is None else dek.encode("utf-8")
    if wrapping_key is None:
        wrapping_key = b64encode(
            bcrypt.kdf(
                password=b64encode(sha256(password.encode("utf-8")).digest()),
                salt=salt,
                desired_key_bytes=32,
                rounds=100,
            )
        )
    else:
        wrapping_key = wrapping_key.encode("utf-8")

    f = Fernet(wrapping_key)
    encrypted_dek = f.encrypt(dek)
    return salt.decode("utf-8"), encrypted_dek.decode("utf-8")


def decrypt_dek(password: str, salt: str, encrypted_dek: str) -> str:
    wrapping_key = b64encode(
        bcrypt.kdf(
            password=b64encode(sha256(password.encode("utf-8")).digest()),
            salt=salt.encode("utf-8"),
            desired_key_bytes=32,
            rounds=100,
        )
    )
    f = Fernet(wrapping_key)

    decrypted_dek = f.decrypt(encrypted_dek.encode("utf-8")).decode("utf-8")
    return decrypted_dek


async def update_user_with_salt_dek(id: str, password: str):
    salt, encrypted_dek = generate_encrypted_dek(password)

    try:
        _ = await db.update_user(id, jsonable_encoder(UpdateUserDEK(salt=salt, encrypted_dek=encrypted_dek)))
    except Exception:
        logger.error(traceback.print_exc())
        raise RuntimeError(f"unable to update user with salt and dek: {id}")


def encrypt_payload(dek: str, data: Any) -> str:
    f = Fernet(dek)
    return f.encrypt(json.dumps(data).encode("utf-8")).decode("utf-8")


def decrypt_payload(dek: str, data: str) -> Any:
    try:
        f = Fernet(dek)
        if isinstance(data, dict):
            return data

        return json.loads(f.decrypt(data.encode("utf-8")))
    except (ValueError, InvalidToken):
        return None
