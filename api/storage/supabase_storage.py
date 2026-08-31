"""
AEGIS-X API Supabase Storage Provider.

Implements IStorageProvider using private Supabase Storage buckets under user-scoped paths (users/<user_id>/...).
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
import httpx

from aegis.core.exceptions import AegisError
from api.core.config import settings
from api.storage.base import IStorageProvider


class SupabaseStorageError(AegisError):
    """Raised when Supabase Storage provider operation fails."""
    pass


class SupabaseStorageProvider(IStorageProvider):
    """Private Supabase Storage Provider implementation."""

    def __init__(self, client: Optional[httpx.Client] = None) -> None:
        if not settings.SUPABASE_URL or not (settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY):
            raise SupabaseStorageError(
                "STORAGE_BACKEND=supabase requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY) environment variables."
            )

        self.bucket = settings.SUPABASE_STORAGE_BUCKET
        self.url = f"{settings.SUPABASE_URL}/storage/v1/object/{self.bucket}"
        self.key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
        }
        self.client = client or httpx.Client(timeout=15.0)

    def _resolve_object_key(self, relative_key: str, user_id: str = "local_dev_user") -> str:
        clean_key = relative_key.lstrip("/\\").replace("\\", "/")
        if clean_key.startswith("users/"):
            return clean_key
        return f"users/{user_id}/{clean_key}"

    def save_file(self, relative_key: str, content: bytes, user_id: str = "local_dev_user") -> str:
        object_key = self._resolve_object_key(relative_key, user_id)
        endpoint = f"{self.url}/{object_key}"

        # Upload with upsert header
        headers = {**self.headers, "x-upsert": "true", "Content-Type": "application/octet-stream"}
        res = self.client.post(endpoint, headers=headers, content=content)
        if res.status_code not in (200, 201):
            raise SupabaseStorageError(f"Failed to upload object to Supabase storage '{object_key}': {res.text}")
        return object_key

    def load_file(self, relative_key: str, user_id: str = "local_dev_user") -> bytes:
        object_key = self._resolve_object_key(relative_key, user_id)
        endpoint = f"{self.url}/{object_key}"

        res = self.client.get(endpoint, headers=self.headers)
        if res.status_code != 200:
            raise FileNotFoundError(f"Stored object '{object_key}' not found in Supabase storage.")
        return res.content

    def save_json(self, relative_key: str, data: Dict[str, Any], user_id: str = "local_dev_user") -> str:
        json_bytes = json.dumps(data, indent=2).encode("utf-8")
        return self.save_file(relative_key, json_bytes, user_id)

    def load_json(self, relative_key: str, user_id: str = "local_dev_user") -> Dict[str, Any]:
        file_bytes = self.load_file(relative_key, user_id)
        return json.loads(file_bytes.decode("utf-8"))

    def delete_file(self, relative_key: str, user_id: str = "local_dev_user") -> bool:
        object_key = self._resolve_object_key(relative_key, user_id)
        endpoint = f"{self.url}/{object_key}"

        res = self.client.delete(endpoint, headers=self.headers)
        return res.status_code in (200, 204)
