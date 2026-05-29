from models.users import User
from services.db import DBService
from fastapi import HTTPException, status
from models.tasks import Task, GroupTask
from utils.timezone import to_myt,now_myt
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta

db = DBService()

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
    new_end_time
):
    if isinstance(user_ids, str):
        user_ids = [user_ids]

    conflicts = {}
    for user_id in user_ids:
        tasks = db.get_tasks_by_user_id_and_date(user_id, new_start_time,new_end_time)
        user_conflicts = []
        for task in tasks:
            if (to_myt(new_start_time) < to_myt(task.end_time) and to_myt(new_end_time) > to_myt(task.start_time)):
                user_conflicts.append(task.to_json())
        conflicts[user_id] = user_conflicts
    return conflicts

def _check_free_time_slot(
    all_busy_slots: List[Dict[str]], 
    working_bounds: Dict[str], 
    duration_minutes: int
) -> List[Dict[str]]:
    sorted_busy = sorted(all_busy_slots, key=lambda x: x['start'])
    
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
        conflict_tasks = _check_conflict_tasks(task, current_user.id)
        if conflict_tasks:
            return JSONResponse({"conflict_data":conflict_tasks,"status_code":status.HTTP_400_BAD_REQUEST, "detail": f"You have a time conflict with {len(conflict_tasks)} tasks"})
        duration = (task.end_time - task.start_time).total_seconds() / 60
        task = task.model_copy(update={"duration": duration,"updated_at":now_myt()})
    else:
        task = task.model_copy(update={"updated_at":now_myt()})
    task = task.model_copy(update={"users": [GroupTask(user_id=current_user.id,name=current_user.name, role="owner")]})
    db.insert_tasks([task])
    return {
        "status": status.HTTP_200_OK,
        "message": "Task created successfully"
    }

async def get_tasks_by_date(current_user: User,start_date,end_date):
    if end_date - start_date > 32:
        return JSONResponse({"status_code":status.HTTP_400_BAD_REQUEST, "detail": f"The filter date cannot be more than 32 days."})
    tasks = db.get_tasks_by_user_id_and_date(current_user.id,start_date,end_date)

    grouped: dict[str, list] = {}
    for task in tasks:
        date_key = task.start_time.date()
        grouped.setdefault(date_key, []).append(task.to_json())

    return {
        "status": status.HTTP_200_OK,
        "tasks": grouped
    }

async def update_task(task: Task, task_id: str, current_user: User):
    task = task.model_copy(update={"id": task_id})
    if task.start_time and task.end_time:
        if not check_valid_task(task):
            return JSONResponse({"status_code":status.HTTP_400_BAD_REQUEST, "detail": f"Invalid task"})
        conflict_tasks = _check_conflict_tasks(task, current_user.id)
        if conflict_tasks:
            return JSONResponse({"conflict_data":conflict_tasks,"status_code":status.HTTP_400_BAD_REQUEST, "detail": f"You have a time conflict with {len(conflict_tasks)} tasks"})
        duration = (task.end_time - task.start_time).total_seconds() / 60
        task = task.model_copy(update={"duration": duration,"updated_at":now_myt()})
    else:
        task = task.model_copy(update={"updated_at":now_myt()})
    db.update_task(task_id, task)
    return {
        "status": status.HTTP_200_OK,
        "message": "Task updated successfully"
    }

async def add_user_to_task(task_id: str, user_id: str, email: str, role: str, current_user: User):
    if not db.get_task_by_id(task_id):
        return JSONResponse({"status_code":status.HTTP_404_NOT_FOUND, "detail": f"Task {task_id} not found"})
    if user_id:
        target_user = db.get_user_by_id(user_id)
    else:
        target_user = db.get_user_by_email(email)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User not found")

    if db.user_exists_in_task(task_id, target_user.id):
        return JSONResponse({"status_code":status.HTTP_400_BAD_REQUEST, "detail": f"User {target_user.id} already exists in task {task_id}"})

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
    if user[0].role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to remove {user[0].name} from this task"
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