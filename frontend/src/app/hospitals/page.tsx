"use client";

import { useEffect, useState, useCallback } from "react";
import { useLanguage } from "@/context/LanguageContext";
import { HospitalCard, HealthFacility } from "@/components/HospitalCard";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface RegionOption {
  region: string;
  count: number;
}
interface TypeOption {
  facility_type: string;
  count: number;
}

export default function HospitalsPage() {
  const { t } = useLanguage();

  const [facilities, setFacilities] = useState<HealthFacility[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  const [regions, setRegions] = useState<RegionOption[]>([]);
  const [types, setTypes] = useState<TypeOption[]>([]);

  const [selectedRegion, setSelectedRegion] = useState("");
  const [selectedType, setSelectedType] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  const pageSize = 20;

  // Load filter options on mount
  useEffect(() => {
    fetch(`${API_URL}/hospitals/regions`)
      .then((r) => r.json())
      .then(setRegions)
      .catch(() => {});
    fetch(`${API_URL}/hospitals/types`)
      .then((r) => r.json())
      .then(setTypes)
      .catch(() => {});
  }, []);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Fetch facilities when filters change
  const fetchFacilities = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedRegion) params.set("region", selectedRegion);
      if (selectedType) params.set("facility_type", selectedType);
      if (debouncedQuery) params.set("q", debouncedQuery);
      params.set("page", String(page));
      params.set("page_size", String(pageSize));

      const res = await fetch(`${API_URL}/hospitals?${params}`);
      const data = await res.json();
      setFacilities(data.facilities || []);
      setTotal(data.total || 0);
    } catch {
      setFacilities([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [selectedRegion, selectedType, debouncedQuery, page]);

  useEffect(() => {
    fetchFacilities();
  }, [fetchFacilities]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setPage(1);
  }, [selectedRegion, selectedType, debouncedQuery]);

  const totalPages = Math.ceil(total / pageSize);
  const hasFilters = selectedRegion || selectedType || searchQuery;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-teal-50/30 to-emerald-50/50 dark:from-slate-900 dark:via-slate-900 dark:to-slate-900 px-4 py-8">
      <div className="mx-auto max-w-5xl space-y-6">

        {/* Page Header */}
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {t("hospitals.title") || "Public Health Facilities"}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t("hospitals.subtitle") || "Free public hospitals and primary care centers in Morocco"}
          </p>
          <p className="text-xs text-teal-600 dark:text-teal-400 mt-0.5 font-medium">
            {total.toLocaleString()} {t("hospitals.found") || "facilities found"}
          </p>
        </div>

        {/* Search & Filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400"
              fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t("hospitals.search") || "Search name or department…"}
              className="w-full rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 pl-10 pr-4 py-2.5 text-sm text-slate-800 dark:text-slate-200 placeholder-slate-400 outline-none focus:border-teal-300 focus:ring-2 focus:ring-teal-100 transition"
            />
          </div>

          {/* Region filter */}
          <select
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            className="rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300 outline-none focus:border-teal-300 focus:ring-2 focus:ring-teal-100 transition min-w-[180px]"
          >
            <option value="">{t("hospitals.allRegions") || "All Regions"}</option>
            {regions.map((r) => (
              <option key={r.region} value={r.region}>
                {r.region} ({r.count})
              </option>
            ))}
          </select>

          {/* Type filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300 outline-none focus:border-teal-300 focus:ring-2 focus:ring-teal-100 transition min-w-[200px]"
          >
            <option value="">{t("hospitals.allTypes") || "All Types"}</option>
            {types.map((tp) => (
              <option key={tp.facility_type} value={tp.facility_type}>
                {tp.facility_type === "Hôpital"
                  ? t("hospitals.typeHopital") || "Hôpital"
                  : t("hospitals.typePrimary") || "Primary Care"}
                {" "}({tp.count})
              </option>
            ))}
          </select>
        </div>

        {/* Clear filters */}
        {hasFilters && (
          <button
            onClick={() => {
              setSelectedRegion("");
              setSelectedType("");
              setSearchQuery("");
            }}
            className="text-sm text-teal-600 dark:text-teal-400 hover:text-teal-700 dark:hover:text-teal-300 font-medium"
          >
            {t("hospitals.clearFilters") || "Clear filters"}
          </button>
        )}

        {/* Facilities Grid */}
        {loading ? (
          <div className="flex justify-center py-16">
            <svg className="h-8 w-8 animate-spin text-teal-500" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : facilities.length === 0 ? (
          <div className="text-center py-16">
            <svg className="mx-auto h-12 w-12 text-slate-300 dark:text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16M3 21h18M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <p className="mt-3 text-slate-500 dark:text-slate-400 text-sm">
              {t("hospitals.noResults") || "No facilities found"}
            </p>
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {facilities.map((f) => (
              <HospitalCard key={f.id} facility={f} />
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 pt-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="rounded-lg px-3 py-1.5 text-sm font-medium bg-white dark:bg-slate-800 ring-1 ring-slate-200 dark:ring-slate-600 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              ← Prev
            </button>
            <span className="text-sm text-slate-500 dark:text-slate-400">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="rounded-lg px-3 py-1.5 text-sm font-medium bg-white dark:bg-slate-800 ring-1 ring-slate-200 dark:ring-slate-600 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
