"use client";

import { useLanguage } from "@/context/LanguageContext";

interface UrgencyBannerProps {
  urgency: string;
}

export function UrgencyBanner({ urgency }: UrgencyBannerProps) {
  const { t } = useLanguage();

  if (urgency === "urgent") {
    return (
      <div
        className="rounded-2xl bg-red-50 dark:bg-red-950/30 border-2 border-red-200 dark:border-red-800 border-l-4 border-l-red-500 p-5 flex items-start gap-4"
        role="alert"
      >
        <svg className="h-6 w-6 shrink-0 text-red-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
        <div>
          <p className="font-bold text-base text-red-800 dark:text-red-300">{t("urgency.urgent.heading")}</p>
          <p className="mt-1 text-base text-red-700 dark:text-red-400 leading-relaxed">{t("urgency.urgent.body")}</p>
        </div>
      </div>
    );
  }

  if (urgency === "soon") {
    return (
      <div
        className="rounded-2xl bg-amber-50 dark:bg-amber-950/30 border-2 border-amber-200 dark:border-amber-800 border-l-4 border-l-amber-500 p-5 flex items-start gap-4"
        role="alert"
      >
        <svg className="h-6 w-6 shrink-0 text-amber-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div>
          <p className="font-bold text-base text-amber-800 dark:text-amber-300">{t("urgency.soon.heading")}</p>
          <p className="mt-1 text-base text-amber-700 dark:text-amber-400 leading-relaxed">{t("urgency.soon.body")}</p>
        </div>
      </div>
    );
  }

  return null;
}
