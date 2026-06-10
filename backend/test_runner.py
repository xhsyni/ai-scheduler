import asyncio
from services.agent_runner import run_agent

async def main():
    res = await run_agent(
        user_id="6a26ebd93512c2f7136bb51f",
        user_name="1234",
        conversation_id="test_conv_001",
        message="Create a meeting tomorrow at 6pm for 1 hour"
    )
    print("FINAL:", res)

asyncio.run(main())