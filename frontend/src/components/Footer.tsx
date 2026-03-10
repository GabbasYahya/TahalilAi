"use client";

import Link from "next/link";
import { useLanguage } from "@/context/LanguageContext";

export function Footer() {
  const { t } = useLanguage();

  return (
    <footer className="border-t border-slate-100 bg-slate-950 text-slate-400">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">

        {/* Top row */}
        <div className="grid grid-cols-1 gap-12 sm:grid-cols-2 lg:grid-cols-4">

          {/* Brand column */}
          <div className="lg:col-span-2">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                </svg>
              </div>
              <span className="text-base font-bold text-white">
                Tahalil<span className="text-primary-400">AI</span>
              </span>
            </div>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-slate-500">
              Plain-language explanations for medical lab results. Designed for patients, not doctors.
            </p>
            <div className="mt-6 flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900 px-4 py-3">
              <svg className="h-4 w-4 shrink-0 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
              </svg>
              <span className="text-xs text-slate-400">
                {t("footer.privacy") || "Files are processed securely and deleted immediately after analysis."}
              </span>
            </div>
          </div>

          {/* Tools column */}
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Tools</p>
            <ul className="mt-5 space-y-3">
              {[
                { label: "Analyze a Report", href: "/upload" },
                { label: "Find a Doctor", href: "/doctors" },
              ].map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-400 transition-colors hover:text-white"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Languages column */}
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Languages</p>
            <ul className="mt-5 space-y-3">
              {["English", "Français", "العربية"].map((lang) => (
                <li key={lang}>
                  <span className="text-sm text-slate-400">{lang}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom row */}
        <div className="mt-14 flex flex-col items-start gap-3 border-t border-slate-800 pt-8 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs text-slate-600">
            © {new Date().getFullYear()} TahalilAI. All rights reserved.
          </p>
          <p className="max-w-md text-xs leading-relaxed text-slate-600">
            {t("footer.disclaimer") || "This tool does not provide medical diagnosis. Always consult a licensed healthcare professional."}
          </p>
        </div>

      </div>
    </footer>
  );
}
