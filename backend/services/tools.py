from services.db import DBService
from controllers.task import _check_conflict_tasks, _check_free_time_slot
from models.tasks import Task, GroupTask
from utils.timezone import to_myt, now_myt
from typing import Optional
from utils.normalize import calculate_hybrid
from datetime import datetime

db = DBService()

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
    def get_free_time_slots(user_ids, day_bounds, durations) -> dict:
        """
        Get the users free timeslots for creating tasks. 
        user_id, day_bounds, and durations are required. 
        Examples: 
            day_bounds = {
                'start': datetime(2026, 5, 28, 9, 0),
                'end': datetime(2026, 5, 28, 17, 0)
            }
            durations = 30
        """
        if isinstance(user_ids,str):
            user_ids = [user_ids]
        busy_slots = []
        search_date = day_bounds['start'].date()
        for user_id in user_ids:
            tasks = db.get_tasks_by_user_id_and_date(user_id,search_date)
            if tasks:
                for task in tasks:
                    busy_slots.append({
                        "start": task["start_time"],
                        "end": task["end_time"]
                    })
        time_slots = _check_free_time_slot(busy_slots,day_bounds, durations)
        return time_slots 

    @mcp.tool()
    def check_schedule_conflict(user_ids, start_time, end_time) -> dict:
        """
        Check conflict schedule for the users by checking the proposed start_time and end_time. 
        user_ids can be list or string. (List means check among different users conflict schedules while string means check their own conflict schedules.)
        start_time and end_time can be required in the strict format of (YYYY-MM-DD T HH:MM:SS)
        Eg. "2026-05-28T15:30:00"
        """
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)

        conflicts = _check_conflict_tasks(
            user_ids,
            start_dt,
            end_dt
        )
        
        return conflicts

    @mcp.tool()
    def add_task_into_schedule(
        user_id: str,
        title: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        priority: str = "mid",
        location: Optional[str] = None,
        link: Optional[str] = None,
        duration: int = None, 
        status: str = "pending",
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
        - link       : optional link for the task; leave blank if not applicable
        - duration   : estimated time taken for the task usually based on the from start time and end_time 
        - status     : status always under pending which the users accept it or not
        - reminder   : set true if the user asked for a reminder
        """
        start = to_myt(start_time)
        end = to_myt(end_time)
        if not duration:
            duration = int((end - start).total_seconds() / 60)
        user = db.get_user_by_id(user_id)
        if not user:
            return {"status": "error", "detail": f"User {user_id} not found"}

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
            status=status,
            created_at=now_myt(),
            updated_at=now_myt(),
        )
        db.insert_tasks([task])
        return task.to_json()
    
    @mcp.tool()
    def check_update_schedule_task_id(
        user_id:str,
        previous_task: str,
        start_time:str,
        end_time:str
    ) -> dict:
        """
        Check the user's requested task to update to get the task id for update the task. It will return the highest hybrid score task id. 
        """
        keywords = previous_task
        embeddings = [-1*1024]
        vector_results, keyword_results = db.get_tasks_by_user_id_and_title(keywords,embeddings,user_id,start_time,end_time)
        results = calculate_hybrid(vector_results,keyword_results)

        return results

    @mcp.tool()
    def update_task_into_schedule(
        task_id:str,
        user_id: str,
        title: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        priority: str = "mid",
        location: Optional[str] = None,
        link: Optional[str] = None,
        duration: int = None, 
        status: str = "pending",
        reminder: bool = False
    ) -> dict:
        """
        Update Task based on the task_id
        - task_id    : the task_id retrieved from the tools "check_update_schedule_task_id"
        - user_id    : the authenticated user's ID
        - title      : short name of the task (e.g. "Gym session")
        - start_time : ISO 8601 with +08:00 offset (e.g. '2025-05-21T07:00:00+08:00')
        - end_time   : ISO 8601 with +08:00 offset
        - description: optional details/notes about the task (e.g. "I will be meeting with John Doe at the coffee shop")
        - priority   : 'low', 'mid', or 'high'  (default 'mid')
        - location   : optional venue name; leave blank if not applicable
        - link       : optional link for the task; leave blank if not applicable
        - duration   : estimated time taken for the task usually based on the from start time and end_time 
        - status     : status always under pending which the users accept it or not
        - reminder   : set true if the user asked for a reminder
        """
        conflicts = _check_conflict_tasks(user_id,start_time,end_time)
        if conflicts:
            return {
                "success": False,
                "message": "Schedule conflict detected",
                "conflicts": conflicts
            }
        updated_task = Task(
            title=title,
            start_time= start_time,
            end_time=end_time,
            description=description,
            priority=priority,
            location=location,
            link=link,
            duration=duration, 
            status=status,
            reminder=reminder
        )
        success = db.update_task(task_id, updated_task)
        if not success:
            return {
                "success": False,
                "message": "Failed to update task"
            }

        return {
            "success": True,
            "message": "Task updated successfully",
            "task": updated_task.to_json()
        }
    
    @mcp.tool()
    def get_user_memory(user_ids) -> dict:
        """
        Get the user's memory based on the user_id.
        """

        if isinstance(user_ids, str):
            user_ids = [user_ids]

        user_tags = []

        for uid in user_ids:
            user = db.get_user_by_id(uid)

            if user is None:
                continue

            if getattr(user, "tags", None):
                if user.tags not in user_tags:
                    user_tags.append(user.tags)

        return user_tags

    