"use client";

import { useLanguage } from "@/context/LanguageContext";

interface ProcessingLoaderProps {
  /** Current step index (0, 1, 2) */
  currentStep: number;
}

/**
 * Calm, step-based loader shown while the report is being "analyzed."
 * Designed to reduce anxiety — uses soft language and gentle animation.
 */
export function ProcessingLoader({ currentStep }: ProcessingLoaderProps) {
  const { t } = useLanguage();

  const steps = [
    { key: "processing.step1", icon: "📄" },
    { key: "processing.step2", icon: "🔍" },
    { key: "processing.step3", icon: "✨" },
  ];

  return (
    <div className="flex flex-col items-center gap-8 py-16">
      {/* Animated circle */}
      <div className="relative flex h-20 w-20 items-center justify-center">
        <div className="absolute inset-0 animate-spin rounded-full border-4 border-gray-200 border-t-primary-500" style={{ animationDuration: "1.5s" }} />
        <span className="text-2xl">{steps[currentStep]?.icon ?? "📄"}</span>
      </div>

      {/* Step list */}
      <div className="flex flex-col gap-4">
        {steps.map((step, idx) => (
          <div key={step.key} className="flex items-center gap-3">
            {/* Step indicator */}
            <div
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold transition-all duration-500 ${
                idx < currentStep
                  ? "bg-primary-500 text-white"
                  : idx === currentStep
                  ? "bg-primary-100 text-primary-700 animate-pulse-gentle"
                  : "bg-gray-100 text-gray-400"
              }`}
            >
              {idx < currentStep ? "✓" : idx + 1}
            </div>

            <span
              className={`text-sm transition-colors duration-500 ${
                idx === currentStep
                  ? "font-medium text-gray-900"
                  : idx < currentStep
                  ? "text-gray-500"
                  : "text-gray-400"
              }`}
            >
              {t(step.key)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
