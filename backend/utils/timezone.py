from zoneinfo import ZoneInfo
from datetime import datetime

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
