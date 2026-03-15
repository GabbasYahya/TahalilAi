"use client";

import { Doctor } from "./DoctorCard";
import { useLanguage } from "@/context/LanguageContext";

interface DoctorDetailModalProps {
  doctor: Doctor;
  onClose: () => void;
}

export function DoctorDetailModal({ doctor, onClose }: DoctorDetailModalProps) {
  const { t } = useLanguage();
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 dark:bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-lg rounded-3xl bg-white dark:bg-slate-800 shadow-2xl ring-1 ring-slate-100 dark:ring-slate-700 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary-600 to-primary-700 px-6 py-5 text-white">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              {doctor.image_url ? (
                <img
                  src={doctor.image_url}
                  alt={doctor.name}
                  className="h-16 w-16 rounded-xl object-cover ring-2 ring-white/30"
                />
              ) : (
                <div className="h-16 w-16 rounded-xl bg-white/20 flex items-center justify-center text-2xl font-bold">
                  {doctor.title === "Dr" ? "Dr" : doctor.name.charAt(0)}
                </div>
              )}
              <div>
                <h2 className="text-lg font-bold">
                  {doctor.title ? `${doctor.title}. ` : ""}
                  {doctor.name}
                </h2>
                <p className="text-sm text-primary-100">{doctor.primary_speciality}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="rounded-lg bg-white/10 p-1.5 hover:bg-white/20 transition-colors"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4 max-h-[60vh] overflow-y-auto">
          {/* City & Address */}
          <div className="flex items-start gap-3">
            <svg className="h-5 w-5 text-slate-400 dark:text-slate-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <div>
              <p className="text-sm font-medium text-slate-800 dark:text-slate-200">{doctor.city}</p>
              {doctor.address && (
                <p className="text-sm text-slate-500 dark:text-slate-400">{doctor.address}</p>
              )}
            </div>
          </div>

          {/* Phone */}
          {doctor.phone && (
            <div className="flex items-center gap-3">
              <svg className="h-5 w-5 text-slate-400 dark:text-slate-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
              <a href={`tel:${doctor.phone}`} className="text-sm text-primary-600 dark:text-primary-400 font-medium hover:underline">
                {doctor.phone}
              </a>
            </div>
          )}

          {/* Languages */}
          {doctor.languages && (
            <div className="flex items-start gap-3">
              <svg className="h-5 w-5 text-slate-400 dark:text-slate-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
              </svg>
              <p className="text-sm text-slate-600 dark:text-slate-300">{doctor.languages}</p>
            </div>
          )}

          {/* Rating */}
          {doctor.google_rating && (
            <div className="flex items-center gap-3">
              <span className="text-yellow-500 text-lg">&#9733;</span>
              <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{doctor.google_rating} / 5</span>
              {doctor.google_review_count != null && (
                <span className="text-xs text-slate-400 dark:text-slate-500">({doctor.google_review_count} reviews)</span>
              )}
            </div>
          )}

          {/* Description */}
          {doctor.description && (
            <div className="rounded-xl bg-slate-50 dark:bg-slate-700 p-4">
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">About</p>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                {doctor.description.length > 500
                  ? doctor.description.slice(0, 500) + "..."
                  : doctor.description}
              </p>
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="border-t border-slate-100 dark:border-slate-700 px-6 py-4 flex gap-3">
          {doctor.phone && (
            <a
              href={`tel:${doctor.phone}`}
              className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-primary-600 py-2.5 text-sm font-semibold text-white hover:bg-primary-700 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
              {t("card.call")}
            </a>
          )}
          {(doctor.address || doctor.city) && (
            <a
              href={`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent([doctor.address, doctor.city].filter(Boolean).join(", "))}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-white dark:bg-slate-700 py-2.5 text-sm font-semibold text-slate-700 dark:text-slate-200 ring-1 ring-slate-200 dark:ring-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
              {t("card.directions")}
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
