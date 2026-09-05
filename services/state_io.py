import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any


def atomic_write_text(path: str | Path, content: str) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temp_path, destination)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def atomic_write_json(path: str | Path, data: Any) -> None:
    content = json.dumps(data, ensure_ascii=False, indent=2)
    atomic_write_text(path, f"{content}\n")


def atomic_write_many_text(files: dict[str | Path, str]) -> None:
    """Stage multiple text files, then replace destinations with rollback on failure."""
    staged: list[tuple[Path, Path]] = []
    backups: list[tuple[Path, Path]] = []
    transaction_id = uuid.uuid4().hex

    try:
        for path, content in files.items():
            destination = Path(path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temp_path = Path(handle.name)
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            staged.append((destination, temp_path))

        for destination, temp_path in staged:
            backup_path = destination.with_name(f".{destination.name}.{transaction_id}.bak")
            if destination.exists():
                os.replace(destination, backup_path)
                backups.append((destination, backup_path))
            os.replace(temp_path, destination)

        for _, backup_path in backups:
            if backup_path.exists():
                backup_path.unlink()
    except Exception:
        for destination, backup_path in reversed(backups):
            if backup_path.exists():
                if destination.exists():
                    destination.unlink()
                os.replace(backup_path, destination)
        raise
    finally:
        for _, temp_path in staged:
            if temp_path.exists():
                temp_path.unlink()
