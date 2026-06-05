import asyncio
from datetime import datetime, timedelta, timezone
from services.db import DBService
from services.llm_api import LLM_GEN
import json
from utils.timezone import now_myt,safe_parse_tags

db = DBService()
llm_gen = LLM_GEN()
async def update_all_users_memory():
    try:
        users = db.db[db.user_collection].find({})
        now = now_myt()
        seven_days_ago = now - timedelta(days=7)

        for user in users:
            user_id = str(user["_id"])
            existing_tags = set(user.get("tags", []))

            # fetch all relevant tasks once per user
            tasks = list(db.db[db.task_collection].find({
                "users.user_id": user_id,
                "created_at": {
                    "$gte": seven_days_ago,
                    "$lte": now
                }
            }))
            tasks_memory = []
            for task in tasks:
                tasks_memory.append({
                    "title": task.get("title", ""),
                    "description": task.get("description", "")
                })
            print(tasks_memory)
            if not tasks:
                continue

            aggregated_tags = set()

            prompt = f"""
                You are a tag generator for tasks.

                Generate 3–5 relevant tags (more likely adjective, verbs, or noun) that usable for memory based on the title and description. 
                This generated tags will be stored as memory in the database and used to recommend similar tasks to the user.
                Strictly do not add any names, locations, terms, dates, times, or numbers.
                Strictly no "[[" or "]]" or "[" or "]" in the output.
                
                Return ONLY one valid JSON list of strings.

                Example of output (single list):
                ["work", "urgent", "meeting"]

                Tasks:
                {tasks_memory}
            """
            response = llm_gen.generate_content(prompt)
            tags = safe_parse_tags(response)

            print(f"Tags for user {user_id}: {tags}")
            aggregated_tags.update(str(t).strip().lower() for t in tags)
            final_tags = existing_tags.union(aggregated_tags)
            final_tags = set(final_tags)
            
            if final_tags != existing_tags:
                db.db[db.user_collection].update_one(
                    {"_id": user["_id"]},
                    {"$set": {"tags": list(final_tags)}}
                )

    except Exception as e:
        print(f"Error in weekly memory background job: {e}")

async def weekly_memory_updater_loop():
    WEEK_SECONDS = 7 * 24 * 60 * 60 
    while True:
        await update_all_users_memory()
        await asyncio.sleep(WEEK_SECONDS)
