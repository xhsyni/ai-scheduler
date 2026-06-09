import axios from "axios";
import { API_BASE_URL } from "./auth";

export interface TaskPayload {
  title: string;
  description?: string;
  priority?: "low" | "mid" | "high";
  category?: string;
  location?: string;
  link?: string[];
  start_time: string; // ISO 8601 string
  end_time: string; // ISO 8601 string
  reminder?: boolean;
  status?: string;
}

export async function getTasks(startDate: string, endDate?: string) {
  const params: Record<string, string> = { start_date: startDate };
  if (endDate) {
    params.end_date = endDate;
  }
  const res = await axios.get(`${API_BASE_URL}/task/get-tasks`, {
    params,
    withCredentials: true,
  });
  return res.data;
}

export async function createTask(taskData: TaskPayload) {
  const res = await axios.post(`${API_BASE_URL}/task/create-task`, taskData, {
    withCredentials: true,
  });
  return res.data;
}

export async function updateTask(taskId: string, taskData: TaskPayload) {
  const res = await axios.put(`${API_BASE_URL}/task/update-task/${taskId}`, taskData, {
    withCredentials: true,
  });
  return res.data;
}


export async function addUserToTask(taskId: string, email: string, role: string) {
  const res = await axios.post(`${API_BASE_URL}/task/add-user-to-task/${taskId}`, {
    email,
    role,
  }, {
    withCredentials: true,
  });
  return res.data;
}

export async function deleteUserFromTask(taskId: string, userId: string) {
  const res = await axios.delete(`${API_BASE_URL}/task/delete-user-from-task/${taskId}/${userId}`, {
    withCredentials: true,
  });
  return res.data;
}

export async function deleteTask(taskId: string) {
  const res = await axios.delete(`${API_BASE_URL}/task/delete-task/${taskId}`, {
    withCredentials: true,
  });
  return res.data;
}

export async function getGroupsOverlay(weekStart: string) {
  const res = await axios.get(`${API_BASE_URL}/task/groups/overlay`, {
    params: { week_start: weekStart },
    withCredentials: true,
  });
  return res.data;
}

export async function lockInGroupTask(payload: { title: string; start_time: string; end_time: string; location?: string }) {
  const res = await axios.post(`${API_BASE_URL}/task/groups/lock-in`, payload, {
    withCredentials: true,
  });
  return res.data;
}

export async function checkTaskConflict(params: { start_time: string; end_time: string; task_id?: string }) {
  const res = await axios.get(`${API_BASE_URL}/task/check-conflict`, {
    params,
    withCredentials: true,
  });
  return res.data;
}
