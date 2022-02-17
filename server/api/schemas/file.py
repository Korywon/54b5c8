from datetime import datetime
from typing import Union

from pydantic import BaseModel


class File(BaseModel):
    id: int
    filename: str
    file_size_bytes: int
    total_rows: int
    done_rows: int
    uploaded_at: datetime
    done_at: datetime

    class Config:
        orm_mode = True


class FileCreate(BaseModel):
    filename: str
    file_size_bytes: int
    total_rows: int


class FileProgressResponse(BaseModel):
    total: int
    done: int
    done_at: Union[datetime, None]
