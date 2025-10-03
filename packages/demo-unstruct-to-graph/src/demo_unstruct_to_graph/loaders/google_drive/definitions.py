from dataclasses import dataclass
from typing import Any, override


def ensure_str(x: Any) -> str:  # pyright: ignore[reportExplicitAny, reportAny]
    if not isinstance(x, str):
        return str(x)  # pyright: ignore[reportAny]
    return x


@dataclass
class FileHandle:
    id: str
    name: str
    kind: str
    mimeType: str

    @classmethod
    def from_dict(cls, file: Any) -> "FileHandle":  # pyright: ignore[reportExplicitAny, reportAny]
        if not isinstance(file, dict):
            raise ValueError("Invalid file format")
        return cls(
            id=ensure_str(file["id"]),
            name=ensure_str(file["name"]),
            kind=ensure_str(file["kind"]),
            mimeType=ensure_str(file["mimeType"]),
        )

    @classmethod
    def build_fields_param(cls) -> str:
        return "nextPageToken, files(id, name, kind, mimeType)"

    @property
    def is_folder(self) -> bool:
        return self.mimeType == "application/vnd.google-apps.folder"

    @override
    def __str__(self) -> str:
        pre = "📁 Folder" if self.is_folder else "📄 File"
        return f"{pre}: {self.name} (ID: {self.id}, kind: {self.kind}, mimeType: {self.mimeType})"
