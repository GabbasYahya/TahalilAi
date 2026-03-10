"use client";

import { useLanguage } from "@/context/LanguageContext";

interface PrivacyBannerProps {
  onDismiss: () => void;
}

export function PrivacyBanner({ onDismiss }: PrivacyBannerProps) {
  const { t } = useLanguage();

  return (
    <div className="rounded-2xl bg-primary-50 dark:bg-primary-950/30 border border-primary-100 dark:border-primary-800 p-4 flex items-start gap-3 mb-6">
      <svg
        className="h-5 w-5 shrink-0 text-primary-600 dark:text-primary-400 mt-0.5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
        aria-hidden="true"
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>

      <div className="flex-1">
        <p className="text-sm font-semibold text-primary-800 dark:text-primary-300">{t("privacy.title")}</p>
        <p className="text-sm text-primary-700 dark:text-primary-400 mt-0.5 leading-relaxed">{t("privacy.body")}</p>
      </div>

      <button
        onClick={onDismiss}
        aria-label="Dismiss privacy notice"
        className="shrink-0 rounded-lg p-1 text-primary-400 dark:text-primary-500 hover:text-primary-600 dark:hover:text-primary-300 hover:bg-primary-100 dark:hover:bg-primary-900/40 transition-colors"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}
