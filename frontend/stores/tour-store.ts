import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

// SSR-safe storage (from auth-store.ts pattern)
const ssrStorage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {},
};

// Type-safe tour ID mapping
type TourId = "dashboard" | "generator" | "pipeline";

interface TourState {
  hasCompletedDashboardTour: boolean;
  hasCompletedGeneratorTour: boolean;
  hasCompletedPipelineTour: boolean;

  markTourComplete: (tourId: TourId) => void;
  resetTours: () => void;
  isTourComplete: (tourId: TourId) => boolean;
}

const keyByTour: Record<TourId, keyof Pick<TourState, "hasCompletedDashboardTour" | "hasCompletedGeneratorTour" | "hasCompletedPipelineTour">> = {
  dashboard: "hasCompletedDashboardTour",
  generator: "hasCompletedGeneratorTour",
  pipeline: "hasCompletedPipelineTour",
};

export const useTourStore = create<TourState>()(
  persist(
    (set, get) => ({
      hasCompletedDashboardTour: false,
      hasCompletedGeneratorTour: false,
      hasCompletedPipelineTour: false,

      markTourComplete: (tourId: TourId) => {
        const key = keyByTour[tourId];
        set({ [key]: true } as Partial<TourState>);
      },

      resetTours: () =>
        set({
          hasCompletedDashboardTour: false,
          hasCompletedGeneratorTour: false,
          hasCompletedPipelineTour: false,
        }),

      isTourComplete: (tourId: TourId) => {
        const key = keyByTour[tourId];
        return get()[key];
      },
    }),
    {
      name: "opportunity-radar-tours",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? localStorage : ssrStorage
      ),
    }
  )
);
