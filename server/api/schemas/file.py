from datetime import datetime

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


class FileProgress(BaseModel):
    total_rows: int
    done_rows: int
