"use client";

import { useLanguage } from "@/context/LanguageContext";

interface ProcessingLoaderProps {
  currentStep: number;
  customMessage?: string;
}

function DocumentIcon() {
  return (
    <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  );
}

function MagnifierIcon() {
  return (
    <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 15.803a7.5 7.5 0 0010.607 10.607z" />
    </svg>
  );
}

function CheckCircleIcon() {
  return (
    <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

const STEP_ICONS = [<DocumentIcon key="doc" />, <MagnifierIcon key="mag" />, <CheckCircleIcon key="chk" />];

export function ProcessingLoader({ currentStep, customMessage }: ProcessingLoaderProps) {
  const { t } = useLanguage();

  const steps = [
    { key: "processing.step1" },
    { key: "processing.step2" },
    { key: "processing.step3" },
  ];

  return (
    <div className="flex flex-col items-center gap-8 py-16">
      <div className="relative flex h-20 w-20 items-center justify-center">
        <div className="absolute inset-0 animate-spin rounded-full border-4 border-slate-200 dark:border-slate-700 border-t-primary-500" style={{ animationDuration: "1.5s" }} />
        <div className="text-primary-600 dark:text-primary-400">
          {STEP_ICONS[currentStep] ?? STEP_ICONS[0]}
        </div>
      </div>

      <div className="flex flex-col gap-4">
        {steps.map((step, idx) => (
          <div key={step.key} className="flex items-center gap-3">
            <div
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold transition-all duration-500 ${
                idx < currentStep
                  ? "bg-primary-500 text-white shadow-sm shadow-primary-200 dark:shadow-primary-900"
                  : idx === currentStep
                  ? "bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300 animate-pulse-gentle"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500"
              }`}
            >
              {idx < currentStep ? (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              ) : (
                idx + 1
              )}
            </div>

            <span
              className={`text-base transition-colors duration-500 ${
                idx === currentStep
                  ? "font-medium text-slate-900 dark:text-slate-100"
                  : idx < currentStep
                  ? "text-slate-400 dark:text-slate-600 line-through decoration-slate-300 dark:decoration-slate-600"
                  : "text-slate-400 dark:text-slate-500"
              }`}
            >
              {t(step.key as any)}
            </span>
          </div>
        ))}

        {customMessage && (
          <div className="mt-4 text-center text-sm text-primary-600 dark:text-primary-400 font-medium animate-pulse">
            {customMessage}
          </div>
        )}
      </div>
    </div>
  );
}
