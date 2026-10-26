#!/usr/bin/env python3
"""Genera las páginas de industria nuevas (inglés y español de Colombia) a partir de una plantilla.

Por qué existe: el sitio es HTML escrito a mano (cada página repite cabecera, pie y estilos) y /es-co/ se genera por
posición de texto desde el inglés. Para las páginas nuevas no queremos mantener 14 archivos a mano, así que estas salen
de un solo archivo de datos (`industries_data.py`) y de una plantilla que reutiliza la cabecera, el pie y el bloque de
precios de dos páginas de referencia, para que no se desfasen.

    python3 tools/pages/build.py            # escribe las páginas y muestra la lista de URLs nuevas para el sitemap
    python3 tools/pages/build.py --check    # no escribe; falla si algún archivo generado difiere del que hay en disco

Referencias (se leen al generar):  industries/cleaning/index.html  y  es-co/industrias/limpieza/index.html
Salida:  industries/<slug>/index.html  y  es-co/industrias/<slug>/index.html

Notas:
  - Las páginas generadas NO deben editarse a mano: cambia `industries_data.py` y vuelve a generar.
  - No se usan estadísticas ni afirmaciones sin fuente (ver el encabezado de `industries_data.py`).
  - El FAQPage se genera desde las preguntas visibles con tools/seo/faq_schema.py.
  - sitemap.xml (archivo estático del repo; es el que ve Google) recibe las URLs nuevas desde este script.
"""
import datetime
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'pages'))
sys.path.insert(0, str(ROOT / 'tools' / 'seo'))
from industries_data import INDUSTRIES  # noqa: E402
from comparisons_data import COMPARISONS  # noqa: E402
from faq_schema import faq_schema  # noqa: E402

SITE = 'https://localboostlab.com'
TODAY = datetime.date.today().isoformat()
REF = {'en': ROOT / 'industries/cleaning/index.html', 'es': ROOT / 'es-co/industrias/limpieza/index.html'}
REF_SLUG = {'en': ('/industries/cleaning', 'Cleaning'), 'es': ('/es-co/industrias/limpieza', 'Limpieza')}
UI = {
    'en': {'home': 'Home', 'inds': 'Industries', 'inds_url': '/industries', 'home_url': '/', 'crumb_label': 'Breadcrumb',
           'cta1': 'Get a Free Audit →', 'cta1_url': '/free-audit', 'cta2': 'How It Works →', 'cta2_url': '/how-it-works',
           'faq_h2': 'Frequently asked questions', 'trust': ['No contract. Cancel anytime.', 'Live within 24 hours', 'Serving all US markets'],
           'area': {'@type': 'Country', 'name': 'United States'}, 'lang': 'en', 'switch': 'English'},
    'es': {'home': 'Inicio', 'inds': 'Industrias', 'inds_url': '/es-co/industrias', 'home_url': '/es-co', 'crumb_label': 'Ruta de navegación',
           'cta1': 'Pide tu auditoría gratis →', 'cta1_url': '/es-co/auditoria-gratis', 'cta2': 'Cómo funciona →', 'cta2_url': '/es-co/como-funciona',
           'faq_h2': 'Preguntas frecuentes', 'trust': ['Sin contrato. Cancelas cuando quieras.', 'Activo en 24 horas', 'Atendemos negocios en toda Colombia'],
           'area': {'@type': 'Country', 'name': 'Colombia'}, 'lang': 'es-CO', 'switch': 'Español'},
}


def url_for(ind, lang):
    if ind.get('kind') == 'comparison':
        return f"/compare/{ind['slug_en']}" if lang == 'en' else f"/es-co/comparar/{ind['slug_es']}"
    return f"/industries/{ind['slug_en']}" if lang == 'en' else f"/es-co/industrias/{ind['slug_es']}"


def out_path(ind, lang):
    return ROOT / (url_for(ind, lang).lstrip('/') + '/index.html')


def esc(s):
    return html.escape(s, quote=True)


def split_ref(lang):
    t = REF[lang].read_text()
    i, j = t.index('<main'), t.index('</main>') + len('</main>')
    return t[:i], t[i:j], t[j:]


def section(main, label):
    for s in re.split(r'(?=<section\b)', main):
        if f'aria-labelledby="{label}"' in s:
            return s.rstrip().split('\n<!--')[0].rstrip()
    raise SystemExit(f'No encuentro la sección {label} en la referencia')


def icons(main):
    found = re.findall(r'<div class="ind-serve-card__icon">.*?</div>', section(main, 'serve-heading'), flags=re.S)
    return found[:4]


def jsonld(ind, lang, data, others):
    u = SITE + url_for(ind, lang)
    ui = UI[lang]
    if ind.get('kind') == 'comparison':
        page = {'@context': 'https://schema.org', '@type': 'WebPage', 'name': data['title'], 'description': data['desc'], 'url': u,
                'inLanguage': ui['lang'], 'isPartOf': {'@type': 'WebSite', 'name': 'Local Boost Lab', 'url': SITE}}
        crumbs = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': ui['home'], 'item': SITE + ui['home_url'].rstrip('/')},
            {'@type': 'ListItem', 'position': 2, 'name': data['name'], 'item': u}]}
        return ''.join(f'\n  <script type="application/ld+json">\n  {json.dumps(d, ensure_ascii=False, indent=2)}\n  </script>' for d in (page, crumbs))
    service = {
        '@context': 'https://schema.org', '@type': 'Service', 'name': data['title'].split(' | ')[0],
        'description': data['service_desc'], 'url': u, 'serviceType': 'Google Business Profile management',
        'provider': {'@type': 'Organization', 'name': 'Local Boost Lab', 'url': SITE},
        'areaServed': ui['area'], 'audience': {'@type': 'Audience', 'audienceType': data['name']},
    }
    crumbs = {
        '@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': ui['home'], 'item': SITE + ui['home_url'].rstrip('/')},
            {'@type': 'ListItem', 'position': 2, 'name': ui['inds'], 'item': SITE + ui['inds_url']},
            {'@type': 'ListItem', 'position': 3, 'name': data['name'], 'item': u}]}
    return ''.join(f'\n  <script type="application/ld+json">\n  {json.dumps(d, ensure_ascii=False, indent=2)}\n  </script>' for d in (service, crumbs))


# Cuarta tarjeta, igual para todas las industrias (es lo que el producto hace por cualquier perfil).
HEALTH = {
    'en': ('Profile health and accurate services', 'We keep the services, categories, hours and contact details on your {short} profile complete and accurate, and flag errors before they cost you visibility in the right searches.'),
    'es': ('Perfil y servicios al día', 'Mantenemos completos y correctos los servicios, las categorías, los horarios y los datos de contacto de tu perfil de {short}, y te avisamos de cualquier error antes de que te cueste visibilidad en las búsquedas correctas.'),
}


def build_main(ind, lang, ref_main):
    d, ui = ind[lang], UI[lang]
    ic = icons(ref_main)
    health = (HEALTH[lang][0], HEALTH[lang][1].format(short=d['short']))
    cards = '\n'.join(
        f'      <div class="ind-serve-card">\n        {ic[n]}\n        <div class="ind-serve-card__label">{esc(lab)}</div>\n        <p>{esc(txt)}</p>\n      </div>'
        for n, (lab, txt) in enumerate(list(d['cards']) + [health]))
    faqs = '\n'.join(
        f'      <div class="faq-item">\n        <button class="faq-btn" aria-expanded="false" aria-controls="faq-{n}">\n          {esc(q)}\n'
        '          <svg width="12" height="8" viewBox="0 0 12 8" fill="none" aria-hidden="true"><path d="M1 1l5 5 5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>\n'
        f'        </button>\n        <div id="faq-{n}" class="faq-answer" role="region">\n          {esc(a)}\n        </div>\n      </div>'
        for n, (q, a) in enumerate(d['faqs'], 1))
    crumb = (f'<nav aria-label="{ui["crumb_label"]}" style="background:var(--surface-mid);padding:10px 0;border-bottom:1px solid var(--border-color);">\n'
             f'  <div class="container" style="font-size:0.8rem;color:var(--text-muted);">\n'
             f'    <a href="{ui["home_url"]}" style="color:var(--text-muted);text-decoration:none;">{ui["home"]}</a>\n    <span style="margin:0 8px;opacity:0.5;">›</span>\n'
             f'    <a href="{ui["inds_url"]}" style="color:var(--text-muted);text-decoration:none;">{ui["inds"]}</a>\n    <span style="margin:0 8px;opacity:0.5;">›</span>\n'
             f'    <span style="color:var(--authority-blue);font-weight:600;">{esc(d["name"])}</span>\n  </div>\n</nav>')
    hero = (f'<section class="ind-hero" aria-labelledby="hero-heading">\n  <div class="container" style="text-align:center;position:relative;z-index:1;">\n'
            f'    <p style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:var(--signal-amber);margin-bottom:14px;">{esc(d["eyebrow"])}</p>\n'
            f'    <h1 id="hero-heading" style="color:white;max-width:800px;margin:0 auto 22px;">{d["h1"]}</h1>\n'
            f'    <p style="color:rgba(255,255,255,0.8);font-size:1.2rem;max-width:640px;margin:0 auto 36px;line-height:1.7;">{esc(d["hero_p"])}</p>\n'
            f'    <div style="display:flex;gap:14px;justify-content:center;flex-wrap:wrap;">\n'
            f'      <a href="{ui["cta1_url"]}" class="btn btn-amber btn-xl">{ui["cta1"]}</a>\n'
            f'      <a href="{ui["cta2_url"]}" class="btn btn-ghost btn-xl" style="color:rgba(255,255,255,0.8);">{ui["cta2"]}</a>\n    </div>\n  </div>\n</section>')
    serve = (f'<section class="section" style="background:var(--surface-light);border-top:1px solid var(--border-color);" aria-labelledby="serve-heading">\n'
             f'  <div class="container" style="max-width:960px;">\n    <h2 id="serve-heading" class="section-title fade-up">{esc(d["serve_h2"])}</h2>\n'
             f'    <p class="section-subtitle fade-up" style="max-width:640px;margin-left:auto;margin-right:auto;">{esc(d["serve_sub"])}</p>\n'
             f'    <div class="ind-serve-grid fade-up" style="margin-top:40px;">\n{cards}\n    </div>\n  </div>\n</section>')
    pricing = section(ref_main, 'pricing-heading')
    faq = (f'<section class="section section--white" aria-labelledby="faq-heading">\n  <div class="container" style="max-width:720px;">\n'
           f'    <h2 id="faq-heading" class="section-title fade-up">{ui["faq_h2"]}</h2>\n    <div class="fade-up" style="margin-top:40px;">\n{faqs}\n    </div>\n  </div>\n</section>')
    trust = ''.join(f'\n        <span>{esc(s)}</span>' for s in ui['trust'])
    cta = (f'<section class="section lbl-cta-section" aria-labelledby="cta-heading">\n  <div class="container">\n    <div class="lbl-cta-block fade-up">\n'
           f'      <h2 id="cta-heading">{esc(d["cta_h2"])}</h2>\n      <p>{esc(d["cta_p"])}</p>\n'
           f'      <a href="{ui["cta1_url"]}" class="btn btn-amber btn-xl">{ui["cta1"]}</a>\n      <div class="lbl-cta-trust">{trust}\n      </div>\n    </div>\n  </div>\n</section>')
    return '<main id="main" role="main">\n' + '\n'.join([crumb, hero, serve, pricing, faq, cta]) + '\n</main>'


COMPARE_CSS = """<style>
.cmp-table{width:100%;border-collapse:collapse;margin-top:32px;background:#fff}
.cmp-table th{padding:14px 16px;font-family:var(--font-heading);font-size:.95rem;color:var(--authority-blue);border-bottom:2px solid var(--border-color);text-align:left}
.cmp-table td{padding:14px 16px;border-bottom:1px solid var(--surface-mid);font-size:.9rem;color:var(--slate-core);vertical-align:top;line-height:1.55}
.cmp-table td:first-child{font-weight:700;color:var(--authority-blue);width:22%}
.cmp-table .cmp-lbl{background:rgba(245,158,11,.06)}
.cmp-table thead th.cmp-lbl{background:rgba(245,158,11,.12)}
.cmp-list{margin:14px 0 0 0;padding:0 0 0 22px;line-height:1.7;color:var(--slate-core);list-style:disc}
.cmp-list--ol{list-style:decimal}
.cmp-list li{margin-bottom:8px}
@media (max-width:700px){.cmp-table th,.cmp-table td{padding:10px 8px;font-size:.8rem}}
</style>"""


def build_comparison_main(cmp, lang, ref_main):
    d, ui = cmp[lang], UI[lang]
    c0, c1, c2 = d['table_cols']
    rows = '\n'.join(f'          <tr><td>{esc(a)}</td><td>{esc(b)}</td><td class="cmp-lbl">{esc(c)}</td></tr>' for a, b, c in d['rows'])
    table = (f'<section class="section section--white" aria-labelledby="table-heading">\n  <div class="container" style="max-width:1000px;">\n'
             f'    <h2 id="table-heading" class="section-title fade-up">{esc(d["table_h2"])}</h2>\n    <div style="overflow-x:auto;" class="fade-up">\n'
             f'      <table class="cmp-table">\n        <thead><tr><th>{esc(c0)}</th><th>{esc(c1)}</th><th class="cmp-lbl">{esc(c2)}</th></tr></thead>\n'
             f'        <tbody>\n{rows}\n        </tbody>\n      </table>\n    </div>\n  </div>\n</section>')

    def card(h2, items, ordered=False):
        tag = 'ol' if ordered else 'ul'
        li = ''.join(f'<li>{esc(x)}</li>' for x in items)
        cls = 'cmp-list cmp-list--ol' if ordered else 'cmp-list'
        return f'<div class="ind-serve-card"><div class="ind-serve-card__label">{esc(h2)}</div><{tag} class="{cls}">{li}</{tag}></div>'
    two = (f'<section class="section" style="background:var(--surface-light);border-top:1px solid var(--border-color);" aria-labelledby="fit-heading">\n'
           f'  <div class="container" style="max-width:960px;">\n    <h2 id="fit-heading" class="section-title fade-up">{esc(d["fit_h2"])}</h2>\n'
           f'    <div class="ind-serve-grid fade-up" style="margin-top:40px;">\n      {card(d["agency_h2"], d["agency_items"])}\n      {card(d["lbl_h2"], d["lbl_items"])}\n    </div>\n  </div>\n</section>')
    decide = (f'<section class="section section--white" aria-labelledby="decide-heading">\n  <div class="container" style="max-width:960px;">\n'
              f'    <h2 id="decide-heading" class="section-title fade-up">{esc(d["decide_h2"])}</h2>\n    <div class="ind-serve-grid fade-up" style="margin-top:40px;">\n'
              f'      {card(d["decide_h2"], d["decide"], True)}\n      {card(d["ask_h2"], d["ask"])}\n    </div>\n  </div>\n</section>')
    # Migas de 2 niveles y hero iguales a las de industria.
    crumb = (f'<nav aria-label="{ui["crumb_label"]}" style="background:var(--surface-mid);padding:10px 0;border-bottom:1px solid var(--border-color);">\n'
             f'  <div class="container" style="font-size:0.8rem;color:var(--text-muted);">\n'
             f'    <a href="{ui["home_url"]}" style="color:var(--text-muted);text-decoration:none;">{ui["home"]}</a>\n    <span style="margin:0 8px;opacity:0.5;">›</span>\n'
             f'    <span style="color:var(--authority-blue);font-weight:600;">{esc(d["name"])}</span>\n  </div>\n</nav>')
    base = build_main({**cmp, lang: {**d, 'cards': [], 'short': '', 'serve_h2': '', 'serve_sub': ''}}, lang, ref_main)  # reutiliza hero, precios, FAQ y CTA
    parts = {k: re.search(r'<section[^>]*aria-labelledby="%s".*?</section>' % k, base, re.S).group(0) for k in ('hero-heading', 'pricing-heading', 'faq-heading', 'cta-heading')}
    return '<main id="main" role="main">\n' + COMPARE_CSS + '\n' + '\n'.join([crumb, parts['hero-heading'], table, two, decide, parts['pricing-heading'], parts['faq-heading'], parts['cta-heading']]) + '\n</main>'


def patch_head(pre, ind, lang, data):
    other = 'es' if lang == 'en' else 'en'
    u, uo = SITE + url_for(ind, lang), SITE + url_for(ind, other)
    en_u, es_u = (u, uo) if lang == 'en' else (uo, u)
    def sub(pat, rep, s, flags=0):
        out, n = re.subn(pat, lambda m: rep, s, count=1, flags=flags)
        if n != 1:
            raise SystemExit(f'Plantilla: no encuentro {pat[:50]}')
        return out
    pre = sub(r'<title>.*?</title>', f'<title>{esc(data["title"])}</title>', pre, re.S)
    pre = sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(data["desc"])}">', pre)
    pre = sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{u}">', pre)
    pre = sub(r'<!-- hreflang:start -->.*?<!-- hreflang:end -->',
              f'<!-- hreflang:start -->\n  <link rel="alternate" hreflang="en" href="{en_u}">\n  <link rel="alternate" hreflang="es-CO" href="{es_u}">\n'
              f'  <link rel="alternate" hreflang="x-default" href="{en_u}">\n  <!-- hreflang:end -->', pre, re.S)
    pre = sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{esc(data["title"])}">', pre)
    pre = sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{esc(data["og"])}">', pre)
    pre = sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{u}">', pre)
    pre = sub(r'<meta name="twitter:title" content="[^"]*">', f'<meta name="twitter:title" content="{esc(data["title"])}">', pre)
    # Todo el marcado JSON-LD de la referencia es de otra página: se reemplaza por el de esta.
    blocks = list(re.finditer(r'\s*<script type="application/ld\+json">.*?</script>', pre, re.S))
    if not blocks:
        raise SystemExit('Plantilla: la referencia no tiene JSON-LD')
    first = blocks[0].start()
    pre = re.sub(r'\s*<script type="application/ld\+json">.*?</script>', '', pre, flags=re.S)
    pre = pre[:first] + jsonld(ind, lang, data, None) + pre[first:]
    return pre


def patch_post_and_nav(text, lang, ind, order_inds):
    ref_url, ref_label = REF_SLUG[lang]
    own_url = url_for(ind, lang)
    # Enlace de cambio de idioma: apunta a la versión equivalente de ESTA página.
    other = 'es' if lang == 'en' else 'en'
    text = re.sub(r'<a href="[^"]*" hreflang="(?:en|es-CO)" lang="(?:en|es)" data-lang-switch>',
                  f'<a href="{url_for(ind, other)}" hreflang="{"es-CO" if other == "es" else "en"}" lang="{"es" if other == "es" else "en"}" data-lang-switch>', text)
    # Menú de industrias y pie: se agregan las industrias nuevas después de la de referencia.
    extra_li = ''.join(f'\n    <li role="presentation"><a href="{url_for(i, lang)}" role="menuitem">{esc(i[lang]["name"])}</a></li>' for i in order_inds)
    extra_a = ''.join(f' <a href="{url_for(i, lang)}">{esc(i[lang]["name"])}</a>' for i in order_inds)
    li_ref = f'<li role="presentation"><a href="{ref_url}" role="menuitem">{ref_label}</a></li>'
    a_ref = f'<a href="{ref_url}">{ref_label}</a>'
    text = text.replace(li_ref, li_ref + extra_li)
    text = text.replace(a_ref, a_ref + extra_a)
    return text


# Enlaces desde los índices de industrias hacia las páginas nuevas (los índices ya listan estas industrias como tarjetas).
# Es un parche idempotente sobre los archivos que sirve el sitio. El índice en español lo regenera tools/i18n/build.py:
# después de correrlo hay que volver a correr este script.
HUBS = {
    'industries.html': ('en', r'<div class="card__title">(?P<t>{title})</div>',
                        {'Landscaping &amp; Lawn Care': 'landscaping', 'Auto Repair': 'auto-repair', 'Med Spa &amp; Aesthetics': 'beauty-salons',
                         'Chiropractic': 'chiropractors', 'Pest Control': 'pest-control', 'Roofing': 'roofing'}),
    'es-co/industrias.html': ('es', r'<div class="other-card__title">(?P<t>{title})</div>',
                              {'Plomería': 'plomeria', 'Talleres mecánicos': 'talleres-mecanicos', 'Jardinería': 'jardineria-y-paisajismo',
                               'Control de plagas': 'control-de-plagas', 'Quiropraxia y bienestar': 'quiropracticos',
                               'Salones de belleza y spas': 'salones-de-belleza', 'Techos y cubiertas': 'techos-e-impermeabilizacion'}),
}


def patch_hubs():
    """Devuelve {ruta: texto nuevo} para los índices que cambian."""
    by_slug = {(i['slug_en'] if lg == 'en' else i['slug_es']): i for i in INDUSTRIES for lg in ('en', 'es')}
    changed = {}
    for rel, (lang, pat, titles) in HUBS.items():
        path = ROOT / rel
        text = path.read_text()
        for title, slug in titles.items():
            ind = by_slug[slug]
            href = url_for(ind, lang)
            rx = re.compile(pat.format(title=re.escape(title)))
            text = rx.sub(lambda m: m.group(0).replace(m.group('t'), f'<a href="{href}" style="color:inherit;text-decoration:none;">{m.group("t")}</a>'), text, count=1) \
                if f'href="{href}" style="color:inherit' not in text else text
        if text != path.read_text():
            changed[path] = text
    return changed


# La página de precios ya tiene una tabla "LBL vs. una agencia": su título pasa a enlazar la comparativa completa.
PRICING_LINKS = {'pricing.html': 'en', 'es-co/precios.html': 'es'}


def patch_pricing_links():
    cmp = COMPARISONS[0]
    changed = {}
    for rel, lang in PRICING_LINKS.items():
        path = ROOT / rel
        text = path.read_text()
        href = url_for({**cmp, 'kind': 'comparison'}, lang)
        if f'href="{href}"' in text:
            continue
        new, n = re.subn(r'(<h2 id="compare2-heading">)(.*?)(</h2>)', lambda m: f'{m.group(1)}<a href="{href}" style="color:inherit;text-decoration:none;">{m.group(2)}</a>{m.group(3)}', text, count=1, flags=re.S)
        if n:
            changed[path] = new
    return changed


def patch_sitemap(urls):
    """El sitemap que ve Google es el archivo estático sitemap.xml (Vercel lo sirve antes que la redirección a Railway).
    Agrega las URLs generadas que falten; no toca las que ya están."""
    path = ROOT / 'sitemap.xml'
    text = path.read_text()
    add = ''
    for u in urls:
        if f'<loc>{u}</loc>' not in text:
            pri = '0.7' if '/compare' in u or '/comparar' in u else '0.6'
            add += f'  <url>\n    <loc>{u}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>{pri}</priority>\n  </url>\n'
    return {path: text.replace('</urlset>', add + '</urlset>')} if add else {}


def render(ind, lang):
    pre, ref_main, post = split_ref(lang)
    data = ind[lang]
    order_inds = sorted(INDUSTRIES, key=lambda i: i['order'])
    body = build_comparison_main(ind, lang, ref_main) if ind.get('kind') == 'comparison' else build_main(ind, lang, ref_main)
    page = patch_head(pre, ind, lang, data) + body + post
    page = patch_post_and_nav(page, lang, ind, order_inds)
    return faq_schema(page)


def main():
    check = '--check' in sys.argv
    urls, diffs = [], []
    for c in COMPARISONS:
        c['kind'] = 'comparison'
    for ind in sorted(INDUSTRIES, key=lambda i: i['order']) + COMPARISONS:
        for lang in ('en', 'es'):
            path, page = out_path(ind, lang), render(ind, lang)
            urls.append(SITE + url_for(ind, lang))
            if check:
                if not path.exists() or path.read_text() != page:
                    diffs.append(str(path.relative_to(ROOT)))
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(page)
    hubs = {**patch_hubs(), **patch_pricing_links(), **patch_sitemap(urls)}
    if check:
        diffs += [str(p.relative_to(ROOT)) for p in hubs]
        if diffs:
            print('Desactualizadas (corre tools/pages/build.py):', *diffs, sep='\n  ')
            sys.exit(1)
        print('OK: las páginas generadas coinciden con la plantilla.')
        return
    for path, text in hubs.items():
        path.write_text(text)
    print(f'{len(hubs)} índice(s) de industrias con enlaces nuevos: {", ".join(str(p.relative_to(ROOT)) for p in hubs) or "ninguno"}')
    (ROOT / 'tools/pages/sitemap-urls.txt').write_text('\n'.join(urls) + '\n')
    print(f'{len(urls)} páginas escritas. URLs generadas (ya agregadas a sitemap.xml), también en tools/pages/sitemap-urls.txt:')
    print('\n'.join(urls))


if __name__ == '__main__':
    main()
