"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import { StatusBadge } from "@/components/StatusBadge";
// import { TestCard } from "@/components/TestCard"; // Using custom rendering for dynamic text

interface AnalysisData {
  text: string;
  reportPath: string;
  timestamp: number;
}

interface ParsedItem {
  id: string;
  raw: string;
  name?: string;
  content?: string;
  status: "normal" | "warning" | "alert";
}

export default function ResultsPage() {
  const { t } = useLanguage();
  const router = useRouter();
  
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [parsedItems, setParsedItems] = useState<ParsedItem[]>([]);
  const [summary, setSummary] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Load data from localStorage
    const stored = localStorage.getItem("analysisResult");
    if (!stored) {
      router.push("/upload");
      return;
    }

    const data: AnalysisData = JSON.parse(stored);
    setAnalysisData(data);
    
    // 2. Parse the text
    parseContent(data.text);
    setLoading(false);
  }, [router]);

  const parseContent = (text: string) => {
    const lines = text.split('\n');
    const items: ParsedItem[] = [];
    let summaryText = "";

    lines.forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed) return;

      // Check if it's a parameter line (starting with - ** or **)
      if (trimmed.startsWith("- **") || trimmed.startsWith("**")) {
        // Simple extraction
        // Example: "**Hemoglobin**: 13.5 (Normal) - Good."
        const nameMatch = trimmed.match(/\*\*(.*?)\*\*/);
        const name = nameMatch ? nameMatch[1] : "Parameter";
        
        // Determine status
        let status: "normal" | "warning" | "alert" = "normal";
        const lower = trimmed.toLowerCase();
        if (lower.includes("(high)") || lower.includes("(low)") || lower.includes("abnormal")) {
          status = "warning"; // or alert
        }
        
        // Clean up the string for display content (remove the **Name**: part)
        // actually just displaying the whole line might be clearer, 
        // or splitting it. Let's keep it simple.
        const content = trimmed.replace(/^- /, '').replace(/\*\*(.*?)\*\*:?/, '').trim();

        items.push({
          id: Math.random().toString(36).substr(2, 9),
          raw: trimmed,
          name,
          content,
          status
        });
      } else {
        // Append to summary if it's a significant text block
        // (Avoiding empty lines or "---")
        if (!trimmed.startsWith("---") && !trimmed.toLowerCase().includes("inst]")) {
             summaryText += trimmed + " ";
        }
      }
    });

    setParsedItems(items);
    setSummary(summaryText || "Analysis complete. See details below.");
  };

  const handleDownload = () => {
    if (!analysisData) return;
    const blob = new Blob([analysisData.text], { type: "text/plain" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "TahalilAI-Report.txt";
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (loading) {
    return <div className="p-10 text-center">Loading results...</div>;
  }

  // Determine overall status based on items
  const overallStatus = parsedItems.some(i => i.status !== "normal") ? "warning" : "normal";

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6 sm:py-14">
      {/* ─── Summary Card ─── */}
      <div className="rounded-3xl border border-gray-100 bg-white p-6 shadow-xl shadow-gray-100/50 sm:p-8">
        <h1 className="text-2xl font-bold text-gray-900">
          {t("results.summaryHeadline")}
        </h1>

        <div className="mt-4">
          <StatusBadge status={overallStatus} />
        </div>

        {/* Overall summary paragraph */}
        <p className="mt-6 leading-relaxed text-gray-600">
          {summary}
        </p>
      </div>

      {/* ─── Dynamic Test Breakdown ─── */}
      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        {parsedItems.map((item) => (
          <div 
            key={item.id}
            className={`rounded-2xl border p-5 transition-shadow hover:shadow-md ${
                item.status === 'normal' 
                ? 'border-success-500/20 bg-success-50' 
                : 'border-warning-500/20 bg-warning-50'
            }`}
          >
             <h3 className="text-base font-semibold text-gray-900 mb-2">{item.name}</h3>
             <p className="text-sm text-gray-700">{item.content}</p>
          </div>
        ))}
      </div>

      {/* ─── Actions ─── */}
      <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
        <button
            onClick={handleDownload}
            className="inline-flex items-center gap-2 rounded-full bg-primary-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-primary-500/20 transition-all hover:bg-primary-700 active:scale-[0.98]"
        >
             <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
               <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
             </svg>
             Download Report
        </button>

        <Link
          href="/upload"
          className="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white px-6 py-3 text-sm font-medium text-gray-600 transition-all hover:bg-gray-50 active:scale-[0.98]"
        >
          Upload another
        </Link>
      </div>
    </div>
  );
}
