"use client";

import type { TestResult } from "@/lib/mockData";
import { useLanguage } from "@/context/LanguageContext";

interface TestCardProps {
  test: TestResult;
}

const statusConfig = {
  normal: {
    bg: "bg-success-50",
    border: "border-success-500/20",
    badge: "bg-success-100 text-success-700",
    dot: "bg-success-500",
  },
  warning: {
    bg: "bg-warning-50",
    border: "border-warning-500/20",
    badge: "bg-warning-100 text-warning-700",
    dot: "bg-warning-500",
  },
  alert: {
    bg: "bg-alert-50",
    border: "border-alert-500/20",
    badge: "bg-alert-100 text-alert-700",
    dot: "bg-alert-500",
  },
};

/**
 * Individual test result card.
 * Shows value, range, status, and a plain-language explanation.
 * Color-coded but never alarming.
 */
export function TestCard({ test }: TestCardProps) {
  const { t } = useLanguage();
  const cfg = statusConfig[test.status];

  return (
    <div
      className={`rounded-2xl border ${cfg.border} ${cfg.bg} p-5 transition-shadow hover:shadow-md`}
    >
      {/* Header row: name + status dot */}
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-base font-semibold text-gray-900">{test.name}</h3>
        <span className={`flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${cfg.badge}`}>
          <span className={`inline-block h-1.5 w-1.5 rounded-full ${cfg.dot}`} />
          {test.status === "normal"
            ? "Normal"
            : test.status === "warning"
            ? "Monitor"
            : "Review"}
        </span>
      </div>

      {/* Value + range */}
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold text-gray-900">{test.value}</span>
        <span className="text-sm text-gray-500">{test.unit}</span>
      </div>
      <p className="mt-1 text-xs text-gray-500">
        {t("results.normalRange")}: {test.normalRange}
      </p>

      {/* Plain-language explanation */}
      <div className="mt-4 border-t border-gray-200/60 pt-3">
        <p className="text-xs font-medium uppercase tracking-wide text-gray-400">
          {t("results.whatThisMeans")}
        </p>
        <p className="mt-1.5 text-sm leading-relaxed text-gray-700">
          {test.explanation}
        </p>
      </div>
    </div>
  );
}
