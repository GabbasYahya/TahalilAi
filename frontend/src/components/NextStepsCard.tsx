"use client";

import { useLanguage } from "@/context/LanguageContext";

interface NextStepsCardProps {
  urgency: string;
  hasDoctors: boolean;
}

export function NextStepsCard({ urgency, hasDoctors }: NextStepsCardProps) {
  const { t } = useLanguage();

  const urgentSteps = [
    t("nextsteps.urgent.1"),
    t("nextsteps.urgent.2"),
    t("nextsteps.urgent.3"),
    t("nextsteps.urgent.4"),
  ];

  const soonSteps = [
    t("nextsteps.soon.1"),
    t("nextsteps.soon.2"),
    t("nextsteps.soon.3"),
    hasDoctors ? t("nextsteps.soon.4") : t("nextsteps.routine.3"),
  ];

  const routineSteps = [
    t("nextsteps.routine.1"),
    t("nextsteps.routine.2"),
    t("nextsteps.routine.3"),
  ];

  const steps =
    urgency === "urgent" ? urgentSteps :
    urgency === "soon"   ? soonSteps   :
                           routineSteps;

  const iconColor =
    urgency === "urgent" ? "bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400" :
    urgency === "soon"   ? "bg-amber-100 dark:bg-amber-900/40 text-amber-600 dark:text-amber-400" :
                           "bg-primary-100 dark:bg-primary-900/40 text-primary-600 dark:text-primary-400";

  return (
    <div className="rounded-2xl bg-white dark:bg-slate-800 ring-1 ring-slate-100 dark:ring-slate-700 shadow-sm p-6">
      <div className="flex items-center gap-3 mb-5">
        <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${iconColor}`}>
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
          </svg>
        </div>
        <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">{t("nextsteps.heading")}</h2>
      </div>

      <ol className="space-y-3">
        {steps.map((step, i) => (
          <li key={i} className="flex items-start gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-700 text-xs font-bold text-slate-500 dark:text-slate-400 mt-0.5">
              {i + 1}
            </span>
            <span className="text-base text-slate-700 dark:text-slate-300 leading-relaxed">{step}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
