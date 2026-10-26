#!/usr/bin/env python3
"""Bundle source files while excluding credentials, captures, and model files."""

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARCHIVE_NAME = "exam-monitor.zip"
TOP_LEVEL_FOLDER = "exam-monitor"

FILES = [
    "main.py",
    "config.py",
    "integrations.py",
    "requirements.txt",
    ".env.example",
    ".gitignore",
    "README.md",
    "package_project.py",
    "setup.sh",
    "setup.ps1",
    "run.sh",
    "run.ps1",
]


def main() -> int:
    missing = [name for name in FILES if not (ROOT / name).is_file()]
    if missing:
        print("ERROR - these project files are missing, nothing was packaged:")
        for name in missing:
            print(f"  - {name}")
        return 1

    archive = ROOT / ARCHIVE_NAME
    if archive.exists():
        archive.unlink()

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in FILES:
            zf.write(ROOT / name, arcname=f"{TOP_LEVEL_FOLDER}/{name}")

    with zipfile.ZipFile(archive) as zf:
        if zf.testzip() is not None:
            print("ERROR - the archive failed its integrity check.")
            return 2
        print(f"Created {archive}  ({archive.stat().st_size / 1024:.1f} KB)")
        for info in zf.infolist():
            print(f"  + {info.filename:<40} {info.file_size:>8,} bytes")

    print("\nDone. Unzip it, then follow README.md (Quick start).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
