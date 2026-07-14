"""
Storage backend selector.

Chooses the storage implementation at import time based on the
STORAGE_BACKEND environment variable:

    (unset) / "sqlite"  → src.storage          (local development)
    "dynamodb"          → src.storage_dynamodb  (AWS deployment)

Both modules expose identical function signatures, so the rest of the
app imports `storage` from here and never needs to know which is active.
"""

import os

if os.getenv("STORAGE_BACKEND", "sqlite") == "dynamodb":
    from src import storage_dynamodb as storage
else:
    from src import storage as storage

__all__ = ["storage"]
