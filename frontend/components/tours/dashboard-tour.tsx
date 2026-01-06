"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { driver, type Driver } from "driver.js";
import { useTourStore } from "@/stores/tour-store";

// Tour steps configuration - shared between auto and manual triggers
const DASHBOARD_TOUR_STEPS = [
  {
    element: '[data-tour="welcome"]',
    popover: {
      title: "Welcome to OpportunityRadar! 🎉",
      description:
        "Let me show you around. This quick tour will help you get started.",
      side: "bottom" as const,
      align: "center" as const,
    },
  },
  {
    element: '[data-tour="stats"]',
    popover: {
      title: "Your Stats at a Glance",
      description:
        "See your total matches, bookmarked opportunities, and application pipeline status.",
      side: "bottom" as const,
    },
  },
  {
    element: '[data-tour="top-matches"]',
    popover: {
      title: "Your Top Matches",
      description:
        "AI-powered matches based on your profile. Higher scores mean better fit for your skills and goals.",
      side: "left" as const,
    },
  },
  {
    element: '[data-tour="opportunities-nav"]',
    popover: {
      title: "Browse All Opportunities",
      description:
        "Click here to see all matched opportunities with filters and search.",
      side: "right" as const,
    },
  },
  {
    element: '[data-tour="pipeline-nav"]',
    popover: {
      title: "Track Your Progress",
      description:
        "Manage your applications through different stages: Discovered → Preparing → Submitted → Results.",
      side: "right" as const,
    },
  },
  {
    element: '[data-tour="generator-nav"]',
    popover: {
      title: "AI Material Generator",
      description:
        "Generate READMEs, pitch decks, and Q&A responses with AI assistance.",
      side: "right" as const,
    },
  },
];

// Hook for manual tour triggering - can be used by other components
export function useDashboardTour() {
  const { hasCompletedDashboardTour, markTourComplete } = useTourStore();
  const driverRef = useRef<Driver | null>(null);

  const startTour = useCallback(() => {
    // Clean up any existing tour instance
    if (driverRef.current) {
      driverRef.current.destroy();
    }

    const driverObj = driver({
      showProgress: true,
      allowClose: true,
      doneBtnText: "Got it!",
      nextBtnText: "Next",
      prevBtnText: "Back",
      steps: DASHBOARD_TOUR_STEPS,
      onDestroyed: () => {
        markTourComplete("dashboard");
        driverRef.current = null;
      },
    });

    driverRef.current = driverObj;
    driverObj.drive();
  }, [markTourComplete]);

  const stopTour = useCallback(() => {
    if (driverRef.current) {
      driverRef.current.destroy();
      driverRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (driverRef.current) {
        driverRef.current.destroy();
      }
    };
  }, []);

  return {
    startTour,
    stopTour,
    hasCompletedDashboardTour,
  };
}

// Component for automatic tour on first visit
export function DashboardTour() {
  const { hasCompletedDashboardTour, markTourComplete } = useTourStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    // Don't run on server or if not mounted
    if (!mounted) return;
    // Don't run if tour already completed
    if (hasCompletedDashboardTour) return;

    // Delay to ensure DOM is rendered and data is loaded
    const timer = setTimeout(() => {
      const driverObj = driver({
        showProgress: true,
        allowClose: true,
        doneBtnText: "Got it!",
        nextBtnText: "Next",
        prevBtnText: "Back",
        steps: DASHBOARD_TOUR_STEPS,
        onDestroyed: () => {
          markTourComplete("dashboard");
        },
      });

      driverObj.drive();
    }, 800);

    return () => clearTimeout(timer);
  }, [mounted, hasCompletedDashboardTour, markTourComplete]);

  return null;
}
