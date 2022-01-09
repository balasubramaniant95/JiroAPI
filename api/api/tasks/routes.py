import traceback

from app import CacheManager
from fastapi import APIRouter, BackgroundTasks, Cookie, HTTPException, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.logger import logger
from fastapi.param_functions import Body, Depends
from fastapi.responses import JSONResponse
from mergedeep import Strategy, merge

from api.security import decrypt_payload, encrypt_payload, get_current_active_user
from api.users.schemas import UserInDB

from .db import TaskDBManager
from .schemas import AddTaskWrapped, TaskInDBWrapped, UpdateTaskWrapped

router = APIRouter()
db = TaskDBManager()


@router.get("/{id}")
async def get_task(
    id: str,
    background_tasks: BackgroundTasks,
    dek: str = Cookie(None),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """fetch user's task"""
    try:
        task = await CacheManager.fetch(id)
        if not task:
            task = await db.get_task_by_id(id)

        if not task:
            raise HTTPException(detail="task not found", status_code=status.HTTP_404_NOT_FOUND)

        background_tasks.add_task(CacheManager.store, id, task)
        if task.get("created_by") != current_user.id:
            raise HTTPException(
                detail="not enough permissions",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        task["task_data"] = decrypt_payload(dek, task["task_data"])
        if not task["task_data"]:
            raise HTTPException(
                detail="task data empty or unable to decrypt data (invalid dek)", 
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return JSONResponse(
            content=jsonable_encoder(TaskInDBWrapped(**task)),
            status_code=status.HTTP_200_OK,
        )
    except RuntimeError:
        logger.error(traceback.print_exc())
        raise HTTPException(
            detail="task fetch failed",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("")
async def get_tasks(
    background_tasks: BackgroundTasks,
    skip: int = 0,
    limit: int = 25,
    dek: str = Cookie(None),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """fetch multiple user's tasks"""
    try:
        key = f"({current_user.id})({skip},{limit})"
        tasks = await CacheManager.fetch(key)
        if not tasks:
            tasks = await db.get_tasks_by_created_by(current_user.id, skip, limit)

        if not tasks:
            raise HTTPException(detail="tasks not found", status_code=status.HTTP_404_NOT_FOUND)

        background_tasks.add_task(CacheManager.store, key, tasks)

        tasks_out = []
        for task in tasks:
            task["task_data"] = decrypt_payload(dek, task["task_data"])
            if not task["task_data"]:
                raise HTTPException(
                    detail="task data empty or unable to decrypt data (invalid dek)", 
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            tasks_out.append(jsonable_encoder(TaskInDBWrapped(**task)))

        return JSONResponse(content=tasks_out, status_code=status.HTTP_200_OK)
    except RuntimeError:
        logger.error(traceback.print_exc())
        raise HTTPException(
            detail="task fetch failed",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("")
async def create_task(
    background_tasks: BackgroundTasks,
    payload: AddTaskWrapped = Body(...),
    dek: str = Cookie(None),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """create new user's task"""
    try:
        payload.created_by = current_user.id
        payload = jsonable_encoder(payload)
        payload["task_data"] = encrypt_payload(dek, payload["task_data"])

        task = await db.add_task(payload)
        background_tasks.add_task(CacheManager.store, task.get("_id"), task)
        background_tasks.add_task(CacheManager.delete, f"""({task.get("created_by")})(*)""", True)

        task["task_data"] = decrypt_payload(dek, task["task_data"])
        if not task["task_data"]:
            raise HTTPException(
                detail="task data empty or unable to decrypt data (invalid dek)", 
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return JSONResponse(
            content=jsonable_encoder(TaskInDBWrapped(**task)),
            status_code=status.HTTP_201_CREATED,
        )
    except RuntimeError:
        logger.error(traceback.print_exc())
        raise HTTPException(
            detail="task creation failed",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.put("/{id}")
async def update_task(
    id: str,
    background_tasks: BackgroundTasks,
    payload: UpdateTaskWrapped = Body(...),
    dek: str = Cookie(None),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """update user's task"""

    def __recursive_parse(d: dict):
        for k, v in d.copy().items():
            if isinstance(v, dict):
                __recursive_parse(v)
            else:
                if v is None:
                    del d[k]

    try:
        task = await db.get_task_by_id(id)
        if not task:
            raise HTTPException(detail="task not found", status_code=status.HTTP_404_NOT_FOUND)

        if task.get("created_by") != current_user.id:
            raise HTTPException(
                detail="not enough permissions",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        payload = jsonable_encoder(payload)
        __recursive_parse(payload)

        if payload.get("task_data"):
            task["task_data"] = decrypt_payload(dek, task["task_data"])
            if not task["task_data"]:
                raise HTTPException(
                    detail="task data empty or unable to decrypt data (invalid dek)", 
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            _task = task.copy()
            _task["task_data"] = merge({}, task["task_data"], payload["task_data"], strategy=Strategy.REPLACE)
            _task["task_data"]["todo_items"] = merge({}, task["task_data"], payload["task_data"], strategy=Strategy.REPLACE).get("todo_items")
            _task["task_data"]["comments"] = merge({}, task["task_data"], payload["task_data"], strategy=Strategy.ADDITIVE).get("comments")

            task["task_data"] = encrypt_payload(dek, _task["task_data"])
            task.pop("_id")
            
            _ = await db.replace_task(id, task)
            payload.pop("task_data")

        task = await db.update_task(id, payload)
        background_tasks.add_task(CacheManager.store, id, task)
        background_tasks.add_task(CacheManager.delete, f"({current_user.id})(*)", True)

        task["task_data"] = decrypt_payload(dek, task["task_data"])
        if not task["task_data"]:
            raise HTTPException(
                detail="task data empty or unable to decrypt data (invalid dek)", 
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return JSONResponse(
            content=jsonable_encoder(TaskInDBWrapped(**task)),
            status_code=status.HTTP_201_CREATED,
        )
    except RuntimeError:
        logger.error(traceback.print_exc())
        raise HTTPException(
            detail="task updation failed",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.delete("/{id}")
async def delete_task(
    id: str,
    background_tasks: BackgroundTasks,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """delete user's task"""
    try:
        task = await db.get_task_by_id(id)
        if not task:
            raise HTTPException(detail="task not found", status_code=status.HTTP_404_NOT_FOUND)

        if task.get("created_by") != current_user.id:
            raise HTTPException(
                detail="not enough permissions",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        _ = await db.delete_task(id)

        background_tasks.add_task(CacheManager.delete, id)
        background_tasks.add_task(CacheManager.delete, f"({current_user.id})(*)", True)
        return Response(content=None, status_code=status.HTTP_204_NO_CONTENT)
    except RuntimeError:
        logger.error(traceback.print_exc())
        raise HTTPException(
            detail="task deletion failed",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
