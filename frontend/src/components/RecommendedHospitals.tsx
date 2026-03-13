"use client";

import Link from "next/link";
import { HospitalCard, HealthFacility } from "./HospitalCard";
import { useLanguage } from "@/context/LanguageContext";

interface RecommendedHospitalsProps {
  hospitals: HealthFacility[];
  specialities: string[];
}

export function RecommendedHospitals({ hospitals, specialities }: RecommendedHospitalsProps) {
  const { t } = useLanguage();

  if (!hospitals.length) return null;

  return (
    <div className="overflow-hidden rounded-3xl bg-white dark:bg-slate-800 shadow-xl shadow-slate-200/50 dark:shadow-slate-900/50 ring-1 ring-slate-100 dark:ring-slate-700">
      {/* Header — teal/green to differentiate from doctor section */}
      <div className="border-b border-slate-100 dark:border-slate-700 bg-gradient-to-r from-teal-600 to-emerald-600 px-8 py-5 text-white">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/20">
              {/* Hospital building icon */}
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <div>
              <h2 className="font-bold tracking-tight">
                {t("hospitals.recommended.title") || "Nearby Public Hospitals"}
              </h2>
              <p className="text-xs text-white/80 mt-0.5">
                {t("hospitals.recommended.subtitle") || "Free public healthcare facilities"}
              </p>
            </div>
          </div>

          {/* "Free public" badge + "View all" link */}
          <div className="flex items-center gap-3">
            <span className="rounded-full bg-white/20 px-3 py-1 text-xs font-semibold">
              {t("hospitals.free") || "Free & Public"}
            </span>
            <Link
              href="/hospitals"
              className="hidden sm:flex items-center gap-1 rounded-full bg-white/15 hover:bg-white/25 px-3 py-1 text-xs font-medium transition-colors"
            >
              {t("hospitals.viewAll") || "View all"}
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>

        {/* Speciality tags */}
        {specialities.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {specialities.map((s) => (
              <span key={s} className="rounded-full bg-white/15 px-2.5 py-0.5 text-xs font-medium">
                {s}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Grid */}
      <div className="p-6 grid gap-3 sm:grid-cols-2">
        {hospitals.map((fac) => (
          <HospitalCard key={fac.id} facility={fac} />
        ))}
      </div>

      {/* Footer link */}
      <div className="border-t border-slate-100 dark:border-slate-700 px-6 py-4 flex justify-end">
        <Link
          href="/hospitals"
          className="flex items-center gap-1.5 text-sm font-medium text-teal-600 dark:text-teal-400 hover:text-teal-700 dark:hover:text-teal-300 transition-colors"
        >
          {t("hospitals.viewAll") || "View all hospitals"}
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </Link>
      </div>
    </div>
  );
}
