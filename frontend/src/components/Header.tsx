"use client";

import Link from "next/link";
import { useLanguage } from "@/context/LanguageContext";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { ThemeToggle } from "./ThemeToggle";

export function Header() {
  const { t } = useLanguage();

  return (
    <header className="sticky top-0 z-50 border-b border-slate-100 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">

        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
            </svg>
          </div>
          <span className="text-base font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Tahalil<span className="text-primary-600">AI</span>
          </span>
        </Link>

        {/* Right side */}
        <div className="flex items-center gap-4">

          {/* Nav links */}
          <nav className="hidden sm:flex items-center gap-1">
            <Link
              href="/"
              className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100"
            >
              {t("header.home") || "Home"}
            </Link>
            <Link
              href="/doctors"
              className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100"
            >
              {t("doctors.nav") || "Find a Doctor"}
            </Link>
            <Link
              href="/hospitals"
              className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100"
            >
              {t("hospitals.nav") || "Hospitals"}
            </Link>
          </nav>

          {/* Divider */}
          <div className="hidden sm:block h-5 w-px bg-slate-200 dark:bg-slate-700" aria-hidden="true" />

          {/* Utility controls */}
          <div className="flex items-center gap-1">
            <LanguageSwitcher />
            <ThemeToggle />
          </div>

        </div>

      </div>
    </header>
  );
}
