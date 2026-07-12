from __future__ import annotations

import asyncio
import json
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI

from tools import Tool, ToolResult

MODEL = "gpt-5.6-luna"

# Standard pricing per 1M tokens:
# https://developers.openai.com/api/docs/pricing
INPUT_PRICE = 1.00
CACHED_INPUT_PRICE = 0.10
OUTPUT_PRICE = 6.00


class Agent:
    """Call the model, run requested tools, and repeat until it answers."""

    def __init__(
        self,
        instructions: str,
        tools: list[Tool],
        max_iterations: int = 20,
    ):
        load_dotenv()
        self.client = AsyncOpenAI()
        self.instructions = instructions
        self.tools = tools
        self.max_iterations = max_iterations

    async def run(self, message: str) -> dict[str, Any]:
        input_items: list[dict[str, Any]] = [
            {
                "type": "message",
                "role": "developer",
                "content": self.instructions,
            },
            {
                "type": "message",
                "role": "user",
                "content": message,
            },
        ]
        tools_by_name = {tool.name: tool for tool in self.tools}
        total_tool_calls = 0
        input_tokens = 0
        cached_input_tokens = 0
        output_tokens = 0
        models_used: set[str] = set()

        try:
            for iteration in range(1, self.max_iterations + 1):
                print(f"[AGENT] iteration {iteration}/{self.max_iterations}")
                response = await self.client.responses.create(
                    model=MODEL,
                    input=input_items,
                    tools=[tool.definition for tool in self.tools],
                    text={"format": {"type": "json_object"}},
                    max_output_tokens=8_000,
                    store=False,
                )

                models_used.add(response.model)
                if response.usage:
                    input_tokens += response.usage.input_tokens
                    output_tokens += response.usage.output_tokens
                    if response.usage.input_tokens_details:
                        cached_input_tokens += (
                            response.usage.input_tokens_details.cached_tokens or 0
                        )

                output_items = [
                    item.model_dump(exclude_none=True) for item in response.output
                ]
                input_items.extend(output_items)
                tool_calls = [
                    item for item in output_items if item["type"] == "function_call"
                ]
                total_tool_calls += len(tool_calls)

                if not tool_calls:
                    return json.loads(response.output_text)

                tool_outputs = await asyncio.gather(
                    *[
                        self._run_tool_call(tool_call, tools_by_name)
                        for tool_call in tool_calls
                    ]
                )
                input_items.extend(tool_outputs)

            raise RuntimeError("Agent reached its tool-call limit without answering")
        finally:
            uncached_input_tokens = input_tokens - cached_input_tokens
            estimated_cost = (
                uncached_input_tokens * INPUT_PRICE
                + cached_input_tokens * CACHED_INPUT_PRICE
                + output_tokens * OUTPUT_PRICE
            ) / 1_000_000
            print("\n[AGENT] run summary")
            print(f"  model: {', '.join(sorted(models_used)) or MODEL}")
            print(f"  tool calls: {total_tool_calls}")
            print(f"  input tokens: {input_tokens}")
            print(f"  cached input tokens: {cached_input_tokens}")
            print(f"  output tokens: {output_tokens}")
            print(f"  total tokens: {input_tokens + output_tokens}")
            print(f"  estimated cost: ${estimated_cost:.6f}")

    async def _run_tool_call(
        self,
        tool_call: dict[str, Any],
        tools_by_name: dict[str, Tool],
    ) -> dict[str, Any]:
        tool = tools_by_name.get(tool_call["name"])
        if tool is None:
            result: ToolResult = f"Unknown tool: {tool_call['name']}"
        else:
            try:
                result = await tool.run(json.loads(tool_call["arguments"]))
            except Exception as error:
                result = f"Tool error: {error}"

        return {
            "type": "function_call_output",
            "call_id": tool_call["call_id"],
            "output": result,
        }
