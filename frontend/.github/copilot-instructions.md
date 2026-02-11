# TahalilAI — Copilot Instructions

## Project Overview
- **Type:** Health-tech web application (patient-facing, MVP)
- **Framework:** Next.js 16 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS 4
- **Font:** Inter

## Design Principles
- Patient-first interface — trust, calm, clarity, safety
- No medical jargon without explanation
- No diagnosis or treatment language
- Emotionally calming tone and gentle transitions
- WCAG-friendly accessibility
- Mobile-first, desktop-optimized

## Color Palette
- **Primary:** Soft medical teal (#14b8a6 / primary-600)
- **Success:** Muted green (#22c55e)
- **Warning:** Soft amber (#f59e0b)
- **Alert:** Muted red (#ef4444) — never bright
- **Background:** White / very light gray
- **Avoid:** Dark mode, neon colors, aggressive contrasts

## Architecture
- Component-based with reusable UI components in `src/components/`
- Language context (EN/FR/AR) in `src/context/LanguageContext.tsx`
- Mock data in `src/lib/mockData.ts`
- Three routes: `/` (landing), `/upload`, `/results`

## Setup Checklist
- [x] Project scaffolded with Next.js + Tailwind
- [x] Design system created (globals.css)
- [x] Shared components built (Header, Footer, LanguageSwitcher, etc.)
- [x] Landing page, Upload page, Results page built
- [x] Processing animation component built
- [x] Mock data wired up
- [x] Build verified — compiles without errors
- [x] README.md up to date
