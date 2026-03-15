"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";

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

  // Doctors
  "doctors.title": {
    en: "Find a Doctor",
    fr: "Trouver un M\u00e9decin",
    ar: "\u0627\u0628\u062d\u062b \u0639\u0646 \u0637\u0628\u064a\u0628",
  },
  "doctors.search": {
    en: "Search by name...",
    fr: "Rechercher par nom...",
    ar: "...\u0627\u0628\u062d\u062b \u0628\u0627\u0644\u0627\u0633\u0645",
  },
  "doctors.allCities": {
    en: "All Cities",
    fr: "Toutes les villes",
    ar: "\u062c\u0645\u064a\u0639 \u0627\u0644\u0645\u062f\u0646",
  },
  "doctors.allSpecialities": {
    en: "All Specialities",
    fr: "Toutes les sp\u00e9cialit\u00e9s",
    ar: "\u062c\u0645\u064a\u0639 \u0627\u0644\u062a\u062e\u0635\u0635\u0627\u062a",
  },
  "doctors.noResults": {
    en: "No doctors found",
    fr: "Aucun m\u00e9decin trouv\u00e9",
    ar: "\u0644\u0645 \u064a\u062a\u0645 \u0627\u0644\u0639\u062b\u0648\u0631 \u0639\u0644\u0649 \u0623\u0637\u0628\u0627\u0621",
  },
  "doctors.clearFilters": {
    en: "Clear filters",
    fr: "Effacer les filtres",
    ar: "\u0645\u0633\u062d \u0627\u0644\u0641\u0644\u0627\u062a\u0631",
  },
  "doctors.doctorsFound": {
    en: "doctors found",
    fr: "m\u00e9decins trouv\u00e9s",
    ar: "\u0637\u0628\u064a\u0628",
  },
  "doctors.nav": {
    en: "Find a Doctor",
    fr: "Trouver un M\u00e9decin",
    ar: "\u0627\u0628\u062d\u062b \u0639\u0646 \u0637\u0628\u064a\u0628",
  },
  "upload.city": {
    en: "City",
    fr: "Ville",
    ar: "\u0627\u0644\u0645\u062f\u064a\u0646\u0629",
  },
  "upload.cityPlaceholder": {
    en: "Select your city (for doctor recommendations)",
    fr: "S\u00e9lectionnez votre ville (pour recommandations)",
    ar: "\u0627\u062e\u062a\u0631 \u0645\u062f\u064a\u0646\u062a\u0643 (\u0644\u0644\u062a\u0648\u0635\u064a\u0627\u062a)",
  },

  // Privacy banner
  "privacy.title": {
    en: "Your file is processed securely.",
    fr: "Votre fichier est traité en toute sécurité.",
    ar: "يتم معالجة ملفك بأمان تام.",
  },
  "privacy.body": {
    en: "It is never stored permanently and is automatically deleted after analysis.",
    fr: "Il n'est jamais stocké de façon permanente et est automatiquement supprimé après l'analyse.",
    ar: "لا يتم تخزينه بشكل دائم ويُحذف تلقائيًا بعد التحليل.",
  },

  // Optional fields toggle
  "upload.optionalToggle": {
    en: "Add optional details to improve accuracy",
    fr: "Ajouter des détails optionnels pour améliorer la précision",
    ar: "أضف تفاصيل اختيارية لتحسين الدقة",
  },

  // Urgency banners
  "urgency.urgent.heading": {
    en: "Important: Attention Required",
    fr: "Important : Attention requise",
    ar: "مهم: يستوجب الانتباه",
  },
  "urgency.urgent.body": {
    en: "Some values in your report fall outside the normal range and may require prompt medical attention. Please consult a doctor before drawing any conclusions.",
    fr: "Certaines valeurs dans votre rapport se situent hors de la plage normale et peuvent nécessiter une attention médicale rapide. Veuillez consulter un médecin avant de tirer des conclusions.",
    ar: "بعض القيم في تقريرك تقع خارج النطاق الطبيعي وقد تستدعي الاهتمام الطبي العاجل. يُرجى استشارة الطبيب قبل استخلاص أي استنتاجات.",
  },
  "urgency.soon.heading": {
    en: "Follow-up Recommended",
    fr: "Suivi recommandé",
    ar: "يُنصح بالمتابعة",
  },
  "urgency.soon.body": {
    en: "A few values in your report are worth discussing with your doctor at your next visit.",
    fr: "Quelques valeurs dans votre rapport méritent d'être discutées avec votre médecin lors de votre prochaine visite.",
    ar: "بعض القيم في تقريرك تستحق المناقشة مع طبيبك في زيارتك القادمة.",
  },

  // Next steps card
  "nextsteps.heading": {
    en: "What to do next",
    fr: "Que faire maintenant",
    ar: "ماذا تفعل بعد ذلك",
  },
  "nextsteps.urgent.1": {
    en: "Read the full analysis below carefully.",
    fr: "Lisez attentivement l'analyse complète ci-dessous.",
    ar: "اقرأ التحليل الكامل أدناه بعناية.",
  },
  "nextsteps.urgent.2": {
    en: "Consult a doctor as soon as possible.",
    fr: "Consultez un médecin dès que possible.",
    ar: "استشر طبيبًا في أقرب وقت ممكن.",
  },
  "nextsteps.urgent.3": {
    en: "Download and bring the PDF report to your appointment.",
    fr: "Téléchargez et apportez le rapport PDF à votre rendez-vous.",
    ar: "حمّل تقرير PDF وأحضره إلى موعدك.",
  },
  "nextsteps.urgent.4": {
    en: "Do not self-medicate based on this analysis.",
    fr: "Ne vous automédiquiez pas sur la base de cette analyse.",
    ar: "لا تعالج نفسك بناءً على هذا التحليل.",
  },
  "nextsteps.soon.1": {
    en: "Read the full analysis below.",
    fr: "Lisez l'analyse complète ci-dessous.",
    ar: "اقرأ التحليل الكامل أدناه.",
  },
  "nextsteps.soon.2": {
    en: "Note which values are flagged for discussion.",
    fr: "Notez les valeurs signalées pour discussion.",
    ar: "لاحظ القيم التي تم الإشارة إليها للمناقشة.",
  },
  "nextsteps.soon.3": {
    en: "Schedule a non-urgent appointment with your doctor.",
    fr: "Prenez un rendez-vous non urgent avec votre médecin.",
    ar: "احجز موعدًا غير عاجل مع طبيبك.",
  },
  "nextsteps.soon.4": {
    en: "Use the AI assistant below if you have questions.",
    fr: "Utilisez l'assistant IA ci-dessous si vous avez des questions.",
    ar: "استخدم المساعد الذكي أدناه إذا كان لديك أسئلة.",
  },
  "nextsteps.routine.1": {
    en: "Read your results below.",
    fr: "Lisez vos résultats ci-dessous.",
    ar: "اقرأ نتائجك أدناه.",
  },
  "nextsteps.routine.2": {
    en: "Keep this report for your records.",
    fr: "Conservez ce rapport pour vos dossiers.",
    ar: "احتفظ بهذا التقرير لسجلاتك.",
  },
  "nextsteps.routine.3": {
    en: "Discuss at your next routine check-up.",
    fr: "Discutez-en lors de votre prochain bilan de santé.",
    ar: "ناقشه في فحصك الدوري القادم.",
  },

  // Report collapse toggle
  "results.readFull": {
    en: "Read full analysis",
    fr: "Lire l'analyse complète",
    ar: "اقرأ التحليل الكامل",
  },
  "results.collapse": {
    en: "Collapse report",
    fr: "Réduire le rapport",
    ar: "طي التقرير",
  },

  // Chat toggle
  "chat.open": {
    en: "Ask a question about your results",
    fr: "Posez une question sur vos résultats",
    ar: "اطرح سؤالاً حول نتائجك",
  },

  // Header nav
  "header.home": { en: "Home", fr: "Accueil", ar: "الرئيسية" },

  // Hero extras
  "hero.findSpecialist": { en: "Find a specialist", fr: "Trouver un spécialiste", ar: "ابحث عن متخصص" },
  "hero.trust2": { en: "Results in under 60 seconds", fr: "Résultats en moins de 60 secondes", ar: "النتائج في أقل من 60 ثانية" },
  "hero.badge.uploaded": { en: "Report uploaded", fr: "Rapport téléchargé", ar: "تم رفع التقرير" },
  "hero.badge.ready": { en: "Explanation ready", fr: "Explication prête", ar: "الشرح جاهز" },

  // Hero process card
  "hero.card.label": { en: "How it works", fr: "Comment ça fonctionne", ar: "كيف يعمل" },
  "hero.card.title": { en: "Three steps to clarity", fr: "Trois étapes vers la clarté", ar: "ثلاث خطوات نحو الوضوح" },
  "hero.step1.label": { en: "Upload your lab report", fr: "Téléchargez votre rapport", ar: "ارفع تقرير مختبرك" },
  "hero.step1.sub": { en: "PDF or image, any format", fr: "PDF ou image, tout format", ar: "PDF أو صورة، أي تنسيق" },
  "hero.step2.label": { en: "AI reads every value", fr: "L'IA lit chaque valeur", ar: "الذكاء الاصطناعي يقرأ كل قيمة" },
  "hero.step2.sub": { en: "OCR + clinical knowledge", fr: "OCR + connaissances cliniques", ar: "تقنية OCR + معرفة سريرية" },
  "hero.step3.label": { en: "Get a plain-language report", fr: "Obtenez un rapport clair", ar: "احصل على تقرير بلغة بسيطة" },
  "hero.step3.sub": { en: "PDF · Audio · Arabic", fr: "PDF · Audio · Arabe", ar: "PDF · صوت · عربي" },
  "hero.card.footer": {
    en: "Files are deleted immediately after analysis",
    fr: "Les fichiers sont supprimés immédiatement après l'analyse",
    ar: "يتم حذف الملفات فور الانتهاء من التحليل",
  },

  // Stats strip
  "stats.languages.label": { en: "Languages supported", fr: "Langues prises en charge", ar: "لغات مدعومة" },
  "stats.languages.note": { en: "AR · FR · EN", fr: "AR · FR · EN", ar: "عربي · فرنسي · إنجليزي" },
  "stats.time.label": { en: "Average analysis time", fr: "Temps d'analyse moyen", ar: "متوسط وقت التحليل" },
  "stats.time.note": { en: "From upload to report", fr: "De l'envoi au rapport", ar: "من الرفع حتى التقرير" },
  "stats.privacy.label": { en: "Deleted after analysis", fr: "Supprimés après analyse", ar: "محذوفة بعد التحليل" },
  "stats.privacy.note": { en: "No files stored", fr: "Aucun fichier stocké", ar: "لا يتم تخزين الملفات" },

  // How it works section
  "hiw.label": { en: "How it works", fr: "Comment ça fonctionne", ar: "كيف يعمل" },
  "hiw.heading": { en: "From document to understanding.", fr: "Du document à la compréhension.", ar: "من المستند إلى الفهم." },
  "hiw.body": {
    en: "Upload your report once, and the AI takes care of the rest — in plain language, in your language.",
    fr: "Téléchargez votre rapport une fois, et l'IA s'occupe du reste — en langage simple, dans votre langue.",
    ar: "ارفع تقريرك مرة واحدة، والذكاء الاصطناعي يتولى الباقي — بلغة بسيطة، بلغتك.",
  },
  "hiw.step1.title": { en: "Upload your report", fr: "Téléchargez votre rapport", ar: "ارفع تقريرك" },
  "hiw.step1.desc": {
    en: "Drop a PDF or photo of your lab results. Blood work, imaging reports, clinic printouts — we handle any format.",
    fr: "Déposez un PDF ou une photo de vos résultats. Analyses sanguines, rapports d'imagerie, imprimés de clinique — nous gérons tout format.",
    ar: "أسقط ملف PDF أو صورة من نتائج مختبرك. تحاليل الدم، تقارير التصوير، مطبوعات العيادات — نتعامل مع أي تنسيق.",
  },
  "hiw.step2.title": { en: "AI reads every value", fr: "L'IA lit chaque valeur", ar: "الذكاء الاصطناعي يقرأ كل قيمة" },
  "hiw.step2.desc": {
    en: "Our model extracts each test result using OCR, identifies what's flagged, and cross-references clinical reference ranges.",
    fr: "Notre modèle extrait chaque résultat d'analyse par OCR, identifie ce qui est signalé et le compare aux plages de référence cliniques.",
    ar: "يستخرج نموذجنا كل نتيجة اختبار باستخدام تقنية OCR، ويحدد ما تم الإشارة إليه، ويقارنه بالنطاقات المرجعية السريرية.",
  },
  "hiw.step3.title": { en: "Get a plain-language report", fr: "Obtenez un rapport en langage simple", ar: "احصل على تقرير بلغة بسيطة" },
  "hiw.step3.desc": {
    en: "Receive a structured report with flagged values explained in plain language. Download a PDF, listen to an audio summary, or ask follow-up questions.",
    fr: "Recevez un rapport structuré avec les valeurs signalées expliquées en langage simple. Téléchargez un PDF, écoutez un résumé audio ou posez des questions.",
    ar: "احصل على تقرير منظم مع شرح القيم المُشار إليها بلغة بسيطة. حمّل ملف PDF، استمع لملخص صوتي، أو اطرح أسئلة متابعة.",
  },
  "hiw.step4.title": { en: "Find a specialist near you", fr: "Trouvez un spécialiste près de vous", ar: "ابحث عن متخصص قريب منك" },
  "hiw.step4.desc": {
    en: "Based on your results, we suggest relevant specialists from our database of doctors across Morocco, with ratings and contact details.",
    fr: "Sur la base de vos résultats, nous suggérons des spécialistes pertinents depuis notre base de médecins au Maroc, avec notes et coordonnées.",
    ar: "بناءً على نتائجك، نقترح متخصصين مناسبين من قاعدة بيانات الأطباء عبر المغرب، مع التقييمات وتفاصيل الاتصال.",
  },

  // Features grid
  "features.label": { en: "What you get", fr: "Ce que vous obtenez", ar: "ما ستحصل عليه" },
  "features.heading1": { en: "Every tool you need.", fr: "Tous les outils dont vous avez besoin.", ar: "كل الأدوات التي تحتاجها." },
  "features.heading2": { en: "Nothing you don't.", fr: "Rien de plus.", ar: "لا شيء زائد." },
  "feat.ai.title": { en: "AI-powered report analysis", fr: "Analyse de rapport par IA", ar: "تحليل التقرير بالذكاء الاصطناعي" },
  "feat.ai.desc": {
    en: "Our model reads your full lab report, identifies abnormal values, explains what they mean in plain language, and provides context based on your age and gender. No copy-paste needed — it works directly from your file.",
    fr: "Notre modèle lit votre rapport complet, identifie les valeurs anormales, explique leur signification en langage simple et fournit un contexte selon votre âge et sexe. Sans copier-coller — il travaille directement depuis votre fichier.",
    ar: "يقرأ نموذجنا تقريرك الكامل، يحدد القيم غير الطبيعية، يشرح معناها بلغة بسيطة، ويقدم سياقًا بناءً على عمرك وجنسك. لا حاجة للنسخ واللصق — يعمل مباشرة من ملفك.",
  },
  "feat.audio.title": { en: "Audio summary", fr: "Résumé audio", ar: "ملخص صوتي" },
  "feat.audio.desc": {
    en: "Listen to your report read aloud. Helpful for patients who prefer audio or are sharing results with family.",
    fr: "Écoutez votre rapport lu à voix haute. Utile pour les patients qui préfèrent l'audio ou partagent les résultats avec leur famille.",
    ar: "استمع لتقريرك يُقرأ بصوت عالٍ. مفيد للمرضى الذين يفضلون الصوت أو يشاركون النتائج مع الأسرة.",
  },
  "feat.arabic.title": { en: "Arabic translation", fr: "Traduction arabe", ar: "ترجمة عربية" },
  "feat.arabic.desc": {
    en: "One-click translation to Arabic — with a separate downloadable PDF in RTL format, right-to-left.",
    fr: "Traduction en un clic vers l'arabe — avec un PDF téléchargeable séparé au format RTL, de droite à gauche.",
    ar: "ترجمة بنقرة واحدة إلى العربية — مع ملف PDF قابل للتحميل بتنسيق من اليمين إلى اليسار.",
  },
  "feat.chat.title": { en: "Ask follow-up questions", fr: "Posez des questions", ar: "اطرح أسئلة متابعة" },
  "feat.chat.desc": {
    en: "After reading your report, the AI stays available. Ask anything — \"what does this mean?\", \"should I be worried?\"",
    fr: "Après lecture du rapport, l'IA reste disponible. Posez n'importe quelle question — \"que signifie ceci ?\", \"dois-je m'inquiéter ?\"",
    ar: "بعد قراءة تقريرك، يبقى الذكاء الاصطناعي متاحًا. اسأل أي شيء — \"ماذا يعني هذا؟\"، \"هل يجب أن أقلق؟\"",
  },
  "feat.doctors.title": { en: "Nearby specialist recommendations", fr: "Recommandations de spécialistes", ar: "توصيات بمتخصصين قريبين" },
  "feat.doctors.desc": {
    en: "Based on your flagged values, we suggest the right type of doctor and show rated specialists near your city.",
    fr: "Sur la base de vos valeurs signalées, nous suggérons le bon type de médecin et affichons des spécialistes bien notés près de votre ville.",
    ar: "بناءً على قيمك المُشار إليها، نقترح النوع المناسب من الأطباء ونعرض متخصصين بتقييمات جيدة قرب مدينتك.",
  },
  "feat.pdf.title": { en: "Download PDF report", fr: "Télécharger le rapport PDF", ar: "تحميل تقرير PDF" },
  "feat.pdf.desc": {
    en: "Save and share your AI-generated explanation as a professionally formatted PDF — available in English and Arabic.",
    fr: "Sauvegardez et partagez votre explication générée par IA sous forme de PDF formaté professionnellement — disponible en anglais et arabe.",
    ar: "احفظ وشارك شرح الذكاء الاصطناعي كملف PDF منسق باحترافية — متاح بالإنجليزية والعربية.",
  },

  // Disclaimer
  "disclaimer.title": {
    en: "Not a substitute for medical advice",
    fr: "Pas un substitut aux avis médicaux",
    ar: "ليس بديلاً عن المشورة الطبية",
  },
  "disclaimer.body": {
    en: "TahalilAI explains what your lab values mean — it does not diagnose, treat, or prescribe. This tool is designed to help you understand your results and prepare for a conversation with your doctor, not to replace one. Always consult a licensed healthcare professional.",
    fr: "TahalilAI explique la signification de vos valeurs de laboratoire — il ne diagnostique pas, ne traite pas et ne prescrit pas. Cet outil est conçu pour vous aider à comprendre vos résultats et préparer une conversation avec votre médecin, pas pour le remplacer. Consultez toujours un professionnel de santé agréé.",
    ar: "تحاليلAI يشرح معنى قيم مختبرك — لا يشخّص ولا يعالج ولا يصف. هذه الأداة مصممة لمساعدتك على فهم نتائجك والاستعداد للحديث مع طبيبك، وليس لاستبداله. استشر دائمًا مختصًا طبيًا مرخصًا.",
  },

  // Trust strip
  "trust.noAccount.title": { en: "No account required", fr: "Sans inscription", ar: "لا حاجة لحساب" },
  "trust.noAccount.body": {
    en: "Just upload and get your results. No sign-up, no email.",
    fr: "Téléchargez simplement et obtenez vos résultats. Sans inscription, sans email.",
    ar: "فقط ارفع واحصل على نتائجك. لا تسجيل، لا بريد إلكتروني.",
  },
  "trust.deleted.title": { en: "Files deleted instantly", fr: "Fichiers supprimés instantanément", ar: "الملفات تُحذف فورًا" },
  "trust.deleted.body": {
    en: "Your document is removed from our servers right after analysis.",
    fr: "Votre document est supprimé de nos serveurs juste après l'analyse.",
    ar: "يُزال مستندك من خوادمنا مباشرة بعد التحليل.",
  },
  "trust.multilang.title": { en: "Arabic & French ready", fr: "Arabe et français disponibles", ar: "العربية والفرنسية متاحتان" },
  "trust.multilang.body": {
    en: "Get your explanation in the language you're most comfortable with.",
    fr: "Obtenez votre explication dans la langue qui vous convient le mieux.",
    ar: "احصل على شرحك باللغة التي تشعر بارتياح أكبر معها.",
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

  // Hospitals
  "hospitals.nav": { en: "Hospitals", fr: "Hôpitaux", ar: "المستشفيات" },
  "hospitals.title": { en: "Public Health Facilities", fr: "Établissements de Santé Publics", ar: "المرافق الصحية العمومية" },
  "hospitals.subtitle": {
    en: "Find public hospitals and primary care centres across Morocco",
    fr: "Trouvez des hôpitaux publics et centres de santé primaires au Maroc",
    ar: "اعثور على المستشفيات العمومية ومراكز الرعاية الصحية الأولية عبر المغرب",
  },
  "hospitals.search": { en: "Search by name, department...", fr: "Rechercher par nom, département...", ar: "ابحث بالاسم أو التخصص..." },
  "hospitals.allRegions": { en: "All Regions", fr: "Toutes les régions", ar: "جميع الجهات" },
  "hospitals.allTypes": { en: "All Types", fr: "Tous les types", ar: "جميع الأنواع" },
  "hospitals.typeHopital": { en: "Hospital", fr: "Hôpital", ar: "مستشفى" },
  "hospitals.typePrimary": { en: "Primary Care", fr: "Soins primaires", ar: "رعاية أولية" },
  "hospitals.noResults": { en: "No facilities found", fr: "Aucun établissement trouvé", ar: "لم يتم العثور على مرافق" },
  "hospitals.clearFilters": { en: "Clear filters", fr: "Effacer les filtres", ar: "مسح الفلاتر" },
  "hospitals.found": { en: "facilities found", fr: "établissements trouvés", ar: "مرفق" },
  "hospitals.region": { en: "Region", fr: "Région", ar: "الجهة" },
  "hospitals.delegation": { en: "Province", fr: "Délégation", ar: "العمالة" },
  "hospitals.departments": { en: "Departments", fr: "Départements", ar: "الأقسام" },
  "hospitals.recommended.title": { en: "Nearby Public Hospitals", fr: "Hôpitaux Publics Proches", ar: "مستشفيات عمومية قريبة" },
  "hospitals.recommended.subtitle": { en: "Free public facilities near you based on your results", fr: "Établissements publics gratuits près de vous selon vos résultats", ar: "مرافق عمومية مجانية بالقرب منك بناءً على نتائجك" },
  "hospitals.free": { en: "Free public", fr: "Public gratuit", ar: "مجاني" },
  "hospitals.viewAll": { en: "View all hospitals", fr: "Voir tous les hôpitaux", ar: "عرض جميع المستشفيات" },

  // Results — language-aware translation buttons
  "results.showEnglish": { en: "Show in English", fr: "Voir en anglais", ar: "عرض بالإنجليزية" },
  "results.translateToArabic": { en: "Translate to Arabic", fr: "Traduire en arabe", ar: "ترجمة إلى العربية" },
  "results.translateToFrench": { en: "Translate to French", fr: "Traduire en français", ar: "ترجمة إلى الفرنسية" },
  "results.translating": { en: "Translating…", fr: "Traduction en cours…", ar: "جارٍ الترجمة…" },
  "results.tab.english": { en: "English", fr: "Anglais", ar: "الإنجليزية" },
  "results.tab.arabic": { en: "Arabic", fr: "Arabe", ar: "العربية" },
  "results.tab.french": { en: "French", fr: "Français", ar: "الفرنسية" },

  // Doctor / Hospital cards
  "card.call":       { en: "Call",       fr: "Appeler",    ar: "اتصل" },
  "card.directions": { en: "Directions", fr: "Itinéraire", ar: "الاتجاهات" },

  // Upload — translation step
  "upload.translatingStep": {
    en: "Translating to your language…",
    fr: "Traduction en cours…",
    ar: "جارٍ الترجمة إلى لغتك…",
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
  const [language, setLanguage] = useState<Language>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("tahalilai_lang");
      if (saved === "en" || saved === "fr" || saved === "ar") return saved;
    }
    return "en";
  });

  const handleSetLanguage = (lang: Language) => {
    setLanguage(lang);
    if (typeof window !== "undefined") {
      localStorage.setItem("tahalilai_lang", lang);
    }
  };

  const t = (key: string): string => {
    return translations[key]?.[language] ?? key;
  };

  const dir = language === "ar" ? "rtl" : "ltr";

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = dir;
  }, [language, dir]);

  return (
    <LanguageContext.Provider value={{ language, setLanguage: handleSetLanguage, t, dir }}>
      <div dir={dir}>{children}</div>
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
}
