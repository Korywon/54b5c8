from sqlalchemy.orm.session import Session
from sqlalchemy.sql.functions import func
from api import schemas
from api.models import File, Prospect
from typing import Union


class FileCrud:
    @classmethod
    def create_file(cls, db: Session, user_id: int, data: schemas.FileCreate) -> File:
        file = File(
            filename=data["filename"],
            file_size=data["file_size"],
            total_rows=data["total_rows"],
            user_id=user_id,
        )
        db.add(file)
        db.commit()
        db.refresh(file)
        return file

    @classmethod
    def get_file(
        cls,
        db: Session,
        user_id: int,
        file_id: int,
    ) -> File:
        return (
            db.query(File)
            .filter(File.user_id == user_id)
            .filter(File.id == file_id)
            .one_or_none()
        )

    @classmethod
    def get_file_progress(
        cls, db: Session, user_id: int, file_id: int
    ) -> Union[schemas.FileProgressResponse, None]:
        file = cls.get_file(db, user_id, file_id)
        if not file:
            return None
         done_rows = (
               db.query(Prospect)
               .filter(Prospect.user_id == user_id)
               .filter(Prospect.file_id == file_id)
               .count()
         )

         return schemas.FileProgressResponse(
               total=file.total_rows, done=done_rows, done_at=file.done_at
         )

    @classmethod
    def update_file_done_at(cls, db: Session, user_id: int, file_id: int):
        file = cls.get_file(db, user_id, file_id)
        file.done_at = func.now()
        db.commit()
