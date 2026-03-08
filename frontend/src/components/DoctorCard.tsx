"use client";

export interface Doctor {
  id: number;
  title: string;
  name: string;
  primary_speciality: string;
  specialities?: string;
  phone: string;
  address: string;
  city: string;
  description: string;
  languages: string;
  image_url: string;
  profile_url: string;
  google_rating?: number | null;
  google_review_count?: number | null;
  distance_km?: number;
}

interface DoctorCardProps {
  doctor: Doctor;
  onClick?: () => void;
}

export function DoctorCard({ doctor, onClick }: DoctorCardProps) {
  return (
    <div
      onClick={onClick}
      className="cursor-pointer rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-100 hover:shadow-md hover:ring-slate-200 transition-all"
    >
      <div className="flex items-start gap-4">
        {/* Avatar */}
        {doctor.image_url ? (
          <img
            src={doctor.image_url}
            alt={doctor.name}
            className="h-14 w-14 rounded-xl object-cover shrink-0"
          />
        ) : (
          <div className="h-14 w-14 rounded-xl bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-lg shrink-0">
            {doctor.title === "Dr" ? "Dr" : doctor.name.charAt(0)}
          </div>
        )}

        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-slate-900 truncate">
            {doctor.title ? `${doctor.title}. ` : ""}
            {doctor.name}
          </h3>
          <p className="text-sm text-indigo-600 font-medium">
            {doctor.primary_speciality}
          </p>
          <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
            <svg
              className="h-3 w-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            {doctor.city}
            {doctor.distance_km != null && (
              <span className="text-slate-400">
                ({doctor.distance_km} km)
              </span>
            )}
          </p>
          {doctor.phone && (
            <p className="text-xs text-slate-400 mt-0.5">{doctor.phone}</p>
          )}
          {doctor.google_rating && (
            <div className="flex items-center gap-1 mt-1">
              <span className="text-yellow-500 text-xs">&#9733;</span>
              <span className="text-xs text-slate-600">
                {doctor.google_rating}
              </span>
              {doctor.google_review_count != null && (
                <span className="text-xs text-slate-400">
                  ({doctor.google_review_count})
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
