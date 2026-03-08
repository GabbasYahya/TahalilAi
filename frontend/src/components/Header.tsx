"use client";

import Link from "next/link";
import { useLanguage } from "@/context/LanguageContext";
import { LanguageSwitcher } from "./LanguageSwitcher";

/**
 * Global header — minimal, trustworthy, always visible.
 * Logo links to home. Language switcher on the right.
 */
export function Header() {
  const { t } = useLanguage();

  return (
    <header className="sticky top-0 z-50 border-b border-gray-100 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2">
          {/* Inline logo mark — a stylized medical cross + AI spark */}
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white font-bold text-sm">
            T
          </div>
          <span className="text-xl font-semibold tracking-tight text-gray-900">
            {t("header.logo")}
          </span>
        </Link>

        <div className="flex items-center gap-4">
          <Link
            href="/doctors"
            className="text-sm font-medium text-slate-600 hover:text-indigo-600 transition-colors"
          >
            {t("doctors.nav")}
          </Link>
          <LanguageSwitcher />
        </div>
      </div>
    </header>
  );
}
