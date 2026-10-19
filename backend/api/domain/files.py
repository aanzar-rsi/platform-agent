from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class FilePickRequest(BaseModel):
    mode: Literal["files", "directory"] = "files"
    multiple: bool = True


class FilePickResponse(BaseModel):
    paths: list[str] = Field(default_factory=list)
    cancelled: bool = False
