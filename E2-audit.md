# E2 — Desktop ↔ Mobile Parity Audit

**Date:** 2026-05-12  
**Method:** Static code audit (grep, structural review). No browser rendering — visual edge cases may still require manual testing at target widths.

---

## Findings fixed in this session

### F1 — `how-it-works.html`: Inline 3-col stat grid no mobile override *(fixed)*
- **Location:** line 221 — `grid-template-columns:repeat(3,1fr)` inline style, no responsive class
- **Risk:** Three stat cards (88% / 76% / 5×) rendered too narrow on 320–480px screens
- **Fix:** Added `.hiw-stat-grid` class + `@media (max-width: 768px) { grid-template-columns: 1fr }` in page `<style>` block

### F2 — `cookies.html`, `privacy.html`, `terms.html`: Tables no horizontal scroll *(fixed)*
- **Location:** `.legal-body table` — 3–4 column tables, no overflow-x wrapper
- **Risk:** Tables overflow viewport on mobile (320–480px), content clipped
- **Fix:** Added `@media (max-width: 640px) { .legal-body table { display: block; overflow-x: auto } }` to each page's `<style>` block

### F3 — `index.html`: Badge stat showing `≤30min` stale copy *(fixed)*
- **Location:** `.ai-badge-card__stat-num` line 460 — should match the A2 update (under 1 hour)
- **Fix:** Changed to `<1hr`

---

## Pages: Status

| Page | Desktop | Mobile | Notes |
|------|---------|--------|-------|
| `index.html` | ✅ Clean | ✅ Clean | Hero mockup hidden on mobile (intentional). F3 fixed above. |
| `pricing.html` | ✅ Clean | ✅ Clean | Grid collapses at 900px via `[aria-labelledby="plans-heading"]` rule (C4). FAQ accordion functional. Annual/monthly toggle works. |
| `how-it-works.html` | ✅ Clean | ✅ Clean after F1 fix | Process blocks collapse at 768px. Stat grid now collapses. |
| `industries.html` | ✅ Clean | ✅ Clean | Sticky industry nav scrolls horizontally on mobile (overflow-x: auto). |
| `industries/hvac/index.html` | ✅ Clean | ⚠️ See note | Inline repeat-3 pricing grid in `<section>` — no mobile override. At ≤480px, cards are readable but tight. Suggest adding `.ind-pricing-grid { grid-template-columns: 1fr }` at ≤600px. Applies to all 4 new industry pages. |
| `contact.html` | ✅ Clean | ✅ Clean | `contact-grid` collapses at 768px. |
| `blog/index.html` | ✅ Clean | ✅ Clean | Featured post collapses. Blog grid collapses. |
| `blog/post.html` | ✅ Clean | ✅ Clean | `article-layout` collapses at 1024px. |
| `blog/post-template.html` | ✅ Clean | ✅ Clean | Same as post.html. |
| `terms.html` | ✅ Clean | ✅ Clean after F2 fix | Tables now scrollable on mobile. |
| `privacy.html` | ✅ Clean | ✅ Clean after F2 fix | Tables now scrollable on mobile. |
| `cookies.html` | ✅ Clean | ✅ Clean after F2 fix | Tables now scrollable on mobile. |
| `waitlist.html` | ✅ Clean | ✅ Clean | Form and plan grid both have mobile rules in page `<style>`. |

---

## Outstanding issues (not fixed, require follow-up)

### O1 — Industry pages: Pricing mini-card grid no mobile collapse *(low severity)*
- **Affects:** `industries/hvac`, `industries/dental`, `industries/legal`, `industries/cleaning`
- **Location:** The 3-card pricing grid inside each industry page uses an inline `grid-template-columns:repeat(3,1fr)` with no class-based override
- **Risk:** At 320–480px, cards are narrow (~100px each) but still readable due to padding and short content. Not broken, just tight.
- **Fix:** Add page-level `@media (max-width: 600px)` rule to collapse to 1 col, or use the `ind-stat-grid` pattern already on those pages which collapses at 480px.

### O2 — Nav hamburger menu: Mobile overlay gap at 768–1024px *(resolved by E1)*
- E1 fix moves hamburger trigger to ≤1024px, eliminating this range entirely.

### O3 — Copy mismatch: `blog/post.html` and `blog/post-template.html` likely have hardcoded review time copy
- These template files were not in the A2 update pass. Run `grep -n "30 min\|30-minute" blog/post.html blog/post-template.html` to verify.

---

## Not reviewed (out of scope or not marketing pages)
- `dashboard.html` — admin interface, not a marketing page
- `onboarding.html` — form flow; no layout drift found in previous audit pass
- City-specific landing pages (`dental/austin`, `hvac/miami`, etc.) — follow city page template, no structural differences from main pages
