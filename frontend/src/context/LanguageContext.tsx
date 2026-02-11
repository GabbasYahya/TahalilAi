"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

export type Language = "en" | "fr" | "ar";

interface Translations {
  [key: string]: { en: string; fr: string; ar: string };
}

/* ── Central translation dictionary ── */
export const translations: Translations = {
  // Header
  "header.logo": { en: "TahalilAI", fr: "TahalilAI", ar: "تحاليلAI" },

  // Landing
  "hero.headline": {
    en: "Medical reports, explained clearly.",
    fr: "Rapports médicaux, expliqués clairement.",
    ar: "تقارير طبية، مُوضَّحة ببساطة.",
  },
  "hero.subtext": {
    en: "Upload your lab results and receive a calm, easy-to-understand explanation. No diagnosis. Just clarity.",
    fr: "Téléchargez vos résultats de laboratoire et recevez une explication calme et facile à comprendre. Pas de diagnostic. Juste de la clarté.",
    ar: "ارفع نتائج تحاليلك واحصل على شرح هادئ وسهل الفهم. لا تشخيص. فقط وضوح.",
  },
  "hero.cta": {
    en: "Upload my report",
    fr: "Télécharger mon rapport",
    ar: "ارفع تقريري",
  },
  "hero.trust": {
    en: "Your files are processed securely and automatically deleted.",
    fr: "Vos fichiers sont traités en toute sécurité et automatiquement supprimés.",
    ar: "يتم معالجة ملفاتك بشكل آمن وحذفها تلقائيًا.",
  },

  // Upload
  "upload.title": {
    en: "Upload your medical report (PDF or image)",
    fr: "Téléchargez votre rapport médical (PDF ou image)",
    ar: "ارفع تقريرك الطبي (PDF أو صورة)",
  },
  "upload.dragText": {
    en: "Drag & drop your file here, or click to browse",
    fr: "Glissez-déposez votre fichier ici, ou cliquez pour parcourir",
    ar: "اسحب وأفلت ملفك هنا، أو انقر للاستعراض",
  },
  "upload.formats": {
    en: "Supports PDF, PNG, JPG (max 10 MB)",
    fr: "Supporte PDF, PNG, JPG (max 10 Mo)",
    ar: "يدعم PDF, PNG, JPG (الحد الأقصى 10 ميجابايت)",
  },
  "upload.age": { en: "Age", fr: "Âge", ar: "العمر" },
  "upload.gender": { en: "Gender", fr: "Genre", ar: "الجنس" },
  "upload.genderMale": { en: "Male", fr: "Homme", ar: "ذكر" },
  "upload.genderFemale": { en: "Female", fr: "Femme", ar: "أنثى" },
  "upload.symptoms": { en: "Symptoms", fr: "Symptômes", ar: "الأعراض" },
  "upload.symptomsPlaceholder": {
    en: "e.g. fatigue, headache…",
    fr: "p.ex. fatigue, maux de tête…",
    ar: "مثال: إرهاق، صداع…",
  },
  "upload.helperText": {
    en: "Providing context helps improve explanations. Optional.",
    fr: "Fournir du contexte améliore les explications. Facultatif.",
    ar: "تقديم سياق يساعد في تحسين الشرح. اختياري.",
  },
  "upload.analyze": {
    en: "Analyze report",
    fr: "Analyser le rapport",
    ar: "تحليل التقرير",
  },

  // Processing
  "processing.step1": {
    en: "Reading your document",
    fr: "Lecture de votre document",
    ar: "جاري قراءة مستندك",
  },
  "processing.step2": {
    en: "Understanding values",
    fr: "Compréhension des valeurs",
    ar: "جاري فهم القيم",
  },
  "processing.step3": {
    en: "Preparing explanation",
    fr: "Préparation de l'explication",
    ar: "جاري تحضير الشرح",
  },

  // Results
  "results.summaryHeadline": {
    en: "Here's a simple summary of your results",
    fr: "Voici un résumé simple de vos résultats",
    ar: "إليك ملخص بسيط لنتائجك",
  },
  "results.normal": {
    en: "Mostly within normal range",
    fr: "Principalement dans la plage normale",
    ar: "ضمن النطاق الطبيعي غالبًا",
  },
  "results.monitor": {
    en: "Some values to monitor",
    fr: "Quelques valeurs à surveiller",
    ar: "بعض القيم تحتاج متابعة",
  },
  "results.review": {
    en: "Important values to review with a doctor",
    fr: "Valeurs importantes à revoir avec un médecin",
    ar: "قيم مهمة يجب مراجعتها مع طبيب",
  },
  "results.whatThisMeans": {
    en: "What this means",
    fr: "Ce que cela signifie",
    ar: "ماذا يعني هذا",
  },
  "results.normalRange": {
    en: "Normal range",
    fr: "Plage normale",
    ar: "النطاق الطبيعي",
  },

  // Footer
  "footer.disclaimer": {
    en: "TahalilAI does not provide medical diagnoses. This information is educational only.",
    fr: "TahalilAI ne fournit pas de diagnostics médicaux. Ces informations sont uniquement éducatives.",
    ar: "تحاليلAI لا تقدم تشخيصات طبية. هذه المعلومات تعليمية فقط.",
  },
  "footer.privacy": {
    en: "Uploaded files are automatically deleted.",
    fr: "Les fichiers téléchargés sont automatiquement supprimés.",
    ar: "يتم حذف الملفات المرفوعة تلقائيًا.",
  },
};

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
  dir: "ltr" | "rtl";
}

const LanguageContext = createContext<LanguageContextType | undefined>(
  undefined
);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>("en");

  const t = (key: string): string => {
    return translations[key]?.[language] ?? key;
  };

  const dir = language === "ar" ? "rtl" : "ltr";

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, dir }}>
      <div dir={dir}>{children}</div>
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
}
