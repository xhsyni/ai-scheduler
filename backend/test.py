from services.scheduler import update_all_users_memory
import asyncio

print(asyncio.run(update_all_users_memory()))