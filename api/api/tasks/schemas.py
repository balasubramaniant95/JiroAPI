import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel
from pydantic.fields import Field


class PriorityType(str, Enum):
    critical = "Critical"
    high = "High"
    medium = "Medium"
    low = "Low"


class StatusType(str, Enum):
    to_do = "To Do"
    in_the_works = "In The Works"
    needs_review = "Needs Review"
    finished = "Finished"
    dropped = "Dropped"


class ToDoItem(BaseModel):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    item: str
    is_done: bool
    created: Optional[datetime] = Field(default_factory=datetime.now)


class Comment(BaseModel):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
    comment: str
    created: Optional[datetime] = Field(default_factory=datetime.now)


# schemas for "get task"
class TaskInDB(BaseModel):
    title: str
    topic: Optional[str]
    priority: Optional[PriorityType]
    status: Optional[StatusType]
    description: Optional[str]
    estimate: Optional[int]
    starts: Optional[datetime]
    due: Optional[datetime]
    comments: Optional[List[Comment]]
    todo_items: Optional[List[ToDoItem]]


class TaskInDBWrapped(BaseModel):
    id: str = Field(None, alias="_id")
    task_data: TaskInDB
    created_by: str
    created: datetime
    modified: Optional[datetime]
    archived: bool


# schemas for "create task"
class AddTask(BaseModel):
    title: str
    topic: Optional[str]
    priority: Optional[PriorityType] = PriorityType.low
    status: Optional[StatusType] = StatusType.to_do
    description: Optional[str]
    estimate: Optional[int]
    starts: Optional[datetime]
    due: Optional[datetime]


class AddTaskWrapped(BaseModel):
    task_data: AddTask
    created_by: Optional[str]
    created: Optional[datetime] = Field(default_factory=datetime.now)
    archived: Optional[bool] = False


# schemas for "update task"
class UpdateTask(BaseModel):
    title: Optional[str]
    topic: Optional[str]
    priority: Optional[PriorityType]
    status: Optional[StatusType]
    description: Optional[str]
    estimate: Optional[int]
    starts: Optional[datetime]
    due: Optional[datetime]
    comments: Optional[List[Comment]]
    todo_items: Optional[List[ToDoItem]]


class UpdateTaskWrapped(BaseModel):
    task_data: UpdateTask
    archived: Optional[bool] = False
    modified: Optional[datetime] = Field(default_factory=datetime.now)
