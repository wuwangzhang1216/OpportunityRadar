import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { apiClient } from "@/services/api-client";

const ssrStorage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {},
};

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
  hasHydrated: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  clearError: () => void;
  setHasHydrated: (state: boolean) => void;
}

// Create store with persist middleware
const useAuthStoreBase = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true, // Start with loading true
      hasHydrated: false,
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
        const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;

        if (!token) {
          set({ user: null, isAuthenticated: false, isLoading: false });
          return;
        }

        // If we have user data from hydration and token exists, trust it
        const currentState = get();
        if (currentState.isAuthenticated && currentState.user) {
          set({ isLoading: false });
          return;
        }

        // Only fetch from API if we don't have user data
        set({ isLoading: true });
        try {
          const user = await apiClient.getMe();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch {
          // Token is invalid, clear it
          apiClient.clearToken();
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },

      clearError: () => set({ error: null }),

      setHasHydrated: (state: boolean) => {
        set({ hasHydrated: state, isLoading: false });
      },
    }),
    {
      name: "auth-storage",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? localStorage : ssrStorage
      ),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state, error) => {
        if (error) {
          console.error("Hydration error:", error);
        }
        // Use setTimeout to ensure this runs after React hydration
        setTimeout(() => {
          useAuthStoreBase.setState({ hasHydrated: true, isLoading: false });
        }, 0);
      },
    }
  )
);

export const useAuthStore = useAuthStoreBase;
