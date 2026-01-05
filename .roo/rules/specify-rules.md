# glean-teleprompter Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-03

## Active Technologies
- TypeScript 5.3+ with strict mode + React 18.2+, Next.js 14+, Jest, React Testing Library, Zustand 4.4+ (001-config-preview-integration)
- N/A (testing feature) (001-config-preview-integration)
- Markdown for documentation, TypeScript 5.3+ for examples + Jest 29+, React Testing Library 13+, Node.js 18+ (001-config-preview-impact-testing)
- File system for documentation, N/A for runtime (001-config-preview-impact-testing)
- TypeScript 5.3+ (strict mode) (003-studio-page-tests)
- localStorage (mocked for testing) (003-studio-page-tests)
- TypeScript 5.3+ (strict mode) + React 18.2+, Next.js 14+, Zustand 4.4+, Framer Motion, Sonner (toasts), Supabase 2.39+, Tailwind CSS, shadcn/ui (004-studio-ui-ux-improvements)
- localStorage (for auto-save status, textarea preferences, keyboard shortcuts stats), Supabase (existing auth/data, no changes) (004-studio-ui-ux-improvements)
- localStorage (primary draft storage), Supabase (optional cloud backup) (006-autosave-improvements)
- TypeScript 5.3+ (strict mode) + React 18.2+, Next.js 14+, Zustand 4.4+, Supabase 2.39+, Tailwind CSS, shadcn/ui, Radix UI components, Framer Motion, Sonner (toasts) (007-unified-state-architecture)
- localStorage for persistence (primary), Supabase (optional cloud backup) (007-unified-state-architecture)
- TypeScript 5.3+ (strict mode) + React 18.2+, Next.js 14+ + Zustand 4.4+, Supabase 2.39+, Tailwind CSS, shadcn/ui, Radix UI components, Framer Motion, Sonner (toasts) (009-fix-preview)
- Web Audio API (011-music-player-widget)
- BroadcastChannel API (011-music-player-widget)
- TypeScript 5.3+ (strict mode) + React 18.2+, Next.js 14+ + Zustand 4.4+, Framer Motion, Sonner (toasts), ReactPlayer, Supabase 2.39+, Tailwind CSS, shadcn/ui (011-music-player-widget)
- localStorage (primary, <1KB), Supabase Storage (audio files, 50MB/file, 500MB total) (011-music-player-widget)

- TypeScript 5.3+ with strict mode + React 18.2+, Next.js 14+, Zustand 4.4+, Supabase 2.39+, Google Fonts API, react-colorful (001-ui-config-system)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

npm test && npm run lint

## Code Style

TypeScript 5.3+ with strict mode: Follow standard conventions

## Recent Changes
- 011-music-player-widget: Added TypeScript 5.3+ (strict mode) + React 18.2+, Next.js 14+ + Zustand 4.4+, Framer Motion, Sonner (toasts), ReactPlayer, Supabase 2.39+, Tailwind CSS, shadcn/ui
- 011-music-player-widget: Added Web Audio API, BroadcastChannel API
- 009-fix-preview: Added TypeScript 5.3+ (strict mode) + React 18.2+, Next.js 14+ + Zustand 4.4+, Supabase 2.39+, Tailwind CSS, shadcn/ui, Radix UI components, Framer Motion, Sonner (toasts)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
