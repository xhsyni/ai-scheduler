import axios from "axios";
import { API_BASE_URL } from "./auth";

export async function getConversations() {
  const res = await axios.get(`${API_BASE_URL}/conversation/get-conversations`, {
    withCredentials: true,
  });
  return res.data;
}

export async function createConversation(title: string) {
  const res = await axios.post(`${API_BASE_URL}/conversation/create-conversation`, {
    title,
  }, {
    withCredentials: true,
  });
  return res.data;
}

export async function getMessages(conversationId: string) {
  const res = await axios.get(`${API_BASE_URL}/conversation/${conversationId}/get-messages`, {
    withCredentials: true,
  });
  return res.data;
}

export async function sendMessage(conversationId: string, content: string) {
  const res = await axios.post(`${API_BASE_URL}/conversation/${conversationId}/send-message`, {
    content,
  }, {
    withCredentials: true,
  });
  return res.data;
}
