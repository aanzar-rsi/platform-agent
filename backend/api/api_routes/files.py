from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from api.core.deps import require_user
from api.domain.files import FilePickRequest, FilePickResponse
from api.services.file_picker_service import FilePickerService

router = APIRouter(
    prefix="/files",
    tags=["files"],
    dependencies=[Depends(require_user)],
)


@router.post("/pick", response_model=FilePickResponse)
def pick_files(body: FilePickRequest) -> FilePickResponse:
    paths = FilePickerService().pick(body.mode, multiple=body.multiple)
    return FilePickResponse(paths=paths, cancelled=not paths)
