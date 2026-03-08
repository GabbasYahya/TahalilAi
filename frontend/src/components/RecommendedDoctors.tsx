"use client";

import { useState } from "react";
import { DoctorCard, Doctor } from "./DoctorCard";
import { DoctorDetailModal } from "./DoctorDetailModal";

interface RecommendedDoctor {
  id: number;
  title: string;
  name: string;
  speciality: string;
  phone: string;
  address: string;
  city: string;
  image_url: string;
  profile_url: string;
}

interface RecommendedDoctorsProps {
  doctors: RecommendedDoctor[];
  specialities: string[];
  urgency: string;
}

export function RecommendedDoctors({
  doctors,
  specialities,
  urgency,
}: RecommendedDoctorsProps) {
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);

  if (!doctors.length) return null;

  // Map recommendation format to Doctor format
  const mappedDoctors: Doctor[] = doctors.map((d) => ({
    id: d.id,
    title: d.title,
    name: d.name,
    primary_speciality: d.speciality,
    phone: d.phone,
    address: d.address,
    city: d.city,
    description: "",
    languages: "",
    image_url: d.image_url,
    profile_url: d.profile_url,
  }));

  const urgencyColor =
    urgency === "urgent"
      ? "from-red-600 to-rose-600"
      : urgency === "soon"
        ? "from-amber-600 to-orange-600"
        : "from-emerald-600 to-teal-600";

  const urgencyText =
    urgency === "urgent"
      ? "Urgent - Please consult as soon as possible"
      : urgency === "soon"
        ? "Recommended - Schedule a visit soon"
        : "Routine - For your regular follow-up";

  return (
    <>
      <div className="overflow-hidden rounded-3xl bg-white shadow-xl shadow-slate-200/50 ring-1 ring-slate-100">
        <div
          className={`border-b border-slate-100 bg-gradient-to-r ${urgencyColor} px-8 py-5 text-white`}
        >
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/20">
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
            </div>
            <div>
              <h2 className="font-bold tracking-tight">
                Recommended Specialists
              </h2>
              <p className="text-xs text-white/80 mt-0.5">{urgencyText}</p>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {specialities.map((s) => (
              <span
                key={s}
                className="rounded-full bg-white/15 px-2.5 py-0.5 text-xs font-medium"
              >
                {s}
              </span>
            ))}
          </div>
        </div>

        <div className="p-6 grid gap-3 sm:grid-cols-2">
          {mappedDoctors.map((doc) => (
            <DoctorCard
              key={doc.id}
              doctor={doc}
              onClick={() => setSelectedDoctor(doc)}
            />
          ))}
        </div>
      </div>

      {selectedDoctor && (
        <DoctorDetailModal
          doctor={selectedDoctor}
          onClose={() => setSelectedDoctor(null)}
        />
      )}
    </>
  );
}
