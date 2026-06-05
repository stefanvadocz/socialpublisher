"""Seed the database with sample suggestions for local development.

Run: ``python scripts/seed.py``  (clears prior demo rows, then re-inserts them).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a plain script (`python scripts/seed.py`).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal, init_db  # noqa: E402
from app.demo_seed import reseed  # noqa: E402


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        count = reseed(db)
        print(f"Seeded {count} suggestions. Run: uvicorn app.main:app --reload")
    finally:
        db.close()


if __name__ == "__main__":
    main()
