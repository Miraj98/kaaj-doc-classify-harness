from __future__ import annotations

import json
from pathlib import Path


class File:
    """A local PDF and its cached page-by-page OCR."""

    def __init__(self, path: str | Path, ocr_path: str | Path | None = None):
        self.path = Path(path)
        self.ocr_path = (
            Path(ocr_path)
            if ocr_path
            else Path(__file__).parent / "data" / "ocr" / f"{self.path.stem}.json"
        )
        self._content: bytes | None = None
        self._parsed_content: list[str] | None = None

    def get_filename(self) -> str:
        return self.path.name

    async def get_content(self) -> bytes:
        if self._content is None:
            self._content = self.path.read_bytes()
        return self._content

    async def get_parsed_content(self) -> list[str]:
        if self._parsed_content is None:
            self._parsed_content = json.loads(self.ocr_path.read_text())
        return self._parsed_content

    async def get_page_count(self) -> int:
        return len(await self.get_parsed_content())

    async def get_page_text(self, page_number: int) -> str:
        pages = await self.get_parsed_content()
        return pages[page_number - 1]

    async def get_page_lines(
        self,
        page_number: int,
        count: int = 25,
        from_end: bool = False,
    ) -> str:
        lines = (await self.get_page_text(page_number)).splitlines()
        selected = lines[-count:] if from_end else lines[:count]
        return "\n".join(selected)
