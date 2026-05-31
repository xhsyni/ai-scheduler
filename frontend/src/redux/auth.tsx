import { createSlice, createAsyncThunk, PayloadAction } from "@reduxjs/toolkit";
import { registerUser as registerUserApi, loginUser as loginUserApi } from "../api/auth";

export const registerUser = createAsyncThunk(
    "users/register",
    async ({ username, email, password }: { username: string, email: string, password: string }) => {
        const res = await registerUserApi(username, email, password);
        console.log(res)
        return res;
    }
)

export const loginUser = createAsyncThunk(
    "users/login",
    async ({ email, password }: { email: string, password: string }) => {
        const res = await loginUserApi(email, password);
        console.log(res)
        return res;
    }
)

interface AuthState {
    isAuthenticated: boolean;
    user: { username: string } | null;
    error: string | null;
}

const initialState: AuthState = {
    isAuthenticated: false,
    user: null,
    error: null
};

const authSlice = createSlice({
    name: "auth",
    initialState,
    reducers: {
        clearError: (state: { error: string | null; }) => {
            state.error = null;
        }
    },
    extraReducers: (builder) => {
        builder
            .addCase(registerUser.fulfilled, (state, action) => {
                state.isAuthenticated = true;
                state.user = action.payload;
                state.error = null;
            })
            .addCase(registerUser.rejected, (state, action) => {
                state.isAuthenticated = false;
                state.user = null;
                state.error = action.error.message || "Registration failed";
            })
            .addCase(loginUser.fulfilled, (state, action) => {
                state.isAuthenticated = true;
                state.user = action.payload;
                state.error = null;
            })
            .addCase(loginUser.rejected, (state, action) => {
                state.isAuthenticated = false;
                state.user = null;
                state.error = action.error.message || "Login failed";
            });
    }
});

export const { clearError } = authSlice.actions;
export default authSlice.reducer;
