"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { useOnboardingStore } from "@/stores/onboarding-store";
import { StepIndicator } from "./components/step-indicator";
import { Step1URL } from "./components/step1-url";
import { Step2Confirm } from "./components/step2-confirm";
import { Step3Matches } from "./components/step3-matches";

export default function OnboardingPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuthStore();
  const { currentStep, loadSuggestions } = useOnboardingStore();

  useEffect(() => {
    // Redirect to login if not authenticated
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    // Load suggestions on mount
    loadSuggestions();
  }, [loadSuggestions]);

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold mb-2">Let's set up your profile</h1>
        <p className="text-gray-600">
          We'll help you find the perfect opportunities in just a few steps
        </p>
      </div>

      <StepIndicator currentStep={currentStep} />

      <div className="mt-8">
        {currentStep === 1 && <Step1URL />}
        {currentStep === 2 && <Step2Confirm />}
        {currentStep === 3 && <Step3Matches />}
      </div>
    </div>
  );
}
