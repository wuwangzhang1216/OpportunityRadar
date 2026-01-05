"use client";

import { useEffect, useState } from "react";
import { driver } from "driver.js";
import { useTourStore } from "@/stores/tour-store";

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
        steps: [
          {
            element: '[data-tour="welcome"]',
            popover: {
              title: "Welcome to OpportunityRadar! 🎉",
              description:
                "Let me show you around. This quick tour will help you get started.",
              side: "bottom",
              align: "center",
            },
          },
          {
            element: '[data-tour="stats"]',
            popover: {
              title: "Your Stats at a Glance",
              description:
                "See your total matches, bookmarked opportunities, and application pipeline status.",
              side: "bottom",
            },
          },
          {
            element: '[data-tour="top-matches"]',
            popover: {
              title: "Your Top Matches",
              description:
                "AI-powered matches based on your profile. Higher scores mean better fit for your skills and goals.",
              side: "left",
            },
          },
          {
            element: '[data-tour="opportunities-nav"]',
            popover: {
              title: "Browse All Opportunities",
              description:
                "Click here to see all matched opportunities with filters and search.",
              side: "right",
            },
          },
          {
            element: '[data-tour="pipeline-nav"]',
            popover: {
              title: "Track Your Progress",
              description:
                "Manage your applications through different stages: Discovered → Preparing → Submitted → Results.",
              side: "right",
            },
          },
          {
            element: '[data-tour="generator-nav"]',
            popover: {
              title: "AI Material Generator",
              description:
                "Generate READMEs, pitch decks, and Q&A responses with AI assistance.",
              side: "right",
            },
          },
        ],
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
