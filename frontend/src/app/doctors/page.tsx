"use client";

import { useEffect, useState, useCallback } from "react";
import { useLanguage } from "@/context/LanguageContext";
import { DoctorCard, Doctor } from "@/components/DoctorCard";
import { DoctorDetailModal } from "@/components/DoctorDetailModal";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface CityOption {
  city: string;
  count: number;
}
interface SpecialityOption {
  speciality: string;
  count: number;
}

export default function DoctorsPage() {
  const { t } = useLanguage();

  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  const [cities, setCities] = useState<CityOption[]>([]);
  const [specialities, setSpecialities] = useState<SpecialityOption[]>([]);

  const [selectedCity, setSelectedCity] = useState("");
  const [selectedSpeciality, setSelectedSpeciality] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);

  const pageSize = 20;

  // Load filter options on mount
  useEffect(() => {
    fetch(`${API_URL}/doctors/cities`)
      .then((r) => r.json())
      .then(setCities)
      .catch(() => {});
    fetch(`${API_URL}/doctors/specialities`)
      .then((r) => r.json())
      .then(setSpecialities)
      .catch(() => {});
  }, []);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Fetch doctors when filters change
  const fetchDoctors = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedCity) params.set("city", selectedCity);
      if (selectedSpeciality) params.set("speciality", selectedSpeciality);
      if (debouncedQuery) params.set("q", debouncedQuery);
      params.set("page", String(page));
      params.set("page_size", String(pageSize));

      const res = await fetch(`${API_URL}/doctors?${params}`);
      const data = await res.json();
      setDoctors(data.doctors || []);
      setTotal(data.total || 0);
    } catch {
      setDoctors([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [selectedCity, selectedSpeciality, debouncedQuery, page]);

  useEffect(() => {
    fetchDoctors();
  }, [fetchDoctors]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [selectedCity, selectedSpeciality, debouncedQuery]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/50 px-4 py-8">
      <div className="mx-auto max-w-5xl space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {t("doctors.title")}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            {total.toLocaleString()} {t("doctors.doctorsFound")}
          </p>
        </div>

        {/* Search & Filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t("doctors.search")}
              className="w-full rounded-xl border border-slate-200 bg-white pl-10 pr-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 outline-none focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100 transition"
            />
          </div>

          {/* City filter */}
          <select
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 outline-none focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100 transition min-w-[160px]"
          >
            <option value="">{t("doctors.allCities")}</option>
            {cities.map((c) => (
              <option key={c.city} value={c.city}>
                {c.city} ({c.count})
              </option>
            ))}
          </select>

          {/* Speciality filter */}
          <select
            value={selectedSpeciality}
            onChange={(e) => setSelectedSpeciality(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 outline-none focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100 transition min-w-[200px]"
          >
            <option value="">{t("doctors.allSpecialities")}</option>
            {specialities.map((s) => (
              <option key={s.speciality} value={s.speciality}>
                {s.speciality} ({s.count})
              </option>
            ))}
          </select>
        </div>

        {/* Clear filters */}
        {(selectedCity || selectedSpeciality || searchQuery) && (
          <button
            onClick={() => {
              setSelectedCity("");
              setSelectedSpeciality("");
              setSearchQuery("");
            }}
            className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
          >
            {t("doctors.clearFilters")}
          </button>
        )}

        {/* Doctor Grid */}
        {loading ? (
          <div className="flex justify-center py-16">
            <svg
              className="h-8 w-8 animate-spin text-indigo-500"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
          </div>
        ) : doctors.length === 0 ? (
          <div className="text-center py-16">
            <svg
              className="mx-auto h-12 w-12 text-slate-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
            <p className="mt-3 text-sm text-slate-500">
              {t("doctors.noResults")}
            </p>
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {doctors.map((doc) => (
              <DoctorCard
                key={doc.id}
                doctor={doc}
                onClick={() => setSelectedDoctor(doc)}
              />
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 pt-4">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>

            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum: number;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (page <= 3) {
                  pageNum = i + 1;
                } else if (page >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = page - 2 + i;
                }
                return (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={`h-9 w-9 rounded-lg text-sm font-medium transition-colors ${
                      page === pageNum
                        ? "bg-indigo-600 text-white"
                        : "text-slate-600 hover:bg-slate-100"
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>

            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedDoctor && (
        <DoctorDetailModal
          doctor={selectedDoctor}
          onClose={() => setSelectedDoctor(null)}
        />
      )}
    </div>
  );
}
