from fastapi import APIRouter, HTTPException, status, Depends, UploadFile
from sqlalchemy.orm.session import Session
from api import schemas
from api.dependencies.auth import get_current_user
from api.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_SIZE, MAX_IMPORT_FILE_SIZE
from api.crud import ProspectCrud, FileCrud
from api.dependencies.db import get_db
import csv
import codecs
import os
import re

router = APIRouter(prefix="/api", tags=["prospects", "prospects_files"])
email_pattern = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


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


@router.get(
    "/prospects_files/{file_id}/progress", response_model=schemas.FileProgressResponse
)
def get_prospects_file_progress(
    file_id: int,
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in"
        )
    progress = FileCrud.get_file_progress(db, current_user.id, file_id)
    return progress


@router.post("/prospect_files/import", response_model=schemas.ProspectImportResponse)
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
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in"
        )

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

    # Create file entry in database.
    current_file = FileCrud.create_file(
        db,
        current_user.id,
        {
            "filename": file.filename,
            "file_size": file_size_bytes,
            "total_rows": num_rows,
        },
    )

    # Response payload describing summary of the import.
    summary = {
        "total": num_rows,
        "skipped": 0,
        "created": 0,
        "updated": 0,
    }

    # Time to rock and roll... parse the CSV.
    for i, row in enumerate(csv_rows):
        # Skip header row.
        if not i and has_headers:
            continue

        # Skip any rows if the indexes are out of range.
        num_col = len(row)
        if any(idx >= num_col for idx in indexes):
            print(f"{i}/{num_rows} SKIPPED")
            summary["skipped"] += 1
            continue

        email = row[email_index]
        first_name = ""
        last_name = ""

        # Attempt to validate the email.
        if not email_pattern.match(email):
            print(f"{i}/{num_rows} {email} SKIPPED (bad email)")
            summary["skipped"] += 1
            continue

        # Grab first and last name if we were given indexes.
        if first_name_index != None:
            first_name = row[first_name_index]
        if last_name_index != None:
            last_name = row[last_name_index]

        prospect = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }

        exists = ProspectCrud.prospect_exists(db, current_user.id, email)

        # Only update if forcing and entry exists.
        # Only create prospects if we don't have an existing prospect.
        if force and exists:
            ProspectCrud.update_prospect(db, current_user.id, prospect)
            summary["updated"] += 1
        elif not exists:
            ProspectCrud.create_prospect(db, current_user.id, prospect)
            summary["created"] += 1
        else:
            print(f"{i}/{num_rows} {email} {first_name} {last_name} SKIPPED")
            summary["skipped"] += 1

        # Update the rows done in the database.
        FileCrud.update_file_progress(db, current_user.id, current_file.id)

    # Update the finished date time of file.
    FileCrud.update_file_done_at(db, current_user.id, current_file.id)

    return summary
