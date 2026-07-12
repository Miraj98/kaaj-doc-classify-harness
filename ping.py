import asyncio
import json

from agent import Agent
from tools import Tool


async def get_weather(arguments: dict) -> str:
    return "The weather is sunny and 72°F."


async def main() -> None:
    weather_tool = Tool(
        definition={
            "type": "function",
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city to check.",
                    }
                },
                "required": ["city"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        handler=get_weather,
    )
    agent = Agent(
        instructions=(
            "You are a connectivity test. Use get_weather to answer the question, "
            "then return a short JSON response."
        ),
        tools=[weather_tool],
    )
    response = await agent.run("What is the weather in New York?")
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
