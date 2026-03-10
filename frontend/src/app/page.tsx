"use client";

import Link from "next/link";
import { useLanguage } from "@/context/LanguageContext";

export default function Home() {
  const { t } = useLanguage();

  return (
    <div className="flex flex-col overflow-hidden">

      {/* ─── Hero ─────────────────────────────────────────────────────── */}
      <section className="relative px-4 pt-20 pb-24 sm:pt-28 sm:pb-32 lg:pt-32">

        {/* Ambient glow — intentionally asymmetric */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute right-0 top-0 -z-10 h-[520px] w-[520px] translate-x-1/3 -translate-y-1/4 rounded-full bg-primary-100 dark:bg-primary-900/20 opacity-50 blur-3xl"
        />

        <div className="mx-auto max-w-6xl">
          <div className="grid grid-cols-1 items-center gap-14 lg:grid-cols-[1fr_420px]">

            {/* ── Copy ── */}
            <div>
              <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-primary-200 dark:border-primary-800 bg-primary-50 dark:bg-primary-900/30 px-3.5 py-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-primary-500 animate-pulse" />
                <span className="text-xs font-semibold uppercase tracking-widest text-primary-700 dark:text-primary-400">
                  Arabic · Français · English
                </span>
              </div>

              <h1 className="max-w-xl text-5xl font-extrabold leading-[1.08] tracking-tight text-slate-900 dark:text-slate-100 sm:text-6xl">
                {t("hero.headline")}
              </h1>

              <p className="mt-6 max-w-md text-lg leading-relaxed text-slate-500 dark:text-slate-400">
                {t("hero.subtext")}
              </p>

              <div className="mt-10 flex flex-wrap items-center gap-4">
                <Link
                  href="/upload"
                  className="inline-flex items-center gap-2 rounded-2xl bg-primary-600 px-7 py-3.5 text-base font-bold text-white shadow-lg shadow-primary-500/20 transition-all hover:bg-primary-700 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-primary-500/25 active:translate-y-0 active:scale-[0.98]"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                  </svg>
                  {t("hero.cta")}
                </Link>
                <Link
                  href="/doctors"
                  className="inline-flex items-center gap-1 text-sm font-semibold text-slate-500 dark:text-slate-400 transition-colors hover:text-primary-600 dark:hover:text-primary-400"
                >
                  {t("hero.findSpecialist")}
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                  </svg>
                </Link>
              </div>

              <div className="mt-8 flex flex-wrap gap-x-6 gap-y-2">
                <span className="flex items-center gap-1.5 text-sm text-slate-400 dark:text-slate-500">
                  <svg className="h-4 w-4 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                  </svg>
                  {t("hero.trust")}
                </span>
                <span className="flex items-center gap-1.5 text-sm text-slate-400 dark:text-slate-500">
                  <svg className="h-4 w-4 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {t("hero.trust2")}
                </span>
              </div>
            </div>

            {/* ── Process visual ── */}
            <div className="relative mx-auto w-full max-w-sm lg:mx-0">

              {/* Step 1 — Document */}
              <div className="badge-left absolute -left-6 top-8 z-10 flex items-center gap-2.5 rounded-2xl bg-white dark:bg-slate-800 px-3.5 py-2.5 shadow-xl ring-1 ring-slate-100 dark:ring-slate-700">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                </div>
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-200">{t("hero.badge.uploaded")}</span>
              </div>

              {/* Step 3 — Done */}
              <div className="badge-right absolute -right-6 bottom-16 z-10 flex items-center gap-2.5 rounded-2xl bg-white dark:bg-slate-800 px-3.5 py-2.5 shadow-xl ring-1 ring-slate-100 dark:ring-slate-700">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-200">{t("hero.badge.ready")}</span>
              </div>

              {/* Main card — process steps */}
              <div className="overflow-hidden rounded-3xl bg-white dark:bg-slate-800 shadow-2xl shadow-slate-300/40 dark:shadow-slate-900/60 ring-1 ring-slate-100 dark:ring-slate-700">
                {/* Card header */}
                <div className="bg-gradient-to-r from-primary-600 to-primary-700 px-6 py-5">
                  <p className="text-[11px] font-semibold uppercase tracking-widest text-primary-200">{t("hero.card.label")}</p>
                  <p className="mt-0.5 text-base font-bold text-white">{t("hero.card.title")}</p>
                </div>

                {/* Steps */}
                <div className="space-y-1 px-6 py-5">
                  {[
                    {
                      icon: (
                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                        </svg>
                      ),
                      labelKey: "hero.step1.label",
                      subKey: "hero.step1.sub",
                      color: "bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400",
                    },
                    {
                      icon: (
                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                        </svg>
                      ),
                      labelKey: "hero.step2.label",
                      subKey: "hero.step2.sub",
                      color: "bg-violet-50 dark:bg-violet-900/20 text-violet-600 dark:text-violet-400",
                    },
                    {
                      icon: (
                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
                        </svg>
                      ),
                      labelKey: "hero.step3.label",
                      subKey: "hero.step3.sub",
                      color: "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400",
                    },
                  ].map((step, i) => (
                    <div key={i} className="flex items-center gap-4 rounded-xl px-3 py-3 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                      <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${step.color}`}>
                        {step.icon}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">{t(step.labelKey)}</p>
                        <p className="text-xs text-slate-400 dark:text-slate-500">{t(step.subKey)}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Footer */}
                <div className="border-t border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-700/50 px-6 py-3 flex items-center gap-2">
                  <svg className="h-3.5 w-3.5 text-primary-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                  </svg>
                  <span className="text-[11px] text-slate-400 dark:text-slate-500">{t("hero.card.footer")}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Stats Strip ──────────────────────────────────────────────── */}
      <section className="border-y border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
        <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
          <div className="grid grid-cols-3 gap-8">
            {[
              { number: "3", labelKey: "stats.languages.label", noteKey: "stats.languages.note" },
              { number: "<60s", labelKey: "stats.time.label", noteKey: "stats.time.note" },
              { number: "100%", labelKey: "stats.privacy.label", noteKey: "stats.privacy.note" },
            ].map((stat) => (
              <div key={stat.labelKey} className="text-center">
                <p className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">{stat.number}</p>
                <p className="mt-1 text-sm font-semibold text-slate-700 dark:text-slate-300">{t(stat.labelKey)}</p>
                <p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">{t(stat.noteKey)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── How it works ─────────────────────────────────────────────── */}
      <section className="px-4 py-24 sm:px-6">
        <div className="mx-auto max-w-5xl">
          <div className="grid grid-cols-1 gap-16 lg:grid-cols-[1fr_520px] lg:items-start">

            {/* Left: heading */}
            <div className="lg:sticky lg:top-28">
              <p className="text-xs font-bold uppercase tracking-widest text-primary-600">{t("hiw.label")}</p>
              <h2 className="mt-3 text-4xl font-extrabold leading-tight tracking-tight text-slate-900 dark:text-slate-100 sm:text-5xl">
                {t("hiw.heading")}
              </h2>
              <p className="mt-5 text-base leading-relaxed text-slate-500 dark:text-slate-400">
                {t("hiw.body")}
              </p>
            </div>

            {/* Right: steps */}
            <div className="space-y-6">
              {[
                {
                  step: "01",
                  titleKey: "hiw.step1.title",
                  descKey: "hiw.step1.desc",
                  icon: (
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                  ),
                },
                {
                  step: "02",
                  titleKey: "hiw.step2.title",
                  descKey: "hiw.step2.desc",
                  icon: (
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                    </svg>
                  ),
                },
                {
                  step: "03",
                  titleKey: "hiw.step3.title",
                  descKey: "hiw.step3.desc",
                  icon: (
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
                    </svg>
                  ),
                },
                {
                  step: "04",
                  titleKey: "hiw.step4.title",
                  descKey: "hiw.step4.desc",
                  icon: (
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                    </svg>
                  ),
                },
              ].map((item) => (
                <div key={item.step} className="flex gap-5 rounded-2xl bg-white dark:bg-slate-800 p-6 ring-1 ring-slate-100 dark:ring-slate-700 shadow-sm">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400">
                    {item.icon}
                  </div>
                  <div>
                    <span className="text-xs font-bold tracking-widest text-slate-400 dark:text-slate-500">{item.step}</span>
                    <h3 className="mt-0.5 text-base font-bold text-slate-900 dark:text-slate-100">{t(item.titleKey)}</h3>
                    <p className="mt-1.5 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{t(item.descKey)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ─── Features grid ────────────────────────────────────────────── */}
      <section className="bg-slate-950 px-4 py-24 sm:px-6">
        <div className="mx-auto max-w-5xl">
          <div className="mb-14">
            <p className="text-xs font-bold uppercase tracking-widest text-primary-400">{t("features.label")}</p>
            <h2 className="mt-3 max-w-xl text-4xl font-extrabold leading-tight tracking-tight text-white sm:text-5xl">
              {t("features.heading1")}<br />
              <span className="text-primary-400">{t("features.heading2")}</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">

            {/* Large card — spans 2 cols */}
            <div className="sm:col-span-2 rounded-3xl bg-white/5 p-8 ring-1 ring-white/10 hover:bg-white/8 transition-colors">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary-500/20 text-primary-400">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                </svg>
              </div>
              <h3 className="mt-5 text-xl font-bold text-white">{t("feat.ai.title")}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">{t("feat.ai.desc")}</p>
              <div className="mt-6 flex flex-wrap gap-2">
                {["Blood tests", "Lipid panels", "Hormone levels", "Urine analysis", "Thyroid", "CBC"].map((tag) => (
                  <span key={tag} className="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-slate-300">{tag}</span>
                ))}
              </div>
            </div>

            {/* Small card */}
            <div className="rounded-3xl bg-white/5 p-7 ring-1 ring-white/10 hover:bg-white/8 transition-colors">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-500/20 text-amber-400">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" />
                </svg>
              </div>
              <h3 className="mt-5 text-base font-bold text-white">{t("feat.audio.title")}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">{t("feat.audio.desc")}</p>
            </div>

            {/* Small card */}
            <div className="rounded-3xl bg-white/5 p-7 ring-1 ring-white/10 hover:bg-white/8 transition-colors">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-rose-500/20 text-rose-400">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 21l5.25-11.25L21 21m-9-3h7.5M3 5.621a48.474 48.474 0 016-.371m0 0c1.12 0 2.233.038 3.334.114M9 5.25V3m3.334 2.364C11.176 10.658 7.69 15.08 3 17.502m9.334-12.138c.896.061 1.785.147 2.666.257m-4.589 8.495a18.023 18.023 0 01-3.827-5.802" />
                </svg>
              </div>
              <h3 className="mt-5 text-base font-bold text-white">{t("feat.arabic.title")}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">{t("feat.arabic.desc")}</p>
            </div>

            {/* Small card */}
            <div className="rounded-3xl bg-white/5 p-7 ring-1 ring-white/10 hover:bg-white/8 transition-colors">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sky-500/20 text-sky-400">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <h3 className="mt-5 text-base font-bold text-white">{t("feat.chat.title")}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">{t("feat.chat.desc")}</p>
            </div>

            {/* Small card */}
            <div className="rounded-3xl bg-white/5 p-7 ring-1 ring-white/10 hover:bg-white/8 transition-colors">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-violet-500/20 text-violet-400">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                </svg>
              </div>
              <h3 className="mt-5 text-base font-bold text-white">{t("feat.doctors.title")}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">{t("feat.doctors.desc")}</p>
            </div>

            {/* Large card — spans 2 cols */}
            <div className="sm:col-span-2 lg:col-span-1 rounded-3xl bg-primary-600/20 p-7 ring-1 ring-primary-500/30 hover:bg-primary-600/25 transition-colors">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary-500/30 text-primary-300">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="mt-5 text-base font-bold text-white">{t("feat.pdf.title")}</h3>
              <p className="mt-2 text-sm leading-relaxed text-primary-200">{t("feat.pdf.desc")}</p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Honest disclaimer banner ─────────────────────────────────── */}
      <section className="px-4 py-16 sm:px-6">
        <div className="mx-auto max-w-3xl rounded-3xl border border-amber-100 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 px-8 py-10">
          <div className="flex gap-5">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-amber-100 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
            </div>
            <div>
              <h3 className="text-base font-bold text-amber-900 dark:text-amber-200">{t("disclaimer.title")}</h3>
              <p className="mt-2 text-sm leading-relaxed text-amber-700 dark:text-amber-300">{t("disclaimer.body")}</p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Trust footer strip ───────────────────────────────────────── */}
      <section className="px-4 pb-24 pt-4 sm:px-6">
        <div className="mx-auto max-w-4xl">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {[
              {
                icon: (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                  </svg>
                ),
                color: "text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/30",
                titleKey: "trust.noAccount.title",
                bodyKey: "trust.noAccount.body",
              },
              {
                icon: (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                  </svg>
                ),
                color: "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20",
                titleKey: "trust.deleted.title",
                bodyKey: "trust.deleted.body",
              },
              {
                icon: (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 21l5.25-11.25L21 21m-9-3h7.5M3 5.621a48.474 48.474 0 016-.371m0 0c1.12 0 2.233.038 3.334.114M9 5.25V3m3.334 2.364C11.176 10.658 7.69 15.08 3 17.502m9.334-12.138c.896.061 1.785.147 2.666.257m-4.589 8.495a18.023 18.023 0 01-3.827-5.802" />
                  </svg>
                ),
                color: "text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-900/20",
                titleKey: "trust.multilang.title",
                bodyKey: "trust.multilang.body",
              },
            ].map((item) => (
              <div key={item.titleKey} className="flex items-start gap-4 rounded-2xl bg-white dark:bg-slate-800 p-5 ring-1 ring-slate-100 dark:ring-slate-700">
                <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${item.color}`}>
                  {item.icon}
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-900 dark:text-slate-100">{t(item.titleKey)}</p>
                  <p className="mt-1 text-xs leading-relaxed text-slate-500 dark:text-slate-400">{t(item.bodyKey)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

    </div>
  );
}
