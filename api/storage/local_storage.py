"""
AEGIS-X API Local Filesystem Storage Provider.

Implements IStorageProvider using local filesystem under settings.STORAGE_DIR with user isolation.
"""

import json
from pathlib import Path
from typing import Any, Dict

from aegis.core.exceptions import AegisError
from api.core.config import settings
from api.storage.base import IStorageProvider


class PathTraversalError(AegisError):
    """Raised when a file path attempts traversal outside allowed storage directory."""
    pass


class LocalStorageProvider(IStorageProvider):
    """Local filesystem storage implementation with path traversal defense."""

    def __init__(self, base_dir: Path = settings.STORAGE_DIR) -> None:
        self.base_dir = base_dir.resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, relative_key: str, user_id: str = "local_dev_user") -> Path:
        """Resolves relative key into safe absolute path scoped by user_id."""
        clean_key = Path(relative_key.lstrip("/\\"))
        
        # Scope by user_id if not already prefix-scoped
        if clean_key.parts and clean_key.parts[0] == "users":
            target_path = (self.base_dir / clean_key).resolve()
        else:
            target_path = (self.base_dir / "users" / user_id / clean_key).resolve()

        if not str(target_path).startswith(str(self.base_dir)):
            raise PathTraversalError(f"Access denied: path '{relative_key}' attempts traversal outside storage root.")

        return target_path

    def save_file(self, relative_key: str, content: bytes, user_id: str = "local_dev_user") -> str:
        safe_path = self._resolve_safe_path(relative_key, user_id)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_bytes(content)
        return str(safe_path)

    def load_file(self, relative_key: str, user_id: str = "local_dev_user") -> bytes:
        safe_path = self._resolve_safe_path(relative_key, user_id)
        if not safe_path.exists():
            raise FileNotFoundError(f"Stored file '{relative_key}' not found.")
        return safe_path.read_bytes()

    def save_json(self, relative_key: str, data: Dict[str, Any], user_id: str = "local_dev_user") -> str:
        json_bytes = json.dumps(data, indent=2).encode("utf-8")
        return self.save_file(relative_key, json_bytes, user_id)

    def load_json(self, relative_key: str, user_id: str = "local_dev_user") -> Dict[str, Any]:
        file_bytes = self.load_file(relative_key, user_id)
        return json.loads(file_bytes.decode("utf-8"))

    def delete_file(self, relative_key: str, user_id: str = "local_dev_user") -> bool:
        try:
            safe_path = self._resolve_safe_path(relative_key, user_id)
            if safe_path.exists():
                safe_path.unlink()
                return True
            return False
        except Exception:
            return False
