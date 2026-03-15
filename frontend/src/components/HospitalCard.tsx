"use client";

export interface HealthFacility {
  id: number;
  name: string;
  region: string;
  delegation: string;
  commune?: string;
  category_code: string;
  category_name: string;
  facility_type: string;
  departments?: string;
  phone?: string;
  address?: string;
}

interface HospitalCardProps {
  facility: HealthFacility;
}

// Color coding by facility type / category
const CATEGORY_COLOR: Record<string, string> = {
  HIR: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300",
  HR:  "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
  HP:  "bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300",
  HPr: "bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300",
  CRO: "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300",
  CPU: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300",
  HPsyR: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300",
  HPsyP: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300",
  "CSU-1": "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
  "CSU-2": "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
  "CSR-1": "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  "CSR-2": "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  DR: "bg-lime-100 text-lime-700 dark:bg-lime-900/40 dark:text-lime-300",
  CDTMR: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300",
  CRSR: "bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300",
  LSP: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300",
};

function HospitalIcon({ facilityType }: { facilityType: string }) {
  if (facilityType === "Hôpital") {
    return (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    );
  }
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
    </svg>
  );
}

export function HospitalCard({ facility }: HospitalCardProps) {
  const badgeClass = CATEGORY_COLOR[facility.category_code] ?? "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300";
  const depts = facility.departments
    ? facility.departments.split(",").slice(0, 4)
    : [];

  return (
    <div className="rounded-2xl bg-white dark:bg-slate-800 p-5 shadow-sm ring-1 ring-slate-100 dark:ring-slate-700 hover:shadow-md hover:ring-slate-200 dark:hover:ring-slate-600 transition-all">
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className={`h-12 w-12 rounded-xl flex items-center justify-center shrink-0 ${
          facility.facility_type === "Hôpital"
            ? "bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400"
            : "bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400"
        }`}>
          <HospitalIcon facilityType={facility.facility_type} />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-semibold text-slate-900 dark:text-slate-100 leading-tight">
              {facility.name}
            </h3>
            <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${badgeClass}`}>
              {facility.category_code}
            </span>
          </div>

          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {facility.category_name}
          </p>

          {/* Location */}
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1.5 flex items-center gap-1">
            <svg className="h-3 w-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span className="truncate">
              {facility.delegation}
              {facility.commune ? ` — ${facility.commune}` : ""}
            </span>
          </p>

          {/* Region */}
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5 truncate pl-4">
            {facility.region}
          </p>

          {/* Departments chips */}
          {depts.length > 0 && (
            <div className="mt-2.5 flex flex-wrap gap-1">
              {depts.map((d) => (
                <span
                  key={d}
                  className="rounded-full bg-slate-100 dark:bg-slate-700 px-2 py-0.5 text-xs text-slate-600 dark:text-slate-300"
                >
                  {d.trim()}
                </span>
              ))}
              {facility.departments && facility.departments.split(",").length > 4 && (
                <span className="rounded-full bg-slate-100 dark:bg-slate-700 px-2 py-0.5 text-xs text-slate-400 dark:text-slate-500">
                  +{facility.departments.split(",").length - 4}
                </span>
              )}
            </div>
          )}

          {/* Phone + Directions */}
          <div className="mt-2 flex items-center gap-3">
            {facility.phone && (
              <a
                href={`tel:${facility.phone}`}
                onClick={(e) => e.stopPropagation()}
                className="inline-flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
                {facility.phone}
              </a>
            )}
            <a
              href={`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent([facility.address, facility.delegation, facility.commune, facility.region].filter(Boolean).join(", "))}`}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="inline-flex items-center gap-1 text-xs text-teal-600 dark:text-teal-400 hover:underline"
            >
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
              Directions
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
