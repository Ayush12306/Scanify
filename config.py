"""Application paths and safe local-storage configuration."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
ORIGINALS_DIR = STORAGE_DIR / "originals"
PROCESSED_DIR = STORAGE_DIR / "processed"
EXPORTS_DIR = STORAGE_DIR / "exports"
DATABASE_PATH = STORAGE_DIR / "scanify.sqlite3"
MAX_UPLOAD_MB = 20
for directory in (ORIGINALS_DIR, PROCESSED_DIR, EXPORTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)
