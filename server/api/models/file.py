from http import server
from time import timezone
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import BigInteger, Boolean, DateTime, Integer, String

from api.database import Base


class File(Base):
    """Files table"""

    __tablename__ = "files"

    id = Column(BigInteger, primary_key=True, autoincrement=True, unique=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    filename = Column(String, index=True, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    total_rows = Column(Integer, nullable=False)
    done_rows = Column(Integer, default=0)

    user = relationship("User", back_populates="files", foreign_keys=[user_id])
    prospects = relationship("Prospect", back_populates="file")

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    done_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"{self.id} | {self.filename}"
