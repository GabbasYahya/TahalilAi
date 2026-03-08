"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { RecommendedDoctors } from "@/components/RecommendedDoctors";

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

interface AnalysisData {
    job_id?: string;
    text: string;
    arabicText?: string;
    audioUrl?: string;
    pdfUrl?: string;
    arabicPdfUrl?: string;
    timestamp: number;
    recommended_specialities?: string[];
    urgency?: string;
    recommended_doctors?: RecommendedDoctor[];
}

export default function ResultsPage() {
    const { t } = useLanguage();
    const router = useRouter();
    
    const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
    const [activeTab, setActiveTab] = useState<"english" | "arabic">("english");
    const [translating, setTranslating] = useState(false);
    const [audioState, setAudioState] = useState<"idle" | "generating" | "ready">("idle");
    const [audioUrl, setAudioUrl] = useState<string | null>(null);

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
                const newData = { ...analysisData, arabicText: json.arabic_text, arabicPdfUrl: json.arabic_pdf_url ?? undefined };
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
        const url = activeTab === "arabic" && analysisData?.arabicPdfUrl
            ? analysisData.arabicPdfUrl
            : analysisData?.pdfUrl;
        if (!url) return;
        window.open(`${API_URL}${url}`, "_blank");
    };

    const handleNewAnalysis = () => {
        localStorage.removeItem("analysisResult");
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
                { role: "assistant", content: "Could not reach the AI service. Is the backend running?" },
            ]);
        } finally {
            setChatLoading(false);
        }
    }, [chatInput, analysisData, chatLoading]);

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
                        {(analysisData.pdfUrl || analysisData.arabicPdfUrl) && (
                            <button
                                onClick={handleDownloadPDF}
                                className="flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm ring-1 ring-slate-200 hover:bg-slate-50 transition-all"
                            >
                                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                {isArabic ? "تحميل PDF" : "Download PDF"}
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

                {/* ─── Critical Alert ─── */}
                {analysisData.urgency === "urgent" && (
                    <div className="flex items-start gap-3 rounded-2xl bg-red-50 p-5 text-sm text-red-900 border border-red-200">
                        <svg className="h-6 w-6 shrink-0 text-red-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <div>
                            <p className="font-semibold text-red-800">Critical Values Detected</p>
                            <p className="text-red-700 leading-relaxed">
                                Some of your results require prompt medical attention. Please consult a doctor as soon as possible.
                            </p>
                        </div>
                    </div>
                )}

                {/* ─── Recommended Doctors ─── */}
                {analysisData.recommended_doctors && analysisData.recommended_doctors.length > 0 && (
                    <RecommendedDoctors
                        doctors={analysisData.recommended_doctors}
                        specialities={analysisData.recommended_specialities || []}
                        urgency={analysisData.urgency || "routine"}
                    />
                )}

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

                {/* ─── AI Chat ─── */}
                {analysisData.job_id && (
                    <div className="overflow-hidden rounded-3xl bg-white shadow-xl shadow-slate-200/50 ring-1 ring-slate-100">

                        {/* Chat header */}
                        <div className="border-b border-slate-100 bg-gradient-to-r from-violet-600 to-indigo-600 px-8 py-5 text-white">
                            <div className="flex items-center gap-3">
                                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/20">
                                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                                    </svg>
                                </div>
                                <div>
                                    <h2 className="font-bold tracking-tight">Ask About Your Results</h2>
                                    <p className="text-xs text-indigo-100">AI assistant based on your specific lab report</p>
                                </div>
                            </div>
                        </div>

                        {/* Message list */}
                        <div className="max-h-96 min-h-[80px] overflow-y-auto px-6 py-5 space-y-4">
                            {chatMessages.length === 0 && (
                                <p className="text-center text-sm text-slate-400 py-4">
                                    Have questions about your results? Ask anything below.
                                </p>
                            )}
                            {chatMessages.map((msg, i) => (
                                <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                                    {msg.role === "assistant" && (
                                        <div className="mr-2 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-violet-100 text-violet-600 self-end mb-0.5">
                                            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                                            </svg>
                                        </div>
                                    )}
                                    <div className={`max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                                        msg.role === "user"
                                            ? "bg-indigo-600 text-white rounded-br-sm"
                                            : "bg-slate-100 text-slate-800 rounded-bl-sm"
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
                                    <div className="mr-2 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-violet-100 text-violet-600">
                                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                                        </svg>
                                    </div>
                                    <div className="rounded-2xl rounded-bl-sm bg-slate-100 px-4 py-3">
                                        <div className="flex items-center gap-1">
                                            <span className="h-2 w-2 rounded-full bg-slate-400 animate-bounce [animation-delay:0ms]" />
                                            <span className="h-2 w-2 rounded-full bg-slate-400 animate-bounce [animation-delay:150ms]" />
                                            <span className="h-2 w-2 rounded-full bg-slate-400 animate-bounce [animation-delay:300ms]" />
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={chatBottomRef} />
                        </div>

                        {/* Suggested questions (shown only before first message) */}
                        {chatMessages.length === 0 && (
                            <div className="px-6 pb-3 flex flex-wrap gap-2">
                                {[
                                    "What do these results mean overall?",
                                    "Which values are abnormal?",
                                    "Should I be concerned?",
                                    "What should I ask my doctor?",
                                ].map((q) => (
                                    <button
                                        key={q}
                                        onClick={() => setChatInput(q)}
                                        className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-100 transition-colors"
                                    >
                                        {q}
                                    </button>
                                ))}
                            </div>
                        )}

                        {/* Input bar */}
                        <div className="border-t border-slate-100 px-6 py-4">
                            <div className="flex items-center gap-3">
                                <input
                                    type="text"
                                    value={chatInput}
                                    onChange={(e) => setChatInput(e.target.value)}
                                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) handleChatSubmit(); }}
                                    placeholder="Ask a question about your results…"
                                    disabled={chatLoading}
                                    className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 outline-none focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100 disabled:opacity-50 transition"
                                />
                                <button
                                    onClick={handleChatSubmit}
                                    disabled={chatLoading || !chatInput.trim()}
                                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                                    aria-label="Send"
                                >
                                    <svg className="h-4 w-4 translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                    </svg>
                                </button>
                            </div>
                            <p className="mt-2 text-xs text-slate-400">
                                The assistant uses your specific lab report as context. It cannot diagnose or prescribe.
                            </p>
                        </div>
                    </div>
                )}

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

