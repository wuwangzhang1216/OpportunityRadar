import { create } from "zustand";
import { persist } from "zustand/middleware";
import { apiClient } from "@/services/api-client";

interface User {
  id: string;
  email: string;
  full_name: string;
  has_profile: boolean;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const data = await apiClient.login(email, password);
          apiClient.setToken(data.access_token);

          const user = await apiClient.getMe();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error: any) {
          const message =
            error.response?.data?.detail || "Login failed. Please try again.";
          set({ error: message, isLoading: false });
          throw error;
        }
      },

      signup: async (email: string, password: string, fullName: string) => {
        set({ isLoading: true, error: null });
        try {
          await apiClient.signup(email, password, fullName);
          // Auto-login after signup
          await get().login(email, password);
        } catch (error: any) {
          const message =
            error.response?.data?.detail || "Signup failed. Please try again.";
          set({ error: message, isLoading: false });
          throw error;
        }
      },

      logout: () => {
        apiClient.clearToken();
        set({ user: null, isAuthenticated: false });
      },

      checkAuth: async () => {
        set({ isLoading: true });
        try {
          const user = await apiClient.getMe();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch {
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({ isAuthenticated: state.isAuthenticated }),
    }
  )
);
