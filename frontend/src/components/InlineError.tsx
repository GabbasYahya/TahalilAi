"use client";

interface InlineErrorProps {
  message: string | null;
  variant?: "error" | "warning" | "info";
  onDismiss?: () => void;
  className?: string;
}

export function InlineError({
  message,
  variant = "error",
  onDismiss,
  className = "",
}: InlineErrorProps) {
  if (!message) return null;

  const styles = {
    error:   "bg-red-50 dark:bg-red-950/40 border border-red-100 dark:border-red-800 text-red-700 dark:text-red-300",
    warning: "bg-amber-50 dark:bg-amber-950/40 border border-amber-100 dark:border-amber-800 text-amber-700 dark:text-amber-300",
    info:    "bg-primary-50 dark:bg-primary-950/40 border border-primary-100 dark:border-primary-800 text-primary-700 dark:text-primary-300",
  }[variant];

  const iconColor = {
    error:   "text-red-400 dark:text-red-500",
    warning: "text-amber-400 dark:text-amber-500",
    info:    "text-primary-400 dark:text-primary-500",
  }[variant];

  return (
    <div className={`rounded-2xl p-4 flex items-start gap-3 ${styles} ${className}`} role="alert">
      {/* Exclamation-circle icon */}
      <svg
        className={`h-5 w-5 shrink-0 mt-0.5 ${iconColor}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
        aria-hidden="true"
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
      </svg>

      <p className="flex-1 text-base leading-relaxed">{message}</p>

      {onDismiss && (
        <button
          onClick={onDismiss}
          aria-label="Dismiss"
          className={`shrink-0 rounded-lg p-1 hover:bg-black/5 dark:hover:bg-white/10 transition-colors ${iconColor}`}
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
}
