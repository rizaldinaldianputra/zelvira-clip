import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from app.core.config import settings
from app.core.logging import logger

class StorageProvider(ABC):
    @abstractmethod
    def save_bytes(self, relative_path: str, data: bytes) -> str:
        """Saves bytes to the storage location."""
        pass

    @abstractmethod
    def get_full_path(self, relative_path: str) -> str:
        """Resolves the absolute path safely."""
        pass

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Checks if a file exists."""
        pass

    @abstractmethod
    def delete_file(self, relative_path: str) -> bool:
        """Deletes a file."""
        pass

    @abstractmethod
    def delete_directory(self, relative_path: str) -> bool:
        """Deletes an entire directory recursively."""
        pass

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.STORAGE_PATH).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _safe_resolve(self, relative_path: str) -> Path:
        """
        Prevents path traversal attacks by ensuring the resolved path
        is strictly inside self.base_dir.
        """
        clean_path = os.path.normpath(relative_path).lstrip("/\\")
        target = (self.base_dir / clean_path).resolve()
        if not str(target).startswith(str(self.base_dir)):
            raise ValueError(f"Path traversal detected: {relative_path}")
        return target

    def save_bytes(self, relative_path: str, data: bytes) -> str:
        target = self._safe_resolve(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as f:
            f.write(data)
        return str(target)

    def get_full_path(self, relative_path: str) -> str:
        return str(self._safe_resolve(relative_path))

    def exists(self, relative_path: str) -> bool:
        target = self._safe_resolve(relative_path)
        return target.exists()

    def delete_file(self, relative_path: str) -> bool:
        target = self._safe_resolve(relative_path)
        if target.exists() and target.is_file():
            target.unlink()
            return True
        return False

    def delete_directory(self, relative_path: str) -> bool:
        target = self._safe_resolve(relative_path)
        if target.exists() and target.is_dir():
            shutil.rmtree(target)
            return True
        return False

# Default global storage provider
storage: StorageProvider = LocalStorageProvider()
