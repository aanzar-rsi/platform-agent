from __future__ import annotations

import os
from typing import Literal


class FilePickerService:
    """Native OS file/folder picker — returns absolute paths for local agent tools."""

    def pick(self, mode: Literal["files", "directory"], multiple: bool = True) -> list[str]:
        if mode == "directory":
            paths = self._pick_directory()
        else:
            paths = self._pick_files(multiple=multiple)
        return [self._normalize_path(p) for p in paths if p]

    @staticmethod
    def _normalize_path(path: str) -> str:
        cleaned = os.path.normpath(path.strip())
        if os.name == "nt":
            return cleaned.replace("/", "\\")
        return cleaned

    @staticmethod
    def _pick_files(multiple: bool) -> list[str]:
        from tkinter import Tk, filedialog

        root = Tk()
        root.withdraw()
        root.update()
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        try:
            if multiple:
                selected = filedialog.askopenfilenames(parent=root)
                return list(selected) if selected else []
            selected = filedialog.askopenfilename(parent=root)
            return [selected] if selected else []
        finally:
            root.destroy()

    @staticmethod
    def _pick_directory() -> list[str]:
        from tkinter import Tk, filedialog

        root = Tk()
        root.withdraw()
        root.update()
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        try:
            selected = filedialog.askdirectory(parent=root, mustexist=True)
            return [selected] if selected else []
        finally:
            root.destroy()
