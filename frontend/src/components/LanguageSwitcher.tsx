"use client";

import { useLanguage, Language } from "@/context/LanguageContext";

const languages: { code: Language; label: string }[] = [
  { code: "en", label: "EN" },
  { code: "fr", label: "FR" },
  { code: "ar", label: "AR" },
];

/**
 * Compact language switcher for the header.
 * Highlights current language with a teal accent.
 */
export function LanguageSwitcher() {
  const { language, setLanguage } = useLanguage();

  return (
    <div className="flex items-center gap-1 rounded-full border border-gray-200 bg-gray-50 p-0.5">
      {languages.map((lang) => (
        <button
          key={lang.code}
          onClick={() => setLanguage(lang.code)}
          aria-label={`Switch to ${lang.label}`}
          className={`rounded-full px-3 py-1 text-xs font-medium transition-all ${
            language === lang.code
              ? "bg-primary-600 text-white shadow-sm"
              : "text-gray-500 hover:text-gray-800"
          }`}
        >
          {lang.label}
        </button>
      ))}
    </div>
  );
}
