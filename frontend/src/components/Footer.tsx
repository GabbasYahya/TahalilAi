"use client";

import { useLanguage } from "@/context/LanguageContext";

/**
 * Global footer — always visible, contains disclaimer & privacy note.
 * Uses muted copy to maintain trust without alarming the user.
 */
export function Footer() {
  const { t } = useLanguage();

  return (
    <footer className="border-t border-gray-100 bg-gray-50">
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <div className="flex flex-col items-center gap-3 text-center text-sm text-gray-500">
          <p>{t("footer.disclaimer")}</p>
          <p className="flex items-center gap-1.5">
            {/* Lock icon for privacy */}
            <svg
              className="h-3.5 w-3.5 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z"
              />
            </svg>
            {t("footer.privacy")}
          </p>
          <p className="mt-2 text-xs text-gray-400">
            © {new Date().getFullYear()} TahalilAI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
