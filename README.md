# CityLens Frontend

Next.js 14 App Router client powered by Tailwind CSS, Shadcn/ui, Supabase, MapLibre GL (OpenStreetMap tiles), and OpenAI Vision integrations.

## Map Tiles

The default base layer uses OpenStreetMap via MapLibre (no API key required). Additional options include CartoDB Voyager, Stadia Maps (set `NEXT_PUBLIC_STADIA_API_KEY` for higher limits), and Esri World Imagery.

## Getting Started

```bash
pnpm install # or npm install / yarn
cp .env.example .env.local
pnpm dev
```

Replace placeholder components with upload workflows, map overlays, and case management tools.
