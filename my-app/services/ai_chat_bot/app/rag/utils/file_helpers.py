import asyncio
import hashlib
from pathlib import Path


async def get_file_size(file_path: str | Path) -> int:
    path = Path(file_path)
    return await asyncio.to_thread(lambda: path.stat().st_size)


async def calculate_checksum(file_path: str | Path, algorithm: str = "sha256") -> str:
    path = Path(file_path)

    def _calculate() -> str:
        digest = hashlib.new(algorithm)
        with path.open("rb") as file:
            for block in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    return await asyncio.to_thread(_calculate)


def normalize_extension(file_path: str | Path) -> str:
    return Path(file_path).suffix.lower().strip()


def safe_filename(file_path: str | Path) -> str:
    return Path(file_path).name

