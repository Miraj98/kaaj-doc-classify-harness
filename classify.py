import asyncio
import json

from agent import Agent

async def main() -> None:
    agent = Agent(
        instructions="You are a helpful assistant. Always respond with valid JSON",
        tools=[],
    )
    result = await agent.run(
        'Return a short JSON response confirming that the model is reachable'
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
