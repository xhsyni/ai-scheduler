from models.users import User
from services.db import DBService
from fastapi import HTTPException, status
from models.tasks import Task, GroupTask
from utils.timezone import to_myt,now_myt
from fastapi.responses import JSONResponse

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

def check_conflict_tasks(task:Task, current_user: User):
    tasks_db = db.get_tasks_by_user_id(current_user.id)
    conflict_tasks = []
    for task_in_db in tasks_db:
        if task_in_db.id == task.id:
            continue
        if to_myt(task.start_time) < to_myt(task_in_db.end_time) and to_myt(task.end_time) > to_myt(task_in_db.start_time):
            conflict_tasks.append(task_in_db.to_json())
    return conflict_tasks


# Task Function
async def create_task(task: Task, current_user: User):
    if task.start_time and task.end_time:
        if not check_valid_task(task):
            return JSONResponse({"status_code":status.HTTP_400_BAD_REQUEST, "detail": f"Invalid task"})
        conflict_tasks = check_conflict_tasks(task, current_user)
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

async def get_tasks(current_user: User):
    tasks = db.get_tasks_by_user_id(current_user.id)

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
        conflict_tasks = check_conflict_tasks(task, current_user)
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