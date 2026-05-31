import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export async function registerUser(username: string, email: string, password: string) {
    const res = await axios.post(`${API_BASE_URL}/users/register`, {
        "name": username,
        "email": email,
        "password": password
    });
    return res.data;
}

export async function loginUser(email: string, password: string) {
    const params = new URLSearchParams();

    params.append("username", email);
    params.append("password", password);

    const res = await axios.post(
        `${API_BASE_URL}/users/login`,
        params,
        {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
        }
    );

    return res.data;
}

export async function getMe() {
    const res = await axios.get(`${API_BASE_URL}/users/me`, {
        withCredentials: true
    });

    return res.data;
}