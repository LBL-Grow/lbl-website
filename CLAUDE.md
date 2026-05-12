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
| `how-it-works.html` | `/how-it-works` | |
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
