"use client";

import { Check, Link2, UserCheck, Rocket } from "lucide-react";
import type { OnboardingStep } from "@/stores/onboarding-store";

interface StepIndicatorProps {
  currentStep: OnboardingStep;
}

const steps = [
  { step: 1 as const, label: "Enter URL", icon: Link2 },
  { step: 2 as const, label: "Confirm Profile", icon: UserCheck },
  { step: 3 as const, label: "Get Matches", icon: Rocket },
];

export function StepIndicator({ currentStep }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-between">
      {steps.map((item, index) => {
        const Icon = item.icon;
        const isCompleted = currentStep > item.step;
        const isCurrent = currentStep === item.step;

        return (
          <div key={item.step} className="flex items-center flex-1">
            {/* Step circle */}
            <div className="flex flex-col items-center">
              <div
                className={`
                  w-10 h-10 rounded-full flex items-center justify-center
                  transition-all duration-300
                  ${
                    isCompleted
                      ? "bg-green-500 text-white"
                      : isCurrent
                      ? "bg-blue-600 text-white"
                      : "bg-gray-200 text-gray-500"
                  }
                `}
              >
                {isCompleted ? (
                  <Check className="h-5 w-5" />
                ) : (
                  <Icon className="h-5 w-5" />
                )}
              </div>
              <span
                className={`
                  mt-2 text-xs font-medium
                  ${isCurrent ? "text-blue-600" : "text-gray-500"}
                `}
              >
                {item.label}
              </span>
            </div>

            {/* Connector line */}
            {index < steps.length - 1 && (
              <div
                className={`
                  flex-1 h-0.5 mx-4
                  ${isCompleted ? "bg-green-500" : "bg-gray-200"}
                `}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
