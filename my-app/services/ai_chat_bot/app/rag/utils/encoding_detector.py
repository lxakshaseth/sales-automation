import asyncio
from pathlib import Path


class EncodingDetector:
    """
    Lightweight encoding detector placeholder.

    A future RAG layer can replace this with charset-normalizer/chardet or a
    managed document processing service without changing the text loader API.
    """

    DEFAULT_ENCODING = "utf-8"
    FALLBACK_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")

    async def detect(self, file_path: str | Path) -> str:
        path = Path(file_path)
        sample = await asyncio.to_thread(lambda: path.read_bytes()[:4096])

        for encoding in self.FALLBACK_ENCODINGS:
            try:
                sample.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue

        return self.DEFAULT_ENCODING
