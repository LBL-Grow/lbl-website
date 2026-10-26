# CLAUDE.md — LBL Website

Static marketing site for Local Boost Lab. No build step. Deployed to Vercel.

## Commands

```bash
# No npm. Edit HTML/CSS/JS directly.
# Preview locally with any static server:
npx serve .
python3 -m http.server 8080
```

## Architecture

Pure static HTML/CSS/JS. `vercel.json` handles routing, proxying, and headers.

**API calls** proxy to Railway backend:
```
/api/* → https://powerful-balance-production-971d.up.railway.app/api/*
```

**Dashboard** redirects to Railway (auth-gated, not served from this repo).

## Pages

| File | Route | Notes |
|------|-------|-------|
| `index.html` | `/` | Homepage |
| `pricing.html` | `/pricing` | Stripe checkout links |
| `how-it-works.html` | `/how-it-works` | GBP service page |
| `whatsapp-ai-assistant.html` | `/whatsapp-ai-assistant` | WhatsApp AI Assistant service page |
| `about.html` | `/about` | |
| `industries.html` | `/industries` | Overview |
| `contact.html` | `/contact` | |
| `onboarding.html` | `/onboarding` | Post-signup checklist |
| `waitlist.html` | `/waitlist` | |
| `blog/index.html` | `/blog` | Blog index |
| `blog/post.html` | `/blog/post` | Dynamic post renderer |
| `privacy.html` / `terms.html` | `/privacy` `/terms` | Legal |

**Industry landing pages** (city-level SEO):
- `dental/austin/`
- `hvac/miami/`, `hvac/phoenix/`
- `plumbing/miami/`

## Shared Code

- `shared.js` — nav scroll behavior, common utilities; included in every page
- `styles.css` — global styles

## Assets

Images come in `.png` + `.webp` pairs. Always add both when uploading new images. Use `.webp` in `<picture>` tags with `.png` fallback.

## Key Constraints

- **No bundler** — `<script>` tags only; no imports, no npm
- **`cleanUrls: true`** in vercel.json — link to `/pricing` not `/pricing.html`
- **GTM tag** (`GTM-NCBWF3MH`) must remain in `<head>` of every page
- **CSP header** in vercel.json is strict — new external scripts need to be added there
- `robots.txt` and `sitemap.xml` are static files; update sitemap when adding pages

## Spanish (Colombia) version: `/es-co/`

The pages under `es-co/` are **generated** from the English pages. Do not edit them by hand.

```bash
python3 tools/i18n/extract.py   # after changing an English page: refresh the list of strings
python3 tools/i18n/build.py     # regenerate es-co/ (fails listing any untranslated string)
python3 tools/i18n/remap.py <page>  # after extract.py, if you moved/removed English markup: realigns the translation positions (run BEFORE editing the .txt by hand; reads the old ones from git HEAD)
```

- Page map (English file → Spanish URL): `tools/i18n/pages.json`
- Translations: `tools/i18n/es-co/<page>.txt` (`<position>|<text>`), shared strings in `_shared.json`, strings inside inline scripts in `_js.json`
- The Spanish pages leave out the unsourced statistics, the "results from clients" blocks and the `aggregateRating` markup
- `build.py` also adds the `hreflang` tags and the language link to the English pages
- `tools/` is excluded from the deployment (`.vercelignore`)
- `/sitemap.xml`: Vercel serves the static `sitemap.xml` of this repo (a file wins over the rewrite to Railway in `vercel.json`), so that is the one Google sees. `tools/pages/build.py` adds the generated pages to it; add other new URLs by hand

## Page templates: new industry pages (`tools/pages/`)

New industry landing pages are **generated** (EN + ES-CO) from one data file, not written by hand and not translated by position.

```bash
python3 tools/pages/build.py          # writes industries/<slug>/ and es-co/industrias/<slug>/ and links them from the industry hubs
python3 tools/pages/build.py --check  # fails if a generated file is out of date
```

- Content: `tools/pages/industries_data.py` (both languages, one block per industry). No statistics or claims without a source.
- The template reuses the header, footer and pricing block of `industries/cleaning/index.html` and `es-co/industrias/limpieza/index.html`, so they stay in sync.
- `tools/i18n/build.py` regenerates `es-co/industrias.html` and drops the hub links: **run `tools/pages/build.py` after it**.
- `tools/pages/build.py` also appends the generated URLs to the static `sitemap.xml` and lists them in `tools/pages/sitemap-urls.txt`.
- Plan: new page types (comparisons, guides) should use this same approach, then the older hand-written pages can move over one by one.
