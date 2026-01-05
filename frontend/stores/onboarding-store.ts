import { create } from "zustand";
import { apiClient } from "@/services/api-client";
import type {
  ExtractedProfile,
  OnboardingConfirmRequest,
  OnboardingSuggestions,
  Match,
} from "@/types";

export type OnboardingStep = 1 | 2 | 3;

interface OnboardingData {
  display_name: string;
  bio: string;
  tech_stack: string[];
  industries: string[];
  goals: string[];
  interests: string[];
  experience_level: string;
  team_size: number;
  profile_type: string;
  location_country: string;
  location_region: string;
}

interface OnboardingState {
  // Current step
  currentStep: OnboardingStep;

  // Step 1: URL input
  url: string;
  isExtracting: boolean;
  extractError: string | null;

  // Step 2: Extracted profile data
  extractedProfile: ExtractedProfile | null;
  confirmedData: OnboardingData;
  isConfirming: boolean;
  confirmError: string | null;

  // Step 3: Top matches
  topMatches: Match[];
  isLoadingMatches: boolean;
  matchError: string | null;

  // Suggestions from backend
  suggestions: OnboardingSuggestions | null;

  // Actions
  setUrl: (url: string) => void;
  extractProfile: () => Promise<void>;
  updateField: <K extends keyof OnboardingData>(
    field: K,
    value: OnboardingData[K]
  ) => void;
  confirmProfile: () => Promise<void>;
  loadSuggestions: () => Promise<void>;
  loadTopMatches: () => Promise<void>;
  pollTopMatches: (maxAttempts?: number) => Promise<void>;
  goToStep: (step: OnboardingStep) => void;
  skipToManual: () => void;
  reset: () => void;
}

const initialData: OnboardingData = {
  display_name: "",
  bio: "",
  tech_stack: [],
  industries: [],
  goals: [],
  interests: [],
  experience_level: "intermediate",
  team_size: 1,
  profile_type: "developer",
  location_country: "",
  location_region: "",
};

export const useOnboardingStore = create<OnboardingState>((set, get) => ({
  currentStep: 1,
  url: "",
  isExtracting: false,
  extractError: null,
  extractedProfile: null,
  confirmedData: { ...initialData },
  isConfirming: false,
  confirmError: null,
  topMatches: [],
  isLoadingMatches: false,
  matchError: null,
  suggestions: null,

  setUrl: (url: string) => set({ url }),

  extractProfile: async () => {
    const { url } = get();
    if (!url) return;

    set({ isExtracting: true, extractError: null });

    try {
      const response = await apiClient.extractProfileFromUrl(url);

      if (!response.success) {
        set({
          extractError: response.error_message || "Failed to extract profile",
          isExtracting: false,
        });
        return;
      }

      const extracted = response.extracted_profile;

      // Pre-populate confirmed data from extracted profile
      const newConfirmedData: OnboardingData = {
        display_name:
          typeof extracted?.company_name?.value === "string"
            ? extracted.company_name.value
            : "",
        bio:
          typeof extracted?.product_description?.value === "string"
            ? extracted.product_description.value
            : "",
        tech_stack: Array.isArray(extracted?.tech_stack?.value)
          ? extracted.tech_stack.value
          : [],
        industries: Array.isArray(extracted?.industries?.value)
          ? extracted.industries.value
          : [],
        goals: Array.isArray(extracted?.goals?.value)
          ? extracted.goals.value
          : [],
        // interests should mirror industries for matching
        interests: Array.isArray(extracted?.industries?.value)
          ? extracted.industries.value
          : [],
        experience_level: "intermediate",
        team_size:
          typeof extracted?.team_size?.value === "number"
            ? extracted.team_size.value
            : 1,
        profile_type:
          typeof extracted?.profile_type?.value === "string"
            ? extracted.profile_type.value
            : "developer",
        location_country:
          typeof extracted?.location?.value === "string"
            ? extracted.location.value
            : "",
        location_region: "",
      };

      set({
        extractedProfile: extracted,
        confirmedData: newConfirmedData,
        isExtracting: false,
        currentStep: 2,
      });
    } catch (error: any) {
      set({
        extractError:
          error.response?.data?.detail ||
          error.message ||
          "Failed to extract profile",
        isExtracting: false,
      });
    }
  },

  updateField: (field, value) => {
    set((state) => ({
      confirmedData: {
        ...state.confirmedData,
        [field]: value,
      },
    }));
  },

  confirmProfile: async () => {
    const { confirmedData, url } = get();

    set({ isConfirming: true, confirmError: null });

    try {
      const requestData: OnboardingConfirmRequest = {
        ...confirmedData,
        source_url: url || undefined,
      };

      const response = await apiClient.confirmOnboarding(requestData);

      if (!response.success) {
        set({
          confirmError: response.error_message || "Failed to create profile",
          isConfirming: false,
        });
        return;
      }

      set({
        isConfirming: false,
        currentStep: 3,
      });

      // Poll for top matches after profile is created (matches computed in background)
      get().pollTopMatches();
    } catch (error: any) {
      set({
        confirmError:
          error.response?.data?.detail ||
          error.message ||
          "Failed to create profile",
        isConfirming: false,
      });
    }
  },

  loadSuggestions: async () => {
    try {
      const suggestions = await apiClient.getOnboardingSuggestions();
      set({ suggestions });
    } catch (error) {
      console.error("Failed to load suggestions:", error);
    }
  },

  loadTopMatches: async () => {
    set({ isLoadingMatches: true });

    try {
      const response = await apiClient.getTopMatches(5);
      set({
        topMatches: response.items || [],
        isLoadingMatches: false,
      });
    } catch (error) {
      console.error("Failed to load top matches:", error);
      set({ isLoadingMatches: false });
    }
  },

  // Poll for matches with exponential backoff
  pollTopMatches: async (maxAttempts = 10) => {
    set({ isLoadingMatches: true, matchError: null });

    let consecutiveErrors = 0;
    const errorThreshold = 3;

    for (let i = 0; i < maxAttempts; i++) {
      try {
        const response = await apiClient.getTopMatches(5);
        consecutiveErrors = 0; // Reset on success

        if (response.items?.length) {
          set({ topMatches: response.items, isLoadingMatches: false, matchError: null });
          return;
        }
      } catch (error) {
        consecutiveErrors++;

        // Surface error after threshold consecutive failures
        if (consecutiveErrors >= errorThreshold) {
          set({
            isLoadingMatches: false,
            matchError: "Unable to load matches. Please try again later.",
          });
          return;
        }
      }

      // Exponential backoff: 250ms, 500ms, 1s, 2s, 2s, 2s...
      await new Promise((r) => setTimeout(r, Math.min(2000, 250 * 2 ** i)));
    }

    // Max attempts reached without matches
    set({
      isLoadingMatches: false,
      matchError: "No matches found yet. Your matches are still being computed.",
    });
  },

  goToStep: (step: OnboardingStep) => set({ currentStep: step }),

  skipToManual: () => {
    set({
      currentStep: 2,
      extractedProfile: null,
      confirmedData: { ...initialData },
    });
  },

  reset: () =>
    set({
      currentStep: 1,
      url: "",
      isExtracting: false,
      extractError: null,
      extractedProfile: null,
      confirmedData: { ...initialData },
      isConfirming: false,
      confirmError: null,
      topMatches: [],
      isLoadingMatches: false,
      matchError: null,
    }),
}));
