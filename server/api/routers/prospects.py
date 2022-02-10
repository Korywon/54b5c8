from fastapi import APIRouter, HTTPException, status, Depends, UploadFile
from sqlalchemy.orm.session import Session
from api import schemas
from api.dependencies.auth import get_current_user
from api.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_IMPORT_FILE_SIZE
from api.crud import ProspectCrud
from api.dependencies.db import get_db
import csv
import codecs
import os

router = APIRouter(prefix="/api", tags=["prospects", "prospects_files"])


@router.get("/prospects", response_model=schemas.ProspectResponse)
def get_prospects_page(
    current_user: schemas.User = Depends(get_current_user),
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    db: Session = Depends(get_db),
):
    """Get a single page of prospects"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in"
        )
    prospects = ProspectCrud.get_users_prospects(db, current_user.id, page, page_size)
    total = ProspectCrud.get_user_prospects_total(db, current_user.id)
    return {"prospects": prospects, "size": len(prospects), "total": total}


# TODO: Get progress on the file.
@router.get("/prospects_files/{file_id}/progress")
def get_prospects_file_progress(
    file_id: int,
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in"
        )
    return {"total": 0, "done": 0}


# TODO: Parse, validate, and import prospects.
@router.post("/prospect_files/import")
def import_prospects_file(
    email_index: int,
    file: UploadFile,
    first_name_index: int = None,
    last_name_index: int = None,
    force: bool = False,
    has_headers: bool = False,
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # TODO: Commented out for debugging. Uncomment this.
    # if not current_user:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in"
    #     )

    # Holds the different indexes. Will be used to find duplicates.
    indexes = [email_index]

    # Only add indexes if they are not the default.
    if first_name_index != None:
        indexes.append(first_name_index)
    if last_name_index != None:
        indexes.append(last_name_index)

    # The set of indexes should be the same as the list of indexes. If they are
    # not the same, that indicates we have duplicates.
    if len(indexes) != len(set(indexes)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Indexes cannot be the same",
        )

    # Check if any of the indexes are less than zero.
    if any(idx < 0 for idx in indexes):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Indexes cannot be below 0",
        )

    # Decode file into a CSV reader object.
    csv_file = csv.reader(codecs.iterdecode(file.file, "utf-8"))
    csv_rows = list(csv_file)
    num_rows = len(csv_rows) - int(has_headers)

    # Go to the end of the file and get the file size.
    file.file.seek(0, os.SEEK_END)
    file_size_bytes = file.file.tell()

    # Check file size does not exceed the max file size.
    if file_size_bytes > MAX_IMPORT_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File size cannot exceed {MAX_IMPORT_FILE_SIZE} bytes",
        )

    # TODO: Check to make sure that the indexes do not exceed the columns.

    # TODO: This is a test of the prospect_exists() function.
    # print(ProspectCrud.prospect_exists(db, "prospect00@mail.com"))

    # Time to rock and roll... parse the CSV.
    for i, row in enumerate(csv_rows):
        # Skip header row.
        if not i and has_headers:
            continue

        email = row[email_index]
        first_name = ""
        last_name = ""

        if first_name_index != None:
            first_name = row[first_name_index]
        if last_name_index != None:
            last_name = row[last_name_index]

        if force or not ProspectCrud.prospect_exists(db, "prospect00@mail.com"):
            print(f"creating prospect {email}")
            # TODO: create a prospect and shove it into database
        else:
            print(f"skipped prospect {email}")
            # TODO: add skipped number
        # print(f"{i}/{num_rows} {email} {first_name} {last_name}")

    return {"message": "hello world"}
