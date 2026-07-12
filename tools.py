from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Union

ToolResult = Union[str, list[dict[str, Any]]]
ToolHandler = Callable[[dict[str, Any]], Awaitable[ToolResult]]


@dataclass
class Tool:
    """An OpenAI function definition bundled with its implementation."""

    definition: dict[str, Any]
    handler: ToolHandler

    @property
    def name(self) -> str:
        return self.definition["name"]

    async def run(self, arguments: dict[str, Any]) -> ToolResult:
        print(f"[TOOL={self.name}] {json.dumps(arguments)}")
        result = await self.handler(arguments)

        if isinstance(result, str):
            preview = "\n".join(result.splitlines()[:5])
            print(f"[TOOL={self.name}] {preview}")
        else:
            for block in result:
                if block["type"] == "input_image":
                    print(f"[TOOL={self.name}] [image returned]")
                elif block["type"] == "input_text":
                    preview = "\n".join(block["text"].splitlines()[:5])
                    print(f"[TOOL={self.name}] {preview}")

        return result
