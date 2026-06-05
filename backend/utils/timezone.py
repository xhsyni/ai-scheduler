from zoneinfo import ZoneInfo
from datetime import datetime
import json
import re

MY_TZ = ZoneInfo("Asia/Kuala_Lumpur")

def now_myt() -> datetime:
    return datetime.now(MY_TZ)

def to_myt(dt: datetime | str | None) -> datetime | None:
    if dt is None:
        return None
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=MY_TZ)
    return dt.astimezone(MY_TZ)

def to_utc(dt: datetime | str | None) -> datetime | None:
    if dt is None:
        return None
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=MY_TZ).astimezone(ZoneInfo("UTC"))
    return dt.astimezone(ZoneInfo("UTC"))

def safe_parse_tags(response):
    if response is None:
        return []

    # if response is object (not string)
    if not isinstance(response, str):
        return response if isinstance(response, list) else []

    text = response.strip()

    # remove ```json blocks if present
    text = re.sub(r"```json|```", "", text).strip()

    # extract first JSON array
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []

    try:
        return json.loads(match.group(0))
    except Exception:
        return []