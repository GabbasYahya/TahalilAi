"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface AnalysisData {
    job_id?: string;
    text: string;
    arabicText?: string;
    audioUrl?: string; 
    pdfUrl?: string;
    timestamp: number;
}

export default function ResultsPage() {
    const { t } = useLanguage();
    const router = useRouter();
    
    const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
    const [activeTab, setActiveTab] = useState<"english" | "arabic">("english");
    const [translating, setTranslating] = useState(false);
    const [audioState, setAudioState] = useState<"idle" | "generating" | "ready">("idle");
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    
    useEffect(() => {
        const stored = localStorage.getItem("analysisResult");
        if (!stored) { router.push("/upload"); return; }
        const data: AnalysisData = JSON.parse(stored);
        if (!data.text) { router.push("/upload"); return; }
        setAnalysisData(data);
        // If audio was previously generated (cached in localStorage)
        if (data.audioUrl) {
            setAudioUrl(`${API_URL}${data.audioUrl}`);
            setAudioState("ready");
        }
    }, [router]);

    const handleListenClick = useCallback(async () => {
        if (!analysisData?.job_id) return;
        
        // Already ready — just scroll to player
        if (audioState === "ready") return;
        if (audioState === "generating") return;
        
        setAudioState("generating");
        
        try {
            // Request audio generation
            const res = await fetch(`${API_URL}/generate-audio`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ job_id: analysisData.job_id })
            });
            const json = await res.json();
            
            if (json.status === "completed" && json.audio_url) {
                // Audio was already generated (cached on server)
                setAudioUrl(`${API_URL}${json.audio_url}`);
                setAudioState("ready");
                const newData = { ...analysisData, audioUrl: json.audio_url };
                setAnalysisData(newData);
                localStorage.setItem("analysisResult", JSON.stringify(newData));
                return;
            }
            
            // Poll for audio completion
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
                        alert("Audio generation failed. Please try again.");
                    }
                } catch {
                    // Keep polling on transient errors
                }
            }, 2000);
            
            // Timeout after 5 minutes
            setTimeout(() => {
                clearInterval(pollAudio);
                setAudioState((prev) => prev === "generating" ? "idle" : prev);
            }, 300000);
            
        } catch {
            setAudioState("idle");
            alert("Could not connect to audio service. Is the backend running?");
        }
    }, [analysisData, audioState]);

    const handleTranslate = async () => {
        if (!analysisData) return;

        // If we already have Arabic cached, just switch tabs
        if (analysisData.arabicText) {
            setActiveTab("arabic");
            return;
        }

        if (!analysisData.job_id) {
            alert("Cannot translate: missing job reference.");
            return;
        }
        
        setTranslating(true);
        try {
            const res = await fetch(`${API_URL}/translate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    text: analysisData.text,
                    job_id: analysisData.job_id 
                })
            });
            
            const json = await res.json();
            if (json.status === "success") {
                const newData = { ...analysisData, arabicText: json.arabic_text };
                setAnalysisData(newData);
                localStorage.setItem("analysisResult", JSON.stringify(newData));
                setActiveTab("arabic");
            } else {
                const errMsg = json.message || "Unknown translation error";
                if (errMsg.includes("CONSUMER_SUSPENDED") || errMsg.includes("API key")) {
                    alert("Translation API key issue. Please check your Gemini API key in the .env file.");
                } else {
                    alert("Translation failed: " + errMsg);
                }
            }
        } catch {
            alert("Could not connect to translation service. Is the backend running?");
        } finally {
            setTranslating(false);
        }
    };

    const handleDownloadPDF = () => {
        if (!analysisData?.pdfUrl) return;
        const link = document.createElement("a");
        link.href = `${API_URL}${analysisData.pdfUrl}`;
        link.setAttribute("download", "TahalilAI-Report.pdf");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleNewAnalysis = () => {
        localStorage.removeItem("analysisResult");
        router.push("/upload");
    };

    if (!analysisData) return null;

    const isArabic = activeTab === "arabic";
    const content = isArabic ? (analysisData.arabicText || "") : analysisData.text;

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/50 px-4 py-8">
            <div className="mx-auto max-w-4xl space-y-6">
                
                {/* ─── Top Bar ─── */}
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <Link href="/upload" className="group flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-indigo-600 transition-colors">
                        <svg className="h-4 w-4 transition-transform group-hover:-translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                        </svg>
                        New Analysis
                    </Link>
                    
                    <div className="flex items-center gap-2">
                        {/* Download PDF */}
                        {analysisData.pdfUrl && (
                            <button
                                onClick={handleDownloadPDF}
                                className="flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm ring-1 ring-slate-200 hover:bg-slate-50 transition-all"
                            >
                                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                Download PDF
                            </button>
                        )}
                        
                        {/* Translate Toggle */}
                        <button
                            onClick={isArabic ? () => setActiveTab("english") : handleTranslate}
                            disabled={translating}
                            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-all ${
                                translating 
                                ? "bg-slate-100 text-slate-400 cursor-wait"
                                : isArabic 
                                ? "bg-white text-slate-700 ring-1 ring-slate-200 hover:bg-slate-50" 
                                : "bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm shadow-indigo-200"
                            }`}
                        >
                            {translating ? (
                                <>
                                    <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                    Translating...
                                </>
                            ) : isArabic ? (
                                "Show English"
                            ) : (
                                <>Translate عربي</>
                            )}
                        </button>
                    </div>
                </div>

                {/* ─── Main Report Card ─── */}
                <div className="overflow-hidden rounded-3xl bg-white shadow-xl shadow-slate-200/50 ring-1 ring-slate-100">
                    
                    {/* Header */}
                    <div className="border-b border-slate-100 bg-gradient-to-r from-indigo-600 to-blue-600 px-8 py-6 text-white">
                        <div className="flex items-start justify-between">
                            <div>
                                <h1 className="text-xl font-bold tracking-tight">
                                    {isArabic ? "تقرير التحليل الطبي" : "Medical Analysis Report"}
                                </h1>
                                <p className="mt-1 text-sm text-indigo-100">
                                    {new Date(analysisData.timestamp).toLocaleDateString("en-US", { 
                                        weekday: "long", year: "numeric", month: "long", day: "numeric" 
                                    })}
                                </p>
                            </div>
                            <div className="rounded-lg bg-white/10 px-3 py-1.5 text-xs font-medium backdrop-blur-sm">
                                {isArabic ? "عربي" : "English"}
                            </div>
                        </div>
                    </div>

                    {/* On-Demand Audio Section */}
                    <div className="border-b border-slate-100 bg-slate-50/50 px-8 py-4">
                        <div className="flex items-center gap-4">
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-100 text-indigo-600">
                                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                                </svg>
                            </div>
                            <div className="flex-1">
                                {audioState === "ready" && audioUrl ? (
                                    <>
                                        <p className="text-xs font-semibold text-slate-700 mb-1">Audio Explanation</p>
                                        <audio controls src={audioUrl} className="w-full h-8" />
                                    </>
                                ) : audioState === "generating" ? (
                                    <div className="flex items-center gap-3">
                                        <svg className="h-5 w-5 animate-spin text-indigo-500" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                        </svg>
                                        <div>
                                            <p className="text-sm font-medium text-slate-700">Generating audio...</p>
                                            <p className="text-xs text-slate-500">This may take a moment. Results are already available above.</p>
                                        </div>
                                    </div>
                                ) : (
                                    <button
                                        onClick={handleListenClick}
                                        className="flex items-center gap-2 rounded-lg bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700 hover:bg-indigo-100 transition-colors"
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

                    {/* Report Content */}
                    <div className={`px-8 py-8 md:px-10 md:py-10 min-h-[300px] ${isArabic ? "text-right" : "text-left"}`} dir={isArabic ? "rtl" : "ltr"}>
                        <article className="prose prose-slate max-w-none prose-headings:text-slate-800 prose-headings:font-bold prose-p:text-slate-600 prose-p:leading-relaxed prose-li:text-slate-600 prose-strong:text-indigo-900 prose-strong:font-semibold">
                            <Markdown remarkPlugins={[remarkGfm]}>
                                {content || "No content available."}
                            </Markdown>
                        </article>
                    </div>
                </div>

                {/* ─── Action Bar ─── */}
                <div className="flex flex-wrap items-center justify-center gap-3">
                    <button
                        onClick={handleNewAnalysis}
                        className="flex items-center gap-2 rounded-xl bg-white px-5 py-2.5 text-sm font-medium text-slate-700 shadow-sm ring-1 ring-slate-200 hover:bg-slate-50 transition-all"
                    >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                        </svg>
                        Analyze Another Document
                    </button>
                </div>

                {/* ─── Disclaimer ─── */}
                <div className="flex items-start gap-3 rounded-2xl bg-amber-50 p-5 text-sm text-amber-900 border border-amber-100">
                    <svg className="h-5 w-5 shrink-0 text-amber-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div>
                        <p className="font-semibold text-amber-800 mb-0.5">Medical Disclaimer</p>
                        <p className="text-amber-700 leading-relaxed">
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

