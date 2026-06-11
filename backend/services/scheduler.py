import asyncio
from datetime import datetime, timedelta, timezone
from services.db import DBService
from services.llm_api import LLM_GEN
import json
from utils.timezone import now_myt,safe_parse_tags

db = DBService()
llm_gen = LLM_GEN()

def flatten_tags(tags):
    result = []
    for t in tags:
        if isinstance(t, list):
            result.extend(t)
        else:
            result.append(t)
    return result

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
                You are a strict tag extraction system.

                You MUST follow these rules exactly:

                1. Read ALL tasks together as ONE dataset.
                2. Do NOT generate tags per task.
                3. Merge all meaning into a single unified tag set.
                4. Output ONLY 3–5 tags total for the entire dataset.
                5. Each tag must be a single word or short phrase (no names, no dates, no numbers).

                STRICT OUTPUT FORMAT:
                - Return ONLY a valid JSON array of strings
                - No explanations
                - No markdown
                - No nested lists
                - No objects

                FORBIDDEN:
                - [["a", "b"], ["c"]]
                - {{"tags": [...]}}
                - per-task grouping

                GOOD EXAMPLE:
                ["work", "meeting", "shopping"]

                TASKS:
                {tasks_memory}
            """
            response = llm_gen.generate_content(prompt)

            tags = flatten_tags(safe_parse_tags(response))

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


async def reminder_check_loop():
    """
    Every 60 seconds, check for tasks starting within the next 10 minutes
    that have reminder=True and haven't been sent yet. Send an email and
    mark reminder_sent=True.
    """
    from services.email_service import send_reminder_email

    POLL_INTERVAL = 60   # seconds
    WINDOW_MINUTES = 10  # remind 10 minutes before

    while True:
        try:
            now = now_myt()
            window_end = now + timedelta(minutes=WINDOW_MINUTES)

            tasks = db.get_upcoming_reminder_tasks(now, window_end)

            for task_doc in tasks:
                task_id = str(task_doc["_id"])
                title = task_doc.get("title", "Untitled Task")
                start_time = task_doc.get("start_time")
                description = task_doc.get("description")
                location = task_doc.get("location")
                users = task_doc.get("users", [])

                # Send to each user associated with this task
                for user_entry in users:
                    user_id = user_entry.get("user_id")
                    if not user_id:
                        continue

                    user = db.get_user_by_id(user_id)
                    if not user or not user.email:
                        continue

                    success = send_reminder_email(
                        to_email=user.email,
                        task_title=title,
                        start_time=start_time,
                        description=description,
                        location=location,
                    )

                    if success:
                        print(f"📧 Reminder sent to {user.email} for '{title}'")

                # Mark as sent regardless (avoid retry-spamming on partial failure)
                db.mark_reminder_sent(task_id)

        except Exception as e:
            print(f"Error in reminder check loop: {e}")

        await asyncio.sleep(POLL_INTERVAL)
