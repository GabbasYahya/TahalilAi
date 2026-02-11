# TahalilAI — Medical Reports, Explained Clearly

An AI-powered web app that helps users understand medical test reports (PDFs or images) in clear, non-diagnostic, human language.

## Tech Stack

- **Framework:** Next.js 16 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS 4
- **Font:** Inter (Google Fonts)

## Pages

| Route | Description |
| ----------- | -------------------------------------------------------- |
| `/` | Landing page — hero, CTA, trust messaging |
| `/upload` | Upload medical report (drag-and-drop), optional context |
| `/results` | AI-generated plain-language test result breakdown |

## Getting Started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
src/
├── app/
│   ├── layout.tsx          # Root layout with Header + Footer
│   ├── page.tsx            # Landing page
│   ├── globals.css         # Design system tokens & animations
│   ├── upload/page.tsx     # Upload page with processing state
│   └── results/page.tsx    # Results page with test cards
├── components/
│   ├── Header.tsx          # Sticky header with logo + language switcher
│   ├── Footer.tsx          # Disclaimer + privacy footer
│   ├── LanguageSwitcher.tsx# EN / FR / AR toggle
│   ├── ProcessingLoader.tsx# Step-based calm loading animation
│   ├── TestCard.tsx        # Individual test result card
│   └── StatusBadge.tsx     # Overall status badge (normal/warning/alert)
├── context/
│   └── LanguageContext.tsx # i18n context with translations
└── lib/
    └── mockData.ts         # Mock CBC report data
```

## Scripts

| Command | Description |
| --------------- | ------------------------------ |
| `npm run dev` | Start development server |
| `npm run build` | Create production build |
| `npm run start` | Run production server |
| `npm run lint` | Run ESLint |
