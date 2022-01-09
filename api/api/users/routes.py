import traceback

from cryptography.fernet import InvalidToken
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.logger import logger
from fastapi.param_functions import Body, Depends
from fastapi.responses import JSONResponse

from api.security import (
    check_pw_hash,
    decrypt_dek,
    generate_encrypted_dek,
    get_current_active_user,
    hash_pw,
    update_user_with_salt_dek,
)
from api.users.schemas import UserInDB

from .db import UserDBManager
from .schemas import (
    CreateUser,
    CreateUserIn,
    CreateUserOut,
    GetUserOut,
    UpdateUserPassword,
    UpdateUserProfile,
    UpdateUserProfileOut,
)

router = APIRouter()
db = UserDBManager()


@router.post("")
async def create_user(background_tasks: BackgroundTasks, payload: CreateUser = Body(...)):
    """create new user"""
    try:
        user = await db.get_user_by_email(payload.email)
        if user:
            raise HTTPException(
                detail="user exists already with provided email",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = CreateUserIn(
            avatar=payload.avatar,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            hashed_password=hash_pw(payload.password.get_secret_value()),
        )
        record = await db.add_user(jsonable_encoder(user))
        background_tasks.add_task(
            update_user_with_salt_dek,
            record.get("_id"),
            payload.password.get_secret_value(),
        )
        return JSONResponse(
            content=jsonable_encoder(CreateUserOut(**record)),
            status_code=status.HTTP_201_CREATED,
        )
    except RuntimeError:
        logger.error(traceback.print_exc())
        raise HTTPException(
            detail="user creation failed",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.put("")
async def update_user(
    payload: UpdateUserProfile = Body(...),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """update current user"""
    try:
        payload = jsonable_encoder(payload)
        to_update = {k: v for k, v in payload.items() if v is not None}

        user = await db.update_user(current_user.id, to_update)
        return JSONResponse(
            content=jsonable_encoder(UpdateUserProfileOut(**user)),
            status_code=status.HTTP_200_OK,
        )
    except RuntimeError:
        logger.error(traceback.print_exc())
        raise HTTPException(
            detail="user updation failed",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.put("/password-change")
async def update_user_password(
    payload: UpdateUserPassword = Body(...),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """update current user's password"""
    try:
        if not check_pw_hash(
            payload.current_password.get_secret_value(),
            current_user.hashed_password.get_secret_value(),
        ):
            raise HTTPException(
                detail="invalid credentials",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if check_pw_hash(
            payload.new_password.get_secret_value(),
            current_user.hashed_password.get_secret_value(),
        ):
            raise HTTPException(
                detail="current password and new password are the same",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        dek = decrypt_dek(
            payload.current_password.get_secret_value(),
            current_user.salt.get_secret_value(),
            current_user.encrypted_dek.get_secret_value(),
        )

        _, encrypted_dek = generate_encrypted_dek(
            payload.new_password.get_secret_value(),
            current_user.salt.get_secret_value(),
            dek,
        )

        payload = jsonable_encoder(payload)
        payload["hashed_password"] = hash_pw(payload.get("new_password"))
        payload["encrypted_dek"] = encrypted_dek
        payload.pop("new_password")
        payload.pop("current_password")

        to_update = {k: v for k, v in payload.items() if v is not None}
        user = await db.update_user(current_user.id, to_update)

        # TODO: invalidate dek stored session cookie revoke jwt token
        return JSONResponse(
            content=jsonable_encoder(UpdateUserProfileOut(**user)),
            status_code=status.HTTP_200_OK,
        )
    except (InvalidToken, RuntimeError):
        logger.error(traceback.print_exc())
        raise HTTPException(
            detail="password change failed",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("")
async def get_user(current_user: UserInDB = Depends(get_current_active_user)):
    """get current user"""
    try:
        user = await db.get_user_by_id(current_user.id)

        return JSONResponse(
            content=jsonable_encoder(GetUserOut(**user)),
            status_code=status.HTTP_200_OK,
        )
    except RuntimeError:
        logger.error(traceback.print_exc())
        raise HTTPException(
            detail="user fetch failed",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
