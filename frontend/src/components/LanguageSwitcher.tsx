"use client";

import { useLanguage, Language } from "@/context/LanguageContext";

const languages: { code: Language; label: string }[] = [
  { code: "en", label: "EN" },
  { code: "fr", label: "FR" },
  { code: "ar", label: "AR" },
];

export function LanguageSwitcher() {
  const { language, setLanguage } = useLanguage();

  return (
    <div className="flex items-center gap-1 rounded-full border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-0.5">
      {languages.map((lang) => (
        <button
          key={lang.code}
          onClick={() => setLanguage(lang.code)}
          aria-label={`Switch to ${lang.label}`}
          className={`rounded-full px-3 py-1 text-xs font-medium transition-all ${
            language === lang.code
              ? "bg-primary-600 text-white shadow-sm"
              : "text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
          }`}
        >
          {lang.label}
        </button>
      ))}
    </div>
  );
}
