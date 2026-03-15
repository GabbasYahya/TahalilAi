"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { RecommendedDoctors } from "@/components/RecommendedDoctors";
import { RecommendedHospitals } from "@/components/RecommendedHospitals";
import { InlineError } from "@/components/InlineError";
import { UrgencyBanner } from "@/components/UrgencyBanner";
import { NextStepsCard } from "@/components/NextStepsCard";
import { StatusBadge } from "@/components/StatusBadge";
import { BiomarkerTable } from "@/components/BiomarkerTable";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface RecommendedDoctor {
    id: number;
    title: string;
    name: string;
    speciality: string;
    phone: string;
    address: string;
    city: string;
    image_url: string;
    profile_url: string;
}

interface RecommendedHospital {
    id: number;
    name: string;
    category_code: string;
    category_name: string;
    facility_type: string;
    region: string;
    delegation: string;
    commune: string;
    departments: string;
    phone: string;
    address: string;
}

interface BiomarkerResult {
    marker_name: string;
    measured_value: string;
    reference_range: string;
    status: string;
    clinical_significance: string;
}

interface AbnormalFindingResult {
    marker: string;
    issue: string;
    possible_meanings: string[];
    recommended_followup_tests: string[];
}

interface StructuredAnalysisData {
    report_summary: {
        overall_status: string;
        short_explanation: string;
        confidence_level: string;
    };
    patient_context: {
        gender_inferred: string;
        age_group_inferred: string;
        inference_confidence: string;
    };
    biomarker_analysis: BiomarkerResult[];
    abnormal_findings: AbnormalFindingResult[];
    recommended_specialties: { specialty: string; reason: string }[];
    health_recommendations: string[];
    missing_information: {
        needs_age: boolean;
        needs_gender: boolean;
        additional_questions: string[];
    };
    system_feedback: string[];
}

interface AnalysisData {
    job_id?: string;
    text: string;
    structured_analysis?: StructuredAnalysisData | null;
    audioUrl?: string;
    pdfUrl?: string;
    timestamp: number;
    recommended_specialities?: string[];
    urgency?: string;
    recommended_doctors?: RecommendedDoctor[];
    recommended_hospitals?: RecommendedHospital[];
}

interface TranslationData {
    lang: "ar" | "fr";
    text: string;
    pdfUrl?: string;
}

export default function ResultsPage() {
    const { t, language } = useLanguage();
    const router = useRouter();

    const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
    const [activeTab, setActiveTab] = useState<"english" | "ar" | "fr">("english");
    const [translationData, setTranslationData] = useState<TranslationData | null>(null);
    const [translating, setTranslating] = useState(false);
    const [audioState, setAudioState] = useState<"idle" | "generating" | "ready">("idle");
    const [audioUrl, setAudioUrl] = useState<string | null>(null);

    // UX state
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [reportExpanded, setReportExpanded] = useState(false);
    const [chatOpen, setChatOpen] = useState(false);

    // ── Chat state ──────────────────────────────────────────────────────
    type ChatMessage = { role: "user" | "assistant"; content: string };
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [chatInput, setChatInput] = useState("");
    const [chatLoading, setChatLoading] = useState(false);
    const chatBottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const stored = localStorage.getItem("analysisResult");
        if (!stored) { router.push("/upload"); return; }
        const data: AnalysisData = JSON.parse(stored);
        if (!data.text) { router.push("/upload"); return; }
        setAnalysisData(data);
        if (data.audioUrl) {
            setAudioUrl(`${API_URL}${data.audioUrl}`);
            setAudioState("ready");
        }
        // Load auto-translated result (set by upload page for AR/FR users)
        const storedTranslation = localStorage.getItem("analysisTranslation");
        if (storedTranslation) {
            try {
                const tr: TranslationData = JSON.parse(storedTranslation);
                setTranslationData(tr);
                setActiveTab(tr.lang);
            } catch {
                // ignore parse errors
            }
        }
    }, [router]);

    const handleListenClick = useCallback(async () => {
        if (!analysisData?.job_id) return;
        if (audioState === "ready") return;
        if (audioState === "generating") return;

        setErrorMessage(null);
        setAudioState("generating");

        try {
            const res = await fetch(`${API_URL}/generate-audio`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ job_id: analysisData.job_id })
            });
            const json = await res.json();

            if (json.status === "completed" && json.audio_url) {
                setAudioUrl(`${API_URL}${json.audio_url}`);
                setAudioState("ready");
                const newData = { ...analysisData, audioUrl: json.audio_url };
                setAnalysisData(newData);
                localStorage.setItem("analysisResult", JSON.stringify(newData));
                return;
            }

            const pollAudio = setInterval(async () => {
                try {
                    const statusRes = await fetch(`${API_URL}/audio-status/${analysisData.job_id}`);
                    const statusJson = await statusRes.json();

                    if (statusJson.status === "completed" && statusJson.audio_url) {
                        clearInterval(pollAudio);
                        setAudioUrl(`${API_URL}${statusJson.audio_url}`);
                        setAudioState("ready");
                        const newData = { ...analysisData, audioUrl: statusJson.audio_url };
                        setAnalysisData(newData);
                        localStorage.setItem("analysisResult", JSON.stringify(newData));
                    } else if (statusJson.status === "failed") {
                        clearInterval(pollAudio);
                        setAudioState("idle");
                        setErrorMessage("Audio generation failed. Please try again.");
                    }
                } catch {
                    // Keep polling on transient errors
                }
            }, 2000);

            setTimeout(() => {
                clearInterval(pollAudio);
                setAudioState((prev) => prev === "generating" ? "idle" : prev);
            }, 300000);

        } catch {
            setAudioState("idle");
            setErrorMessage("Audio service is temporarily unavailable.");
        }
    }, [analysisData, audioState]);

    const handleTranslate = async (targetLang: "ar" | "fr") => {
        if (!analysisData) return;

        // Already have translation for this language — just switch tab
        if (translationData?.lang === targetLang) {
            setActiveTab(targetLang);
            return;
        }

        if (!analysisData.job_id) {
            setErrorMessage("Unable to translate this report. Please analyze a new document.");
            return;
        }

        setErrorMessage(null);
        setTranslating(true);
        try {
            const res = await fetch(`${API_URL}/translate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    text: analysisData.text,
                    job_id: analysisData.job_id,
                    target_lang: targetLang,
                })
            });

            const json = await res.json();
            if (json.status === "success") {
                const tr: TranslationData = {
                    lang: targetLang,
                    text: json.translated_text,
                    pdfUrl: json.translated_pdf_url ?? undefined,
                };
                setTranslationData(tr);
                localStorage.setItem("analysisTranslation", JSON.stringify(tr));
                setActiveTab(targetLang);
            } else {
                setErrorMessage("Translation is temporarily unavailable. Please try again later.");
            }
        } catch {
            setErrorMessage("Could not reach the translation service.");
        } finally {
            setTranslating(false);
        }
    };

    const handleDownloadPDF = () => {
        const url = (activeTab !== "english" && translationData?.pdfUrl)
            ? translationData.pdfUrl
            : analysisData?.pdfUrl;
        if (!url) return;
        window.open(`${API_URL}${url}`, "_blank");
    };

    const handleNewAnalysis = () => {
        localStorage.removeItem("analysisResult");
        localStorage.removeItem("analysisTranslation");
        router.push("/upload");
    };

    // ── Chat handlers ───────────────────────────────────────────────────
    useEffect(() => {
        chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [chatMessages, chatLoading]);

    const handleChatSubmit = useCallback(async () => {
        if (!chatInput.trim() || !analysisData?.job_id || chatLoading) return;
        const question = chatInput.trim();
        setChatInput("");
        setChatMessages(prev => [...prev, { role: "user", content: question }]);
        setChatLoading(true);
        try {
            const res = await fetch(`${API_URL}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ job_id: analysisData.job_id, message: question }),
            });
            const json = await res.json();
            const answer = json.answer || "Sorry, I could not generate a response. Please try again.";
            setChatMessages(prev => [...prev, { role: "assistant", content: answer }]);
        } catch {
            setChatMessages(prev => [
                ...prev,
                { role: "assistant", content: "Could not reach the AI service. Please check your connection." },
            ]);
        } finally {
            setChatLoading(false);
        }
    }, [chatInput, analysisData, chatLoading]);

    if (!analysisData) return null;

    const isTranslated = activeTab !== "english";
    const content = isTranslated ? (translationData?.text || "") : analysisData.text;
    const structured = !isTranslated ? (analysisData.structured_analysis ?? null) : null;
    const urgency = analysisData.urgency || "routine";
    const hasDoctors = (analysisData.recommended_doctors?.length ?? 0) > 0;
    const hasHospitals = (analysisData.recommended_hospitals?.length ?? 0) > 0;

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 dark:from-slate-900 via-primary-50/20 dark:via-slate-900 to-primary-50/30 dark:to-slate-900 px-4 py-8">
            <div className="mx-auto max-w-4xl space-y-6">

                {/* ─── Top Bar ─── */}
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <Link href="/upload" className="group flex items-center gap-2 text-sm font-medium text-slate-500 dark:text-slate-400 hover:text-primary-600 transition-colors">
                        <svg className="h-4 w-4 transition-transform group-hover:-translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                        </svg>
                        New Analysis
                    </Link>

                    <div className="flex items-center gap-2">
                        {/* Download PDF */}
                        {(analysisData.pdfUrl || translationData?.pdfUrl) && (
                            <button
                                onClick={handleDownloadPDF}
                                className="flex items-center gap-2 rounded-xl bg-white dark:bg-slate-800 px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 shadow-sm ring-1 ring-slate-200 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
                            >
                                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                {activeTab === "ar" ? "تحميل PDF" : "Download PDF"}
                            </button>
                        )}

                        {/* Translate Toggle */}
                        {isTranslated ? (
                            // Viewing translated content → "Show in English" button
                            <button
                                onClick={() => setActiveTab("english")}
                                className="flex items-center gap-2 rounded-xl bg-white dark:bg-slate-800 px-4 py-2 text-sm font-semibold text-slate-700 dark:text-slate-300 ring-1 ring-slate-200 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
                            >
                                {t("results.showEnglish")}
                            </button>
                        ) : language === "en" ? (
                            // English site → two side-by-side translate buttons
                            <>
                                <button
                                    onClick={() => handleTranslate("ar")}
                                    disabled={translating}
                                    className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-all ${
                                        translating
                                        ? "bg-slate-100 dark:bg-slate-700 text-slate-400 dark:text-slate-500 cursor-wait"
                                        : "bg-primary-600 text-white hover:bg-primary-700 shadow-sm shadow-primary-200"
                                    }`}
                                >
                                    {translating ? (
                                        <>
                                            <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                            </svg>
                                            {t("results.translating")}
                                        </>
                                    ) : t("results.translateToArabic")}
                                </button>
                                <button
                                    onClick={() => handleTranslate("fr")}
                                    disabled={translating}
                                    className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-all ${
                                        translating
                                        ? "bg-slate-100 dark:bg-slate-700 text-slate-400 dark:text-slate-500 cursor-wait"
                                        : "bg-primary-600 text-white hover:bg-primary-700 shadow-sm shadow-primary-200"
                                    }`}
                                >
                                    {translating ? t("results.translating") : t("results.translateToFrench")}
                                </button>
                            </>
                        ) : (
                            // Arabic/French site viewing English → one translate button for their language
                            <button
                                onClick={() => handleTranslate(language as "ar" | "fr")}
                                disabled={translating}
                                className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-all ${
                                    translating
                                    ? "bg-slate-100 dark:bg-slate-700 text-slate-400 dark:text-slate-500 cursor-wait"
                                    : "bg-primary-600 text-white hover:bg-primary-700 shadow-sm shadow-primary-200"
                                }`}
                            >
                                {translating ? (
                                    <>
                                        <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                        </svg>
                                        {t("results.translating")}
                                    </>
                                ) : language === "ar" ? t("results.translateToArabic") : t("results.translateToFrench")}
                            </button>
                        )}
                    </div>
                </div>

                {/* ─── Inline Error ─── */}
                {errorMessage && (
                    <InlineError message={errorMessage} onDismiss={() => setErrorMessage(null)} />
                )}

                {/* ─── Main Report Card ─── */}
                <div className="overflow-hidden rounded-3xl bg-white dark:bg-slate-800 shadow-xl shadow-slate-200/50 dark:shadow-slate-900/50 ring-1 ring-slate-100 dark:ring-slate-700">

                    {/* Header */}
                    <div className="border-b border-slate-100 dark:border-slate-700 bg-gradient-to-r from-primary-600 to-primary-700 px-8 py-6 text-white">
                        <div className="flex items-start justify-between">
                            <div>
                                <h1 className="text-xl font-bold tracking-tight">
                                    {activeTab === "ar" ? "تقرير التحليل الطبي" : "Medical Analysis Report"}
                                </h1>
                                <p className="mt-1 text-sm text-primary-100">
                                    {new Date(analysisData.timestamp).toLocaleDateString("en-US", {
                                        weekday: "long", year: "numeric", month: "long", day: "numeric"
                                    })}
                                </p>
                            </div>
                            <div className="rounded-lg bg-white/10 px-3 py-1.5 text-xs font-medium backdrop-blur-sm">
                                {activeTab === "ar" ? t("results.tab.arabic") : activeTab === "fr" ? t("results.tab.french") : t("results.tab.english")}
                            </div>
                        </div>
                    </div>

                    {/* Collapsible Report Content */}
                    {structured ? (
                        /* ── Structured View ── */
                        <div className="px-8 py-6 md:px-10 space-y-6">
                            {/* Status summary */}
                            <StatusBadge
                                overallStatus={structured.report_summary.overall_status}
                                confidence={structured.report_summary.confidence_level}
                                shortExplanation={structured.report_summary.short_explanation}
                            />

                            {/* Biomarker table */}
                            <BiomarkerTable biomarkers={structured.biomarker_analysis} />

                            {/* Abnormal findings */}
                            {structured.abnormal_findings.length > 0 && (
                                <div className="rounded-2xl bg-white dark:bg-slate-800 ring-1 ring-red-100 dark:ring-red-900/30 shadow-sm overflow-hidden">
                                    <div className="px-5 py-3 bg-red-50 dark:bg-red-950/30 border-b border-red-100 dark:border-red-900/40">
                                        <h3 className="text-sm font-bold text-red-800 dark:text-red-300">Abnormal Findings</h3>
                                    </div>
                                    <div className="divide-y divide-red-50 dark:divide-red-900/20">
                                        {structured.abnormal_findings.map((f, i) => (
                                            <div key={i} className="px-5 py-4 space-y-2">
                                                <p className="text-sm font-semibold text-red-700 dark:text-red-400">{f.marker} — <span className="font-normal">{f.issue}</span></p>
                                                {f.possible_meanings.length > 0 && (
                                                    <ul className="text-xs text-slate-600 dark:text-slate-400 space-y-0.5 pl-3">
                                                        {f.possible_meanings.map((m, j) => <li key={j} className="list-disc ml-2">{m}</li>)}
                                                    </ul>
                                                )}
                                                {f.recommended_followup_tests.length > 0 && (
                                                    <p className="text-xs text-slate-500 dark:text-slate-500">Follow-up: {f.recommended_followup_tests.join(", ")}</p>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Health recommendations */}
                            {structured.health_recommendations.length > 0 && (
                                <div className="rounded-2xl bg-emerald-50 dark:bg-emerald-950/20 ring-1 ring-emerald-100 dark:ring-emerald-900/30 px-5 py-4">
                                    <h3 className="text-sm font-bold text-emerald-800 dark:text-emerald-300 mb-2">Health Recommendations</h3>
                                    <ul className="space-y-1.5">
                                        {structured.health_recommendations.map((r, i) => (
                                            <li key={i} className="flex items-start gap-2 text-sm text-emerald-700 dark:text-emerald-400">
                                                <span className="mt-0.5 text-emerald-500">&#10003;</span>
                                                {r}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Specialty recommendations */}
                            {structured.recommended_specialties.length > 0 && (
                                <div className="rounded-2xl bg-sky-50 dark:bg-sky-950/20 ring-1 ring-sky-100 dark:ring-sky-900/30 px-5 py-4">
                                    <h3 className="text-sm font-bold text-sky-800 dark:text-sky-300 mb-2">Recommended Consultation</h3>
                                    {structured.recommended_specialties.map((s, i) => (
                                        <div key={i} className="mb-2">
                                            <p className="text-sm font-semibold text-sky-700 dark:text-sky-400">{s.specialty}</p>
                                            <p className="text-xs text-slate-500 dark:text-slate-500">{s.reason}</p>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Collapsible full markdown */}
                            <div>
                                <button
                                    onClick={() => setReportExpanded((v) => !v)}
                                    className="flex items-center gap-1.5 text-sm font-medium text-slate-400 hover:text-primary-500 transition-colors"
                                >
                                    {reportExpanded ? "Hide raw analysis" : "Show full AI analysis text"}
                                    <svg className={`h-4 w-4 transition-transform duration-200 ${reportExpanded ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="m19 9-7 7-7-7" />
                                    </svg>
                                </button>
                                {reportExpanded && (
                                    <article className="mt-4 prose prose-sm prose-slate dark:prose-invert max-w-none prose-p:text-slate-500 dark:prose-p:text-slate-400">
                                        <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
                                    </article>
                                )}
                            </div>
                        </div>
                    ) : (
                        /* ── Legacy Markdown View ── */
                        <>
                            <div
                                className={`relative px-8 py-8 md:px-10 md:py-10 min-h-[200px] ${activeTab === "ar" ? "text-right" : "text-left"} ${!reportExpanded ? "max-h-64 overflow-hidden" : ""}`}
                                dir={activeTab === "ar" ? "rtl" : "ltr"}
                            >
                                {!reportExpanded && (
                                    <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-white dark:from-slate-800 to-transparent" />
                                )}
                                <article className="prose prose-lg prose-slate dark:prose-invert max-w-none prose-headings:text-slate-800 dark:prose-headings:text-slate-200 prose-headings:font-bold prose-p:text-slate-600 dark:prose-p:text-slate-400 prose-p:leading-relaxed prose-li:text-slate-600 dark:prose-li:text-slate-400 prose-strong:text-primary-900 prose-strong:font-semibold">
                                    <Markdown remarkPlugins={[remarkGfm]}>
                                        {content || "No content available."}
                                    </Markdown>
                                </article>
                            </div>
                            {/* Expand / Collapse toggle */}
                            <div className="border-t border-slate-100 dark:border-slate-700 px-8 py-4">
                                <button
                                    onClick={() => setReportExpanded((v) => !v)}
                                    className="flex items-center gap-1.5 text-sm font-medium text-primary-600 hover:text-primary-700 transition-colors"
                                >
                                    {reportExpanded ? t("results.collapse") || "Collapse report" : t("results.readFull") || "Read full analysis"}
                                    <svg className={`h-4 w-4 transition-transform duration-200 ${reportExpanded ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="m19 9-7 7-7-7" />
                                    </svg>
                                </button>
                            </div>
                        </>
                    )}
                </div>

                {/* ─── Urgency Banner ─── */}
                <UrgencyBanner urgency={urgency} />

                {/* ─── Next Steps ─── */}
                <NextStepsCard urgency={urgency} hasDoctors={hasDoctors} />

                {/* ─── Recommended Doctors ─── */}
                {hasDoctors && (
                    <RecommendedDoctors
                        doctors={analysisData.recommended_doctors!}
                        specialities={analysisData.recommended_specialities || []}
                    />
                )}

                {/* ─── Recommended Hospitals ─── */}
                {hasHospitals && (
                    <RecommendedHospitals
                        hospitals={analysisData.recommended_hospitals!}
                        specialities={analysisData.recommended_specialities || []}
                    />
                )}

                {/* ─── Audio Bar ─── */}
                {analysisData.job_id && (
                    <div className="rounded-2xl bg-white dark:bg-slate-800 ring-1 ring-slate-100 dark:ring-slate-700 shadow-sm px-6 py-4">
                        <div className="flex items-center gap-4">
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary-100 text-primary-600">
                                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                                </svg>
                            </div>
                            <div className="flex-1">
                                {audioState === "ready" && audioUrl ? (
                                    <>
                                        <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Audio Explanation</p>
                                        <audio controls src={audioUrl} className="w-full h-8" />
                                    </>
                                ) : audioState === "generating" ? (
                                    <div className="flex items-center gap-3">
                                        <svg className="h-5 w-5 animate-spin text-primary-500" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                        </svg>
                                        <div>
                                            <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Generating audio...</p>
                                            <p className="text-xs text-slate-500 dark:text-slate-400">This may take a moment.</p>
                                        </div>
                                    </div>
                                ) : (
                                    <button
                                        onClick={handleListenClick}
                                        className="flex items-center gap-2 rounded-lg bg-primary-50 px-4 py-2 text-sm font-medium text-primary-700 hover:bg-primary-100 transition-colors"
                                    >
                                        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M8 5v14l11-7z" />
                                        </svg>
                                        Listen to Audio Explanation
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* ─── Action Bar ─── */}
                <div className="flex flex-wrap items-center justify-center gap-3">
                    <button
                        onClick={handleNewAnalysis}
                        className="flex items-center gap-2 rounded-xl bg-white dark:bg-slate-800 px-5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 shadow-sm ring-1 ring-slate-200 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
                    >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                        </svg>
                        Analyze Another Document
                    </button>
                </div>

                {/* ─── AI Chat (collapsed by default) ─── */}
                {analysisData.job_id && (
                    <div className="overflow-hidden rounded-3xl bg-white dark:bg-slate-800 shadow-xl shadow-slate-200/50 dark:shadow-slate-900/50 ring-1 ring-slate-100 dark:ring-slate-700">

                        {/* Always-visible toggle header */}
                        <button
                            onClick={() => setChatOpen((v) => !v)}
                            className="w-full flex items-center justify-between px-8 py-5 bg-gradient-to-r from-primary-600 to-primary-700 text-white hover:from-primary-700 hover:to-primary-800 transition-colors"
                        >
                            <div className="flex items-center gap-3">
                                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/20">
                                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                                    </svg>
                                </div>
                                <div className="text-left">
                                    <h2 className="font-bold tracking-tight">{t("chat.open") || "Ask About Your Results"}</h2>
                                    <p className="text-xs text-primary-100">
                                        {chatMessages.length > 0 ? `${chatMessages.length} message${chatMessages.length > 1 ? "s" : ""}` : "AI assistant based on your specific lab report"}
                                    </p>
                                </div>
                            </div>
                            <svg
                                className={`h-5 w-5 transition-transform duration-200 ${chatOpen ? "rotate-180" : ""}`}
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                                strokeWidth={2}
                            >
                                <path strokeLinecap="round" strokeLinejoin="round" d="m19 9-7 7-7-7" />
                            </svg>
                        </button>

                        {/* Chat body — only rendered when open */}
                        {chatOpen && (
                            <>
                                {/* Message list */}
                                <div className="max-h-96 min-h-[80px] overflow-y-auto bg-white dark:bg-slate-800 px-6 py-5 space-y-4">
                                    {chatMessages.length === 0 && (
                                        <p className="text-center text-base text-slate-400 dark:text-slate-500 py-4">
                                            Have questions about your results? Ask anything below.
                                        </p>
                                    )}
                                    {chatMessages.map((msg, i) => (
                                        <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                                            {msg.role === "assistant" && (
                                                <div className="mr-2 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-100 text-primary-600 self-end mb-0.5">
                                                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                                                    </svg>
                                                </div>
                                            )}
                                            <div className={`max-w-[78%] rounded-2xl px-4 py-3 text-base leading-relaxed ${
                                                msg.role === "user"
                                                    ? "bg-primary-600 text-white rounded-br-sm"
                                                    : "bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-bl-sm"
                                            }`}>
                                                <article className="prose prose-sm max-w-none prose-p:my-0 prose-li:my-0 prose-headings:my-1 prose-strong:font-semibold prose-p:leading-relaxed">
                                                    <Markdown remarkPlugins={[remarkGfm]}>{msg.content}</Markdown>
                                                </article>
                                            </div>
                                        </div>
                                    ))}

                                    {/* Typing indicator */}
                                    {chatLoading && (
                                        <div className="flex justify-start">
                                            <div className="mr-2 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-100 text-primary-600">
                                                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                                                </svg>
                                            </div>
                                            <div className="rounded-2xl rounded-bl-sm bg-slate-100 dark:bg-slate-700 px-4 py-3">
                                                <div className="flex items-center gap-1">
                                                    <span className="h-2 w-2 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce [animation-delay:0ms]" />
                                                    <span className="h-2 w-2 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce [animation-delay:150ms]" />
                                                    <span className="h-2 w-2 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce [animation-delay:300ms]" />
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                    <div ref={chatBottomRef} />
                                </div>

                                {/* Suggested questions (shown only before first message) */}
                                {chatMessages.length === 0 && (
                                    <div className="px-6 pb-3 flex flex-wrap gap-2 bg-white dark:bg-slate-800">
                                        {[
                                            "What do these results mean overall?",
                                            "Which values are abnormal?",
                                            "Should I be concerned?",
                                            "What should I ask my doctor?",
                                        ].map((q) => (
                                            <button
                                                key={q}
                                                onClick={() => setChatInput(q)}
                                                className="rounded-full border border-primary-200 dark:border-primary-700 bg-primary-50 dark:bg-primary-900/20 px-3 py-1.5 text-xs font-medium text-primary-700 dark:text-primary-300 hover:bg-primary-100 dark:hover:bg-primary-900/40 transition-colors"
                                            >
                                                {q}
                                            </button>
                                        ))}
                                    </div>
                                )}

                                {/* Input bar */}
                                <div className="border-t border-slate-100 dark:border-slate-700 bg-white dark:bg-slate-800 px-6 py-4">
                                    <div className="flex items-center gap-3">
                                        <input
                                            type="text"
                                            value={chatInput}
                                            onChange={(e) => setChatInput(e.target.value)}
                                            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) handleChatSubmit(); }}
                                            placeholder="Ask a question about your results…"
                                            disabled={chatLoading}
                                            className="flex-1 rounded-xl border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 px-4 py-2.5 text-base text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-400 outline-none focus:border-primary-300 focus:ring-2 focus:ring-primary-100 dark:focus:ring-primary-900/40 disabled:opacity-50 transition"
                                        />
                                        <button
                                            onClick={handleChatSubmit}
                                            disabled={chatLoading || !chatInput.trim()}
                                            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                                            aria-label="Send"
                                        >
                                            <svg className="h-4 w-4 translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                            </svg>
                                        </button>
                                    </div>
                                    <p className="mt-2 text-xs text-slate-400 dark:text-slate-500">
                                        The assistant uses your specific lab report as context. It cannot diagnose or prescribe.
                                    </p>
                                </div>
                            </>
                        )}
                    </div>
                )}

                {/* ─── Disclaimer ─── */}
                <div className="flex items-start gap-3 rounded-2xl bg-amber-50 dark:bg-amber-950/30 p-5 text-sm text-amber-900 dark:text-amber-200 border border-amber-100 dark:border-amber-800">
                    <svg className="h-5 w-5 shrink-0 text-amber-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div>
                        <p className="font-semibold text-amber-800 dark:text-amber-300 mb-0.5">Medical Disclaimer</p>
                        <p className="text-amber-700 dark:text-amber-300 leading-relaxed">
                            This AI-generated report is for <strong>informational purposes only</strong>.
                            It is <strong>not</strong> a medical diagnosis.
                            Always consult a certified healthcare professional for accurate interpretation.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
