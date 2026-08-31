"""
AEGIS-X API Storage Provider Protocols & Interfaces.

Defines abstract interface for file binary and JSON result payload storage.
Implemented by LocalStorageProvider (filesystem) and SupabaseStorageProvider (private Supabase buckets).
"""

from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class IStorageProvider(Protocol):
    """Abstract storage provider protocol."""

    def save_file(self, relative_key: str, content: bytes, user_id: str = "local_dev_user") -> str:
        """Saves binary file bytes under user-scoped storage key and returns storage path key."""
        ...

    def load_file(self, relative_key: str, user_id: str = "local_dev_user") -> bytes:
        """Loads binary file bytes for given storage key and user identity."""
        ...

    def save_json(self, relative_key: str, data: Dict[str, Any], user_id: str = "local_dev_user") -> str:
        """Saves JSON result payload under user-scoped storage key and returns storage path key."""
        ...

    def load_json(self, relative_key: str, user_id: str = "local_dev_user") -> Dict[str, Any]:
        """Loads JSON result payload for given storage key and user identity."""
        ...

    def delete_file(self, relative_key: str, user_id: str = "local_dev_user") -> bool:
        """Deletes file or object under given key."""
        ...
