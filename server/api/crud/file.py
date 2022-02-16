from sqlalchemy.orm.session import Session
from sqlalchemy.sql.functions import func
from api import schemas
from api.models import File


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
            .first()
        )

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
            .first()
        )

    @classmethod
    def get_file_progress(
        cls, db: Session, user_id: int, file_id: int
    ) -> schemas.FileProgressResponse:
        file = cls.get_file(db, user_id, file_id)
        return {"total": file.total_rows, "done": file.done_rows}

    @classmethod
    def update_file_progress(cls, db: Session, user_id: int, file_id: int):
        file = cls.get_file(db, user_id, file_id)
        file.done_rows += 1
        db.commit()

    @classmethod
    def update_file_done_at(cls, db: Session, user_id: int, file_id: int):
        file = cls.get_file(db, user_id, file_id)
        file.done_at = func.now()
        db.commit()
