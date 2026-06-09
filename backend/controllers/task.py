from models.users import User
from services.db import DBService
from fastapi import HTTPException, status
from models.tasks import Task, GroupTask
from utils.timezone import to_myt,now_myt
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from services.embeddings import Similarity
import json

db = DBService()
similarity = Similarity()

def check_valid_task(task:Task):
    if task.id:
        task_in_db = db.get_task_by_id(task.id)
        if not task_in_db:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task.id} not found")
    if task.start_time is None or task.end_time is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start time and end time are required")
    if task.start_time > task.end_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start time must be before end time")
    return True
    
def _check_conflict_tasks(
    user_ids: str | list[str],
    new_start_time,
    new_end_time,
    task_id: Optional[str] = None
):
    if isinstance(user_ids, str):
        user_ids = [user_ids]
    
    if new_start_time.tzinfo is None:
        new_start_time = new_start_time.replace(tzinfo=timezone.utc)

    if new_end_time.tzinfo is None:
        new_end_time = new_end_time.replace(tzinfo=timezone.utc)

    local_start = to_myt(new_start_time)
    day_start = datetime(local_start.year, local_start.month, local_start.day, 0, 0, 0, tzinfo=local_start.tzinfo)
    day_end = day_start + timedelta(days=1)

    conflicts = {}

    for user_id in user_ids:
        tasks = db.get_tasks_by_user_id_and_date(
            user_id,
            day_start,
            day_end
        )

        user_conflicts = []

        for task in tasks:
            if str(task.id) == str(task_id):
                continue
            task_start = task.start_time
            task_end = task.end_time

            if task_start.tzinfo is None:
                task_start = task_start.replace(tzinfo=timezone.utc)

            if task_end.tzinfo is None:
                task_end = task_end.replace(tzinfo=timezone.utc)

            if new_start_time < task_end and new_end_time > task_start:
                task_data = task.to_json()
                task_data.pop("embeddings", None)
                user_conflicts.append(task_data)

        conflicts[user_id] = user_conflicts
    print(f"Conflict check for user_ids={user_ids}, new_start_time={to_myt(new_start_time)}, new_end_time={to_myt(new_end_time).isoformat()} found conflicts: {conflicts}")
    return conflicts

def _check_free_time_slot(
    all_busy_slots: List[Dict[str,datetime]], 
    working_bounds: Dict[str,datetime], 
    duration_minutes: int
) -> List[Dict[str,datetime]]:
    # Convert all datetimes to MYT to prevent comparison errors
    working_bounds = {
        'start': to_myt(working_bounds['start']),
        'end': to_myt(working_bounds['end'])
    }
    
    normalized_busy = []
    for busy in all_busy_slots:
        normalized_busy.append({
            'start': to_myt(busy['start']),
            'end': to_myt(busy['end'])
        })
        
    sorted_busy = sorted(normalized_busy, key=lambda x: x['start'])
    
    merged_busy= []
    for current in sorted_busy:
        if not merged_busy:
            merged_busy.append(current.copy())
            continue
            
        last_merged = merged_busy[-1]
        
        if current['start'] <= last_merged['end']:
            if current['end'] > last_merged['end']:
                last_merged['end'] = current['end']
        else:
            merged_busy.append(current.copy())
            
    free_slots = []
    current_pointer = working_bounds['start']
    min_duration = timedelta(minutes=duration_minutes)
    
    for busy in merged_busy:
        if busy['start'] - current_pointer >= min_duration:
            free_slots.append({'start': current_pointer, 'end': busy['start']})
        if busy['end'] > current_pointer:
            current_pointer = busy['end']
            
    if working_bounds['end'] - current_pointer >= min_duration:
        free_slots.append({'start': current_pointer, 'end': working_bounds['end']})
        
    return free_slots

# Task Function
async def create_task(task: Task, current_user: User):
    if task.start_time and task.end_time:
        if not check_valid_task(task):
            return JSONResponse({"status_code":status.HTTP_400_BAD_REQUEST, "detail": f"Invalid task"})
        conflict_tasks = _check_conflict_tasks(current_user.id, task.start_time, task.end_time)
        total_conflicts = sum(len(v) for v in conflict_tasks.values())

        # if total_conflicts > 0:
        #     return JSONResponse(
        #         content=json.loads(
        #             json.dumps({
        #                 "conflict_data": conflict_tasks,
        #                 "status_code": status.HTTP_400_BAD_REQUEST,
        #                 "detail": "Time conflict"
        #             }, default=str)
        #         )
        #     )
        duration = (task.end_time - task.start_time).total_seconds() / 60
        task = task.model_copy(update={"duration": duration,"updated_at":now_myt()})
    else:
        task = task.model_copy(update={"updated_at":now_myt()})
    desc = task.description or ""
    embeddings_arr = similarity.encode(task.title + "\n" + desc)
    task.embeddings = embeddings_arr.tolist() if hasattr(embeddings_arr, "tolist") else list(embeddings_arr)
    task = task.model_copy(update={"users": [GroupTask(user_id=current_user.id, name=current_user.name, role="owner")]})
    inserted_ids = db.insert_tasks([task])
    return {
        "status": status.HTTP_200_OK,
        "message": "Task created successfully",
        "task_id": inserted_ids[0] if inserted_ids else None
    }

async def get_tasks_by_date(current_user: User,start_date: str,end_date: Optional[str] = None):
    if isinstance(start_date, str):
        start_date_iso = datetime.fromisoformat(start_date)
    if isinstance(end_date, str):        
        end_date_iso = datetime.fromisoformat(end_date)
    
    if end_date_iso - start_date_iso > timedelta(days=32):
        return JSONResponse({"status_code":status.HTTP_400_BAD_REQUEST, "detail": f"The filter date cannot be more than 32 days."})
    tasks = db.get_tasks_by_user_id_and_date(current_user.id,start_date,end_date)

    grouped: dict[str, list] = {}
    for task in tasks:
        date_key = task.start_time.date()
        task_data = task.to_json()
        task_data.pop("embeddings", None)
        grouped.setdefault(date_key, []).append(task_data)

    return {
        "status": status.HTTP_200_OK,
        "tasks": grouped
    }

async def update_task(task: Task, task_id: str, current_user: User):
    task = task.model_copy(update={"id": task_id})
    if task.start_time and task.end_time:
        if not check_valid_task(task):
            return JSONResponse({"status_code":status.HTTP_400_BAD_REQUEST, "detail": f"Invalid task"})
        
        existing_task = db.get_task_by_id(task_id)
        if not existing_task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found")

        user_ids = [u.user_id for u in existing_task.users]
        if current_user.id not in user_ids:
            user_ids.append(current_user.id)

        conflict_tasks = _check_conflict_tasks(user_ids, task.start_time, task.end_time, task_id=task_id)
        total_conflicts = sum(len(v) for v in conflict_tasks.values())

        # if total_conflicts > 0:
        #     return JSONResponse(
        #         content=json.loads(
        #             json.dumps({
        #                 "conflict_data": conflict_tasks,
        #                 "status_code": status.HTTP_400_BAD_REQUEST,
        #                 "detail": "Time conflict"
        #             }, default=str)
        #         )
        #     )
        duration = (task.end_time - task.start_time).total_seconds() / 60
        task = task.model_copy(update={"duration": duration,"updated_at":now_myt()})
    else:
        task = task.model_copy(update={"updated_at":now_myt()})
    desc = task.description or ""
    embeddings_arr = similarity.encode(task.title + "\n" + desc)
    task.embeddings = embeddings_arr.tolist() if hasattr(embeddings_arr, "tolist") else list(embeddings_arr)
    db.update_task(task_id, task)
    return {
        "status": status.HTTP_200_OK,
        "message": "Task updated successfully"
    }

async def add_user_to_task(task_id: str, user_id: str, email: str, role: str, current_user: User):
    task = db.get_task_by_id(task_id)
    if not task:
        return JSONResponse({"status_code":status.HTTP_404_NOT_FOUND, "detail": f"Task {task_id} not found"})
    if user_id:
        target_user = db.get_user_by_id(user_id)
    else:
        target_user = db.get_user_by_email(email)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User not found")

    if db.user_exists_in_task(task_id, target_user.id):
        return JSONResponse({"status_code":status.HTTP_400_BAD_REQUEST, "detail": f"User {target_user.id} already exists in task {task_id}"})

    # Check conflicts for the target collaborator
    if task.start_time and task.end_time:
        conflict_tasks = _check_conflict_tasks(target_user.id, task.start_time, task.end_time, task_id=task_id)
        total_conflicts = sum(len(v) for v in conflict_tasks.values())
        if total_conflicts > 0:
            return JSONResponse({
                "status_code": status.HTTP_400_BAD_REQUEST,
                "detail": f"Time conflict: {target_user.name} is busy during this time slot."
            })

    db.add_user_to_task(task_id, GroupTask(user_id=target_user.id,name=target_user.name, role=role, updated_by=current_user.id))
    return {
        "status": status.HTTP_200_OK,
        "message": "User added to task successfully"
    }

async def update_user_role(task_id: str, user_id: str, new_role: str,current_user: User):
    task = db.get_task_by_id(task_id)
    user = [user for user in task.users if user.user_id == current_user.id]
    if new_role == "owner":
        return JSONResponse({"status_code":status.HTTP_400_BAD_REQUEST, "detail": f"Not more than 1 owner in task"})
    if user[0].role != "owner" or user[0].role != "admin":
        return JSONResponse({"status_code":status.HTTP_403_FORBIDDEN, "detail": f"You do not have permission to update user role in this task"})
    updated = db.update_user_role_in_task(task_id, user_id, new_role)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found in task {task_id}"
        )
    return {
        "status": status.HTTP_200_OK,
        "message": f"Role updated to '{new_role}' for user {user_id}"
    }

async def delete_user_from_task(task_id: str, user_id: str, current_user: User):
    if current_user.id == user_id:
        return JSONResponse({"status_code":status.HTTP_400_BAD_REQUEST, "detail": f"You cannot delete yourself from the task"})
    task = db.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    if current_user.id not in [user.user_id for user in task.users]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to delete user from this task"
        )
    user = [user for user in task.users if user.user_id == user_id]
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found in task {task_id}"
        )
    current_user_in_task = next((u for u in task.users if u.user_id == current_user.id), None)
    if not current_user_in_task or current_user_in_task.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete users from this task"
        )
    if user[0].role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The owner cannot be removed from the task"
        )
    updated = db.delete_user_from_task(task_id, user_id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found in task {task_id}"
        )
    return {
        "status": status.HTTP_200_OK,
        "message": f"User {user[0].name} removed from task {task_id}"
    }

async def delete_task(task_id: str, current_user: User):
    task = db.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    current_user_in_task = next((u for u in task.users if u.user_id == current_user.id), None)
    if not current_user_in_task or current_user_in_task.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this task"
        )
    deleted = db.delete_task(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task"
        )
    return {
        "status": status.HTTP_200_OK,
        "message": "Task deleted successfully"
    }

async def get_groups_overlay(current_user: User, week_start_str: str):
    try:
        week_start = datetime.strptime(week_start_str, "%Y-%m-%d")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid week_start format. Use YYYY-MM-DD")
    
    all_users = db.get_all_users()
    squad_users = []
    for u in all_users:
        if u.id == current_user.id:
            squad_users.insert(0, u)
        elif len(squad_users) < 5:
            squad_users.append(u)
            
    if current_user.id not in [u.id for u in squad_users]:
        squad_users.insert(0, current_user)
        if len(squad_users) > 5:
            squad_users = squad_users[:5]

    colors = ["bg-gradient-primary", "bg-amber-500", "bg-emerald-500", "bg-accent", "bg-indigo-400"]
    members_data = []
    for idx, u in enumerate(squad_users):
        name_label = "You" if u.id == current_user.id else (u.name or u.email.split("@")[0])
        members_data.append({
            "user_id": u.id,
            "name": name_label,
            "color": colors[idx % len(colors)]
        })

    slots_hours = [9, 11, 13, 15, 17, 19, 21]
    week_end = week_start + timedelta(days=7)
    overlay = [[2 for _ in range(7)] for _ in range(7)]

    squad_tasks_by_user = {}
    for u in squad_users:
        tasks = db.get_tasks_by_user_id_and_date(u.id, week_start, week_end)
        squad_tasks_by_user[u.id] = tasks

    slot_scores = []
    for si, start_hour in enumerate(slots_hours):
        for di in range(7):
            day_date = week_start + timedelta(days=di)
            slot_start = datetime(day_date.year, day_date.month, day_date.day, start_hour, 0, 0)
            slot_start = slot_start.replace(tzinfo=timezone(timedelta(hours=8)))
            slot_end = slot_start + timedelta(hours=2)

            free_count = 0
            busy_count = 0
            for u in squad_users:
                user_tasks = squad_tasks_by_user.get(u.id, [])
                has_overlap = False
                for task in user_tasks:
                    if task.start_time and task.end_time:
                        t_start = task.start_time
                        t_end = task.end_time
                        if t_start.tzinfo is None:
                            t_start = t_start.replace(tzinfo=timezone.utc)
                        if t_end.tzinfo is None:
                            t_end = t_end.replace(tzinfo=timezone.utc)
                        
                        if slot_start < t_end and slot_end > t_start:
                            has_overlap = True
                            break
                if has_overlap:
                    busy_count += 1
                else:
                    free_count += 1

            if busy_count == 0:
                val = 2
            elif free_count == 0:
                val = 0
            else:
                val = 1
            overlay[si][di] = val

            slot_scores.append({
                "free_count": free_count,
                "day_index": di,
                "slot_index": si,
                "start": slot_start,
                "end": slot_end
            })

    sorted_slots = sorted(slot_scores, key=lambda x: (-x["free_count"], x["day_index"], x["slot_index"]))
    top_3 = sorted_slots[:3]

    days_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    slots_labels = ["9am – 11am", "11am – 1pm", "1pm – 3pm", "3pm – 5pm", "5pm – 7pm", "7pm – 9pm", "9pm – 11pm"]

    optimal_suggestions = []
    for item in top_3:
        optimal_suggestions.append({
            "day_name": days_names[item["day_index"]],
            "slot_label": slots_labels[item["slot_index"]],
            "free_count": item["free_count"],
            "total_count": len(squad_users),
            "start_iso": item["start"].isoformat(),
            "end_iso": item["end"].isoformat(),
            "day_index": item["day_index"],
            "slot_index": item["slot_index"]
        })

    if not optimal_suggestions:
        optimal_suggestions = [{
            "day_name": "Thursday",
            "slot_label": "3pm – 5pm",
            "free_count": len(squad_users),
            "total_count": len(squad_users),
            "start_iso": (week_start + timedelta(days=3, hours=15)).replace(tzinfo=timezone(timedelta(hours=8))).isoformat(),
            "end_iso": (week_start + timedelta(days=3, hours=17)).replace(tzinfo=timezone(timedelta(hours=8))).isoformat(),
            "day_index": 3,
            "slot_index": 3
        }]

    return {
        "members": members_data,
        "overlay": overlay,
        "suggestions": optimal_suggestions
    }

async def lock_in_group_task(
    current_user: User,
    title: str,
    start_time: str,
    end_time: str,
    location: Optional[str] = None
):
    try:
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid start_time or end_time format. Use ISO 8601 offset-aware strings.")

    all_users = db.get_all_users()
    squad_users = []
    for u in all_users:
        if u.id == current_user.id:
            squad_users.insert(0, u)
        elif len(squad_users) < 5:
            squad_users.append(u)
            
    if current_user.id not in [u.id for u in squad_users]:
        squad_users.insert(0, current_user)
        if len(squad_users) > 5:
            squad_users = squad_users[:5]

    users_list = []
    for u in squad_users:
        role = "owner" if u.id == current_user.id else "editor"
        users_list.append(GroupTask(
            user_id=u.id,
            name=u.name or u.email.split("@")[0],
            role=role,
            updated_by=current_user.id
        ))

    duration = (end_dt - start_dt).total_seconds() / 60
    
    desc = "Shared squad collaboration task locked in from Groups panel."
    embeddings_arr = similarity.encode(title + "\n" + desc)
    embeddings_list = embeddings_arr.tolist() if hasattr(embeddings_arr, "tolist") else list(embeddings_arr)

    task = Task(
        title=title,
        description=desc,
        priority="mid",
        category="Work",
        location=location or "Squad Meeting Point",
        start_time=start_dt,
        end_time=end_dt,
        duration=int(duration),
        reminder=True,
        status="pending",
        embeddings=embeddings_list,
        users=users_list
    )

    inserted_ids = db.insert_tasks([task])
    return {
        "status": status.HTTP_200_OK,
        "message": "Squad collaboration block locked in successfully!",
        "task_id": inserted_ids[0] if inserted_ids else None
    }

async def check_task_conflict(start_time: str, end_time: str, task_id: Optional[str], current_user: User):
    try:
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid datetime format")
    
    user_ids = [current_user.id]
    if task_id:
        existing_task = db.get_task_by_id(task_id)
        if existing_task:
            user_ids = [u.user_id for u in existing_task.users]
            if current_user.id not in user_ids:
                user_ids.append(current_user.id)
    
    conflict_tasks = _check_conflict_tasks(user_ids, start_dt, end_dt, task_id=task_id)
    
    mapped_conflicts = {}
    for uid, tasks in conflict_tasks.items():
        if tasks:
            user_obj = db.get_user_by_id(uid)
            name = user_obj.name if user_obj else "Unknown Collaborator"
            name_label = f"{name} (You)" if uid == current_user.id else name
            mapped_conflicts[name_label] = tasks
            
    return {
        "has_conflict": len(mapped_conflicts) > 0,
        "conflict_data": mapped_conflicts
    }