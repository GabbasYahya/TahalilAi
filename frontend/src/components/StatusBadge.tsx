"use client";

import type { TestStatus } from "@/lib/mockData";
import { useLanguage } from "@/context/LanguageContext";

interface StatusBadgeProps {
  status: TestStatus;
}

/**
 * Top-level status badge used on the results summary card.
 * Uses emoji + text to clearly communicate overall result.
 */
export function StatusBadge({ status }: StatusBadgeProps) {
  const { t } = useLanguage();

  const config = {
    normal: {
      emoji: "🟢",
      text: t("results.normal"),
      bg: "bg-success-50 border-success-200",
      textColor: "text-success-700",
    },
    warning: {
      emoji: "🟡",
      text: t("results.monitor"),
      bg: "bg-warning-50 border-warning-200",
      textColor: "text-warning-700",
    },
    alert: {
      emoji: "🔴",
      text: t("results.review"),
      bg: "bg-alert-50 border-alert-200",
      textColor: "text-alert-700",
    },
  };

  const cfg = config[status];

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 ${cfg.bg}`}
    >
      <span className="text-lg">{cfg.emoji}</span>
      <span className={`text-sm font-medium ${cfg.textColor}`}>{cfg.text}</span>
    </div>
  );
}
