from datetime import datetime, timedelta
import json
from typing import Optional
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from models.tasks import GroupTask, Task
from services.db import DBService
from utils.timezone import now_myt, to_myt

db = DBService()

USER_AGENT = "ai-scheduler/1.0"


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return to_myt(parsed)

def _serialize_tasks(tasks: list[Task]) -> list[dict]:
    return [task.to_json() for task in tasks]


def _find_conflicts(user_id: str, start_time: datetime, end_time: datetime) -> list[Task]:
    conflicts = []
    for task in db.get_tasks_by_user_id(user_id):
        if not task.start_time or not task.end_time:
            continue
        if start_time < to_myt(task.end_time) and end_time > to_myt(task.start_time):
            conflicts.append(task)
    return conflicts


def _check_schedule_conflict(user_id: str, start_time: str, end_time: str) -> dict:
    start = _parse_datetime(start_time)
    end = _parse_datetime(end_time)
    conflicts = _find_conflicts(user_id, start, end)
    return {
        "has_conflict": len(conflicts) > 0,
        "conflicts": _serialize_tasks(conflicts),
    }

def _create_schedule_task(
    user_id: str,
    title: str,
    start_time: str,
    end_time: str,
    description: Optional[str] = None,
    priority: str = "mid",
    location: Optional[str] = None,
    reminder: bool = False,
) -> dict:
    user = db.get_user_by_id(user_id)
    if not user:
        return {"status": "error", "detail": f"User {user_id} not found"}

    start = _parse_datetime(start_time)
    end = _parse_datetime(end_time)
    duration = int((end - start).total_seconds() / 60)
    task = Task(
        users=[GroupTask(user_id=user.id, name=user.name, role="owner")],
        title=title,
        description=description,
        priority=priority,
        location=location,
        start_time=start,
        end_time=end,
        duration=duration,
        reminder=reminder,
        status="scheduled",
        updated_at=now_myt(),
    )
    db.insert_tasks([task])
    return {
        "status": "scheduled",
        "task": task.to_json(),
    }


def _get_user_memory(user_id: str) -> dict:
    user = db.get_user_by_id(user_id)
    if not user:
        return {"status": "error", "detail": f"User {user_id} not found"}
    return {
        "user_id": user.id,
        "name": user.name,
        "tags": user.tags
    }


def _get_json(url: str) -> dict | list:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _geocode_location(location: str) -> dict:
    query = urlencode({"q": location, "format": "json", "limit": 1})
    results = _get_json(f"https://nominatim.openstreetmap.org/search?{query}")
    if not results:
        raise ValueError(f"Could not find coordinates for '{location}'")

    result = results[0]
    return {
        "name": result.get("display_name"),
        "lat": float(result["lat"]),
        "lon": float(result["lon"]),
    }


def _estimate_travel_time(origin: str, destination: str, transport_mode: str = "driving") -> dict:
    osrm_profiles = {
        "driving": "driving",
        "walking": "foot",
        "cycling": "bike",
    }
    profile = osrm_profiles.get(transport_mode)
    if not profile:
        return {
            "status": "error",
            "detail": f"Unsupported transport_mode '{transport_mode}'. Use driving, walking, or cycling.",
        }

    try:
        origin_point = _geocode_location(origin)
        destination_point = _geocode_location(destination)
        coordinates = (
            f"{origin_point['lon']},{origin_point['lat']};"
            f"{destination_point['lon']},{destination_point['lat']}"
        )
        route_url = (
            f"https://router.project-osrm.org/route/v1/{profile}/{quote(coordinates, safe=';,')}"
            "?overview=false&alternatives=false&steps=false"
        )
        route_data = _get_json(route_url)
        routes = route_data.get("routes", [])
        if not routes:
            return {
                "status": "error",
                "detail": f"No route found from '{origin}' to '{destination}'",
                "origin": origin,
                "destination": destination,
                "transport_mode": transport_mode,
            }

        route = routes[0]
        duration_minutes = round(route["duration"] / 60)
        distance_km = round(route["distance"] / 1000, 2)
    except Exception as error:
        return {
            "status": "error",
            "detail": str(error),
            "origin": origin,
            "destination": destination,
            "transport_mode": transport_mode,
        }

    return {
        "status": "ok",
        "origin": origin,
        "destination": destination,
        "transport_mode": transport_mode,
        "estimated_minutes": duration_minutes,
        "distance_km": distance_km,
        "provider": "OpenStreetMap Nominatim + OSRM",
        "resolved_origin": origin_point,
        "resolved_destination": destination_point,
    }


def _normalize_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _default_collaboration_title(tags: list[str], objective: Optional[str]) -> str:
    if objective:
        return objective
    if "study" in [tag.lower() for tag in tags]:
        return "Group study session"
    return "Collaboration session"


def _recommend_collaboration_task(
    user_id: str,
    participant_count: int,
    objective: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
) -> dict:
    memory = _get_user_memory(user_id)
    tags = memory.get("tags", []) if memory.get("status") != "error" else []
    objective = _normalize_optional_text(objective)
    description = _normalize_optional_text(description)
    title = _default_collaboration_title(tags, objective)

    return {
        "title": title,
        "description": description,
        "priority": "mid",
        "recommended_duration_minutes": 60 if participant_count <= 3 else 90,
        "location": location,
        "reasoning": "Recommended from user memory, group size, and collaboration context.",
    }


def _add_task_into_schedule(
    user_id: str,
    title: str,
    start_time: str,
    end_time: str,
    description: Optional[str] = None,
    priority: str = "mid",
    location: Optional[str] = None,
    reminder: bool = False,
) -> dict:
    conflict_result = _check_schedule_conflict(user_id, start_time, end_time)
    if conflict_result["has_conflict"]:
        return {
            "case": "add_tasks_into_schedule",
            "status": "conflict",
            "reasoning": "The requested time overlaps existing tasks.",
            "conflicts": conflict_result["conflicts"],
        }

    task_result = _create_schedule_task(
        user_id=user_id,
        title=title,
        start_time=start_time,
        end_time=end_time,
        description=description,
        priority=priority,
        location=location,
        reminder=reminder,
    )
    return {
        "case": "add_tasks_into_schedule",
        "agent_path": ["Calendar Scheduler Agent"],
        **task_result,
    }


def _recommend_tasks_for_collaboration(
    user_id: str,
    participant_count: int,
    start_time: str,
    origin: str,
    destination: str,
    objective: Optional[str] = None,
    description: Optional[str] = None,
    transport_mode: str = "driving",
) -> dict:
    memory = _get_user_memory(user_id)
    travel = _estimate_travel_time(origin, destination, transport_mode)
    if travel.get("status") == "error":
        return {
            "case": "recommend_tasks_for_collaboration",
            "status": "error",
            "agent_path": ["Memory Agent", "Travel Agent"],
            "memory": memory,
            "travel": travel,
        }
    recommendation = _recommend_collaboration_task(
        user_id=user_id,
        participant_count=participant_count,
        objective=_normalize_optional_text(objective),
        description=_normalize_optional_text(description),
        location=destination,
    )

    start = _parse_datetime(start_time) + timedelta(minutes=travel["estimated_minutes"])
    end = start + timedelta(minutes=recommendation["recommended_duration_minutes"])
    schedule = _add_task_into_schedule(
        user_id=user_id,
        title=recommendation["title"],
        start_time=start.isoformat(),
        end_time=end.isoformat(),
        description=recommendation["description"],
        priority=recommendation["priority"],
        location=destination,
        reminder=True,
    )
    return {
        "case": "recommend_tasks_for_collaboration",
        "agent_path": [
            "Travel Agent",
            "Recommendation Agent",
            "Calendar Scheduler Agent",
        ],
        "memory": memory,
        "travel": travel,
        "recommendation": recommendation,
        "schedule": schedule,
    }


# ── MCP tool registration ─────────────────────────────────────────────────────

# 1. get_current_datetime
# 	- ()
# 2. get_user_tasks_by_date
# 	- (user_id, date) 
# 3. get_free_time_slots
# 	-  (user_id, date) 
# 4. check_schedule_conflict
# 	-  (user_id, start time, end time) 
# 5. add_task_into_schedule
# 	- (user_id, title, start_time, end_time, description, priority, location, link, duration, status, reminder) 
# 6. update_task_in_schedule
# 	- (user_id, title, start_time, end_time, description, priority, location, link, duration, status, reminder) 
# 7. get_user_memory 
# 	- [user_ids]
# 8. location_finder
# 	- (origin, destination, transport mode) 

def register_mcp_tools(mcp):

    @mcp.tool()
    def get_current_datetime() -> dict:
        """
        Get the current date and time in Asia/Kuala_Lumpur (UTC+8).
        Always call this first when the user mentions relative times like
        'tomorrow', 'next Monday', 'in 2 hours', etc.
        """
        now = now_myt()
        return {
            "iso": now.isoformat(),
            "date": now.date().isoformat(),
            "time": now.strftime("%H:%M"),
            "weekday": now.strftime("%A"),
            "timezone": "Asia/Kuala_Lumpur (UTC+8)",
        }

    @mcp.tool()
    def get_user_tasks_by_date(user_id: str, date: str) -> dict:
        """
        List all scheduled tasks for a user on a specific date.
        Use this to show the user their upcoming events or to check what
        is already on their calendar before scheduling something new.
        """
        tasks = db.get_tasks_by_user_id_and_date(user_id, date)
        return {
            "tasks": _serialize_tasks(tasks),
            "date": date,
            "user_id": user_id,
        }

    @mcp.tool()
    def get_free_time_slots(user_id: str, date: str) -> dict:
        """
        Get the user's free time slots for a specific date.
        The date must be in ISO format (e.g. '2025-05-21').
        Use this to find suitable times for scheduling new tasks.
        """

        tasks = db.get_tasks_by_user_id_and_date(user_id, date)

        # Keep only tasks with valid start/end times
        tasks_ = [
            task for task in tasks
            if task.start_time and task.end_time
        ]

        # Sort tasks by start time
        tasks_.sort(key=lambda x: x.start_time)

        # Define day boundaries
        target_date = datetime.fromisoformat(date).date()
        day_start = datetime.combine(target_date, time.min)
        day_end = datetime.combine(target_date, time.max)

        free_time_slots = []

        current_start = day_start

        for task in tasks_:
            task_start = task.start_time
            task_end = task.end_time

            # Convert string datetime if necessary
            if isinstance(task_start, str):
                task_start = datetime.fromisoformat(task_start)

            if isinstance(task_end, str):
                task_end = datetime.fromisoformat(task_end)

            # Free slot before this task
            if task_start > current_start:
                free_time_slots.append({
                    "start_time": current_start.isoformat(),
                    "end_time": task_start.isoformat(),
                })

            # Move current pointer forward
            current_start = max(current_start, task_end)

        # Free slot after last task
        if current_start < day_end:
            free_time_slots.append({
                "start_time": current_start.isoformat(),
                "end_time": day_end.isoformat(),
            })

        return {
            "free_time_slots": free_time_slots,
            "date": date,
            "user_id": user_id,
        }

    @mcp.tool()
    def check_schedule_conflict(user_id: str, start_time: str, end_time: str) -> dict:
        """
        Check whether a proposed time range overlaps any existing task for this user.
        start_time and end_time must be ISO 8601 strings with +08:00 offset,
        e.g. '2025-05-21T09:00:00+08:00'.
        Returns has_conflict (bool) and a list of conflicting tasks. 
        """
        return _check_schedule_conflict(user_id, start_time, end_time)

    @mcp.tool()
    def add_task_into_schedule(
        user_id: str,
        title: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        priority: str = "mid",
        location: Optional[str] = None,
        reminder: bool = False,
    ) -> dict:
        """
        Add a task to the user's schedule after automatically checking for conflicts.
        - user_id    : the authenticated user's ID
        - title      : short name of the task (e.g. "Gym session")
        - start_time : ISO 8601 with +08:00 offset (e.g. '2025-05-21T07:00:00+08:00')
        - end_time   : ISO 8601 with +08:00 offset
        - description: optional details/notes about the task (e.g. "I will be meeting with John Doe at the coffee shop")
        - priority   : 'low', 'mid', or 'high'  (default 'mid')
        - location   : optional venue name; leave blank if not applicable
        - reminder   : set true if the user asked for a reminder

        Returns status='scheduled' on success, or status='conflict' with details
        of the overlapping tasks so the agent can suggest an alternative time.
        """
        return _add_task_into_schedule(
            user_id=user_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description or None,
            priority=priority or "mid",
            location=location or None,
            reminder=reminder,
        )

    def update_task_in_schedule(
        task_id: str,
        title: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        location: Optional[str] = None,
        reminder: Optional[bool] = None,
    ) -> dict:
        """
        Update an existing task in the schedule. Only provide the fields that need to be changed.
        - task_id    : the ID of the task to update
        - title      : new title for the task (e.g. "Gym session with Alice")
        - start_time : new start time in ISO 8601 with +08:00 offset
        - end_time   : new end time in ISO 8601 with +08:00 offset
        - description: new details/notes about the task
        - priority   : 'low', 'mid', or 'high'
        - location   : new venue name; leave blank if not applicable
        - reminder   : set true if the user asked for a reminder, false to remove reminder

        Returns status='updated' on success, or status='error' if the task is not found
        or if the new time range conflicts with another existing task.
        """
        # For simplicity, this example does not implement the update logic.
        return {
            "status": "error",
            "detail": "Update functionality is not implemented in this example.",
            "task_id": task_id,
        }

    @mcp.tool()
    def get_user_memory(user_id: str) -> dict:
        """
        Retrieve the user's stored preferences and activity tags.
        Useful for personalising recommendations (e.g. study, fitness, social).
        """
        return _get_user_memory(user_id)

    @mcp.tool()
    def estimate_travel_time(
        origin: str,
        destination: str,
        transport_mode: str = "driving",
    ) -> dict:
        """
        Estimate travel time and distance between two locations using OpenStreetMap.
        - origin         : starting place name or address (e.g. 'Bangsar, Kuala Lumpur')
        - destination    : destination place name or address (e.g. 'KLCC, Kuala Lumpur')
        - transport_mode : 'driving' (default), 'walking', or 'cycling'

        Returns estimated_minutes and distance_km on success, or status='error'
        with a detail message if a location cannot be found.
        """
        return _estimate_travel_time(origin, destination, transport_mode or "driving")

    @mcp.tool()
    def recommend_collaboration_task(
        user_id: str,
        participant_count: int,
        objective: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> dict:
        """
        Recommend a collaboration task based on the user's preferences and group size.
        - user_id          : the authenticated user's ID
        - participant_count: total number of participants including the user
        - objective        : short event title from the user (e.g. "Project sync with team")
        - description      : optional extra notes for the calendar entry; omit if none
        - location         : optional venue for the session
        """
        return _recommend_collaboration_task(
            user_id,
            participant_count,
            _normalize_optional_text(objective),
            _normalize_optional_text(description),
            location or None,
        )

    @mcp.tool()
    def recommend_tasks_for_collaboration(
        user_id: str,
        participant_count: int,
        start_time: str,
        origin: str,
        destination: str,
        objective: Optional[str] = None,
        description: Optional[str] = None,
        transport_mode: str = "driving",
    ) -> dict:
        """
        Full collaboration workflow: estimates travel time, recommends a task,
        then automatically schedules it on the calendar.
        - user_id          : the authenticated user's ID
        - participant_count: total number of participants including the user
        - start_time       : when the user plans to leave (ISO 8601 with +08:00)
        - origin           : the user's starting location
        - destination      : where the collaboration session will take place
        - objective        : short event title from the user (e.g. "Basketball with friends")
        - description      : optional extra notes for the calendar entry; omit if none
        - transport_mode   : 'driving' (default), 'walking', or 'cycling'
        """
        return _recommend_tasks_for_collaboration(
            user_id=user_id,
            participant_count=participant_count,
            start_time=start_time,
            origin=origin,
            destination=destination,
            objective=_normalize_optional_text(objective),
            description=_normalize_optional_text(description),
            transport_mode=transport_mode,
        )
