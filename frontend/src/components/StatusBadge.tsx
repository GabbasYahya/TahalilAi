"use client";

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
    normal: { label: "All Normal", color: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300 ring-emerald-200 dark:ring-emerald-800" },
    mostly_normal: { label: "Mostly Normal", color: "bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-300 ring-sky-200 dark:ring-sky-800" },
    abnormal: { label: "Abnormal Results", color: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300 ring-amber-200 dark:ring-amber-800" },
    critical: { label: "Critical Values", color: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300 ring-red-200 dark:ring-red-800" },
};

const CONFIDENCE_LABEL: Record<string, string> = {
    low: "Low confidence",
    medium: "Medium confidence",
    high: "High confidence",
};

interface StatusBadgeProps {
    overallStatus: string;
    confidence: string;
    shortExplanation: string;
}

export function StatusBadge({ overallStatus, confidence, shortExplanation }: StatusBadgeProps) {
    const cfg = STATUS_CONFIG[overallStatus] || STATUS_CONFIG.mostly_normal;

    return (
        <div className="flex flex-col gap-3 rounded-2xl bg-white dark:bg-slate-800 ring-1 ring-slate-100 dark:ring-slate-700 shadow-sm px-6 py-5">
            <div className="flex items-center gap-3 flex-wrap">
                <span className={`inline-flex items-center rounded-full px-3.5 py-1.5 text-sm font-semibold ring-1 ${cfg.color}`}>
                    {cfg.label}
                </span>
                <span className="text-xs text-slate-400 dark:text-slate-500">
                    {CONFIDENCE_LABEL[confidence] || confidence}
                </span>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{shortExplanation}</p>
        </div>
    );
}
