import traceback

from config import config
from fastapi import APIRouter, HTTPException, Response, status
from fastapi.logger import logger
from fastapi.param_functions import Depends
from fastapi.security import OAuth2PasswordRequestForm

from api.security import check_pw_hash, create_access_token, decrypt_dek

from .db import AuthDBManager

router = APIRouter()
db = AuthDBManager()


@router.post("")
async def login_user(
    response: Response,
    payload: OAuth2PasswordRequestForm = Depends(),
):
    """oauth2 token login. generate jwt bearer access token"""
    try:
        user = await db.get_user_by_email(payload.username)
        if not user:
            raise HTTPException(detail="invalid credentials", status_code=status.HTTP_400_BAD_REQUEST)

        if not user.get("is_active"):
            raise HTTPException(detail="inactive user", status_code=status.HTTP_400_BAD_REQUEST)

        if not check_pw_hash(payload.password, user.get("hashed_password")):
            raise HTTPException(detail="invalid credentials", status_code=status.HTTP_400_BAD_REQUEST)

        access_token = create_access_token(data={"_id": user.get("_id")})
        dek = decrypt_dek(payload.password, user.get("salt"), user.get("encrypted_dek"))

        response.set_cookie(
            key="dek",
            value=dek,
            httponly=True,
            max_age=config.ACCESS_TOKEN_EXPIRE_TIMEOUT * 60,
            expires=config.ACCESS_TOKEN_EXPIRE_TIMEOUT * 60,
        )

        return {"access_token": access_token, "token_type": "bearer"}
    except RuntimeError:
        logger.error(traceback.print_exc())
        raise HTTPException(detail="Login Failed", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# TODO: add logout route with support to invalidate cookies and revoke jwt token
