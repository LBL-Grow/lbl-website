#!/usr/bin/env python3
"""Genera las páginas en español (Colombia) en /es-co/ a partir de las páginas en inglés.

Uso:  python3 tools/i18n/build.py          genera /es-co/ y marca las páginas en inglés con hreflang
      python3 tools/i18n/build.py --check  solo avisa de textos sin traducir

El sitio sigue sin paso de build: el HTML generado se guarda en el repositorio.
Cuando cambie una página en inglés: `python3 tools/i18n/extract.py`, traducir lo nuevo en
tools/i18n/es-co/<clave>.txt y volver a correr este script.

Formato de tools/i18n/es-co/<clave>.txt: una línea por texto, `<posición>|<texto en español>`.
  - Lo que no esté ahí se busca en _shared.json (textos repetidos entre páginas).
  - `@@DROP:<clase o etiqueta>@@` elimina el elemento contenedor con esa clase o etiqueta.
  - `@@EMPTY@@` deja el texto vacío. Un rango `42-49|...` aplica el mismo valor a varias posiciones.
"""
import json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from extract import ROOT, PAGES, TOK, ATTR, META_OK, clean

SITE = 'https://localboostlab.com'
I18N = ROOT / 'tools/i18n/es-co'
SHARED = json.load(open(I18N / '_shared.json'))
JS = json.load(open(I18N / '_js.json'))
PATCHES = json.load(open(I18N / '_patches.json'))
LINKS = {c['en']: c['es'] for c in PAGES.values()}
VOID = {'br', 'img', 'input', 'meta', 'link', 'hr', 'source'}


def load_page(key):
    out = {}
    path = I18N / f'{key}.txt'
    if path.exists():
        for line in path.read_text().splitlines():
            if not line.strip() or line.startswith('#'):
                continue
            i, _, es = line.partition('|')
            a, _, b = i.partition('-')
            for n in range(int(a), int(b or a) + 1):
                out[n] = es.strip()
    return out


def memory():
    """Traducciones ya hechas en otras páginas, por texto exacto: último recurso."""
    mem = {}
    for key in PAGES:
        src = I18N / 'src' / f'{key}.json'
        if not src.exists():
            continue
        page = load_page(key)
        for item in json.load(open(src)):
            es = page.get(item['i'])
            if es and '@@' not in es:
                mem.setdefault(item['en'].strip(), es)
    return mem


MEMORY = memory()


def translate(html, key, missing):
    page = load_page(key)
    n = [0]

    def tr(en):
        i = n[0]
        n[0] += 1
        if i in page:
            es = page[i]
        elif en.strip() in SHARED:
            es = SHARED[en.strip()]
        elif en.strip() in MEMORY:
            es = MEMORY[en.strip()]
        else:
            missing.append((key, i, en.strip()))
            return en
        if es == '@@EMPTY@@':
            es = ''
        lead = en[:len(en) - len(en.lstrip())]
        trail = en[len(en.rstrip()):]
        return lead + es + trail

    out = []
    for part in TOK.split(html):
        if not part:
            continue
        if part.startswith('<'):
            low = part[:8].lower()
            skip = (low.startswith(('<script', '<style', '<!--'))
                    or (part.lower().startswith('<meta') and not META_OK.search(part))
                    or part.lower().startswith(('<link', '<html', '<body', '<head', '</')))
            if not skip:
                def sub(m, tag=part):
                    name, val = m.group(1), m.group(2)
                    if name == 'content' and not tag.lower().startswith('<meta'):
                        return m.group(0)
                    if name == 'value' and not re.search(r'type="(submit|button)"', tag):
                        return m.group(0)
                    if re.search(r'[A-Za-z]{2}', val) and not val.startswith(('http', '/', '#')):
                        return f'{name}="{tr(val)}"'
                    return m.group(0)
                part = ATTR.sub(sub, part)
            out.append(part)
        else:
            # En Colombia "$97" se lee como pesos: los precios en dólares van como US$97.
            out.append(tr(part) if re.search(r'[A-Za-z]{2}', part) else re.sub(r'(?<![A-Z])\$(?=\d)', 'US$', part))
    return ''.join(out)


def element_bounds(html, pos, target):
    """Límites del elemento más cercano que contiene `pos` y cuya etiqueta o clase es `target`."""
    opens = list(re.finditer(r'<([a-zA-Z0-9]+)\b([^>]*)>', html[:pos]))
    for m in reversed(opens):
        tag, attrs = m.group(1).lower(), m.group(2)
        cls = re.search(r'class="([^"]*)"', attrs)
        if tag != target and not (cls and target in cls.group(1).split()):
            continue
        if tag in VOID:
            continue
        depth, end = 0, None
        for t in re.finditer(rf'<(/?){tag}\b[^>]*>', html[m.start():], re.I):
            depth += -1 if t.group(1) else 1
            if depth == 0:
                end = m.start() + t.end()
                break
        if end and end > pos:
            return m.start(), end
    raise SystemExit(f'DROP: no encontré <{target}> alrededor de la posición {pos}')


def apply_drops(html):
    while True:
        m = re.search(r'@@DROP:([\w-]+)@@', html)
        if not m:
            return html
        a, b = element_bounds(html, m.start(), m.group(1))
        html = html[:a] + html[b:]


def rewrite_links(html):
    def sub(m):
        url = m.group(2)
        path, sep, rest = re.match(r'([^#?]*)([#?]?)(.*)', url).groups()
        norm = path.rstrip('/') or '/'
        if norm in LINKS:
            return f'{m.group(1)}"{LINKS[norm]}{sep}{rest}"'
        return m.group(0)
    return re.sub(r'(\bhref=)"(/[^"]*)"', sub, html)


def apply_patches(html, key):
    """Ajustes propios de la versión Colombia que no son traducción (p. ej. plan único en pesos).

    _patches.json: {"*": {...}, "<clave>": {...}} con
      "drop":    [[texto, clase o etiqueta], ...]  elimina el elemento contenedor de cada aparición del texto
      "replace": [[antes, después], ...]          reemplazo literal en el HTML final
    """
    for scope in ('*', key):
        cfg = PATCHES.get(scope, {})
        for marker, target in cfg.get('drop', []):
            while marker in html:
                a, b = element_bounds(html, html.index(marker), target)
                html = html[:a] + html[b:]
        for old, new in cfg.get('replace', []):
            html = html.replace(old, new)
    css = PATCHES.get('css')
    if css:
        html = html.replace('</head>', f'  <style data-es-co>{css}</style>\n</head>', 1)
    # Ajustes de accesibilidad y uso táctil solo para es-CO (archivo aparte, no se duplica en cada página).
    html = html.replace('</head>', '  <link rel="stylesheet" href="/es-co/es-co.css?v=14">\n</head>', 1)
    return html


def absolute_assets(html, src):
    """Las rutas relativas (p. ej. `styles.css`) dejan de servir al mover la página a /es-co/: se vuelven absolutas."""
    base = '/' + '/'.join(src.split('/')[:-1])
    base = base.rstrip('/') + '/'
    return re.sub(r'\b(href|src)="(?!/|#|[a-zA-Z][a-zA-Z0-9+.-]*:)([^"]+)"',
                  lambda m: f'{m.group(1)}="{base}{m.group(2)}"', html)


def hreflang_block(cfg):
    en, es = SITE + cfg['en'].rstrip('/'), SITE + cfg['es']
    en = en or SITE
    return ('<!-- hreflang:start -->\n'
            f'  <link rel="alternate" hreflang="en" href="{en}">\n'
            f'  <link rel="alternate" hreflang="es-CO" href="{es}">\n'
            f'  <link rel="alternate" hreflang="x-default" href="{en}">\n'
            '  <!-- hreflang:end -->')


def set_hreflang(html, cfg):
    block = hreflang_block(cfg)
    if '<!-- hreflang:start -->' in html:
        return re.sub(r'<!-- hreflang:start -->.*?<!-- hreflang:end -->', block, html, flags=re.S)
    return re.sub(r'(<link rel="canonical"[^>]*>)', lambda m: m.group(1) + '\n  ' + block, html, count=1)


PILL = 'border:1px solid rgba(255,255,255,.5);border-radius:999px;padding:4px 12px;white-space:nowrap'


# El enlace de idioma ocupa sitio en el menú: se evita que los enlaces partan en dos líneas.
# `.grid-3>*{min-width:0}` corrige un desborde lateral de las tarjetas de precios entre 1025 y 1200 px.
# `.nav__lang-m` es el enlace de idioma de la cabecera en móvil (el menú de escritorio se oculta bajo 1024 px).
NAV_CSS = ('  <style data-lang-nav>.grid-3>*{min-width:0}.nav__links a{white-space:nowrap}'
           '@media(max-width:1600px){.nav__links{gap:14px}.nav__links a{font-size:.84rem}.nav__cta{padding-left:16px;padding-right:16px}}'
           '.nav__lang-m{display:none}'
           '@media(max-width:1024px){.nav__lang-m{display:inline-flex;align-items:center;margin-left:auto;margin-right:14px;'
           'color:#fff;font-size:.8rem;font-weight:600}}</style>')
# La barra promocional de la home tapaba la mitad superior del menú fijo (y con él el enlace de idioma):
# el menú se coloca justo debajo de la barra mientras esta se ve.
NAV_JS = ('<script data-lang-nav>(function(){var p=document.getElementById("promo-bar"),n=document.querySelector("nav.nav");'
          'if(!p||!n)return;function f(){n.style.top=(p.offsetParent===null?0:Math.max(0,p.getBoundingClientRect().bottom))+"px"}'
          'f();addEventListener("load",f);addEventListener("scroll",f,{passive:true});addEventListener("resize",f);'
          'p.addEventListener("click",function(){setTimeout(f,0)})})()</script>')


def append_inside(html, cls, snippet):
    """Inserta `snippet` justo antes del cierre del primer <div class="cls ...">."""
    m = re.search(rf'<div class="{cls}"[^>]*>', html)
    if not m:
        return html
    depth = 0
    for t in re.finditer(r'<(/?)div\b[^>]*>', html[m.start():]):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            at = m.start() + t.start()
            return html[:at] + snippet + html[at:]
    return html


def set_lang_link(html, href, hreflang, label):
    """Enlace de cambio de idioma: cabecera (escritorio y móvil), menú móvil y pie."""
    attrs = f'href="{href}" hreflang="{hreflang}" lang="{hreflang[:2]}" data-lang-switch'
    short = {'en': 'EN', 'es-CO': 'ES'}[hreflang]
    pill = f'style="{PILL}" title="{label}" aria-label="{label}"'
    html = clean(html)
    html = re.sub(r'\s*<(style|script) data-lang-nav>.*?</\1>', '', html, flags=re.S)
    html = html.replace('</head>', NAV_CSS + '\n</head>', 1)
    html = html.replace('</body>', NAV_JS + '\n</body>', 1)
    html = append_inside(html, 'nav__links', f'  <a {attrs} {pill}>{short}</a>\n    ')
    html = re.sub(r'(<button class="nav__hamburger")', lambda m: f'<a {attrs} class="nav__lang-m" {pill}>{short}</a>\n    ' + m.group(1), html, count=1)
    html = re.sub(r'(<div class="nav__mobile-overlay"[^>]*>)', lambda m: m.group(1) + f'\n  <a {attrs}>{label}</a>', html, count=1)
    return re.sub(r'(<div class="footer__bottom">)', lambda m: m.group(1) + f'\n      <span><a {attrs}>{label}</a></span>', html, count=1)


def jsonld(cfg, title, desc):
    data = {
        '@context': 'https://schema.org',
        '@type': 'WebPage',
        'url': SITE + cfg['es'],
        'name': title,
        'description': desc,
        'inLanguage': 'es-CO',
        'isPartOf': {'@type': 'WebSite', 'name': 'Local Boost Lab', 'url': SITE},
        'publisher': {'@type': 'Organization', 'name': 'Local Boost Lab', 'url': SITE,
                      'logo': SITE + '/Logo_vertical_yellow_white_60.png', 'email': 'hello@localboostlab.com'},
    }
    return '<script type="application/ld+json">\n' + json.dumps(data, ensure_ascii=False, indent=2) + '\n</script>'


def head(html, cfg):
    url = SITE + cfg['es']
    html = html.replace('<html lang="en">', '<html lang="es-CO">', 1)
    html = re.sub(r'<link rel="canonical"[^>]*>', f'<link rel="canonical" href="{url}">', html, count=1)
    html = re.sub(r'(<meta property="og:url" content=")[^"]*"', rf'\g<1>{url}"', html)
    if 'og:locale' not in html:
        html = re.sub(r'(<link rel="canonical"[^>]*>)', r'\1\n  <meta property="og:locale" content="es_CO">', html, count=1)
    # El marcado en inglés trae datos que no se pueden sostener (calificación 4.9 / 47): se reemplaza por uno mínimo.
    title = re.search(r'<title>(.*?)</title>', html, re.S).group(1).strip()
    desc = re.search(r'<meta name="description" content="([^"]*)"', html).group(1)
    blocks = list(re.finditer(r'[ \t]*(<!--[^>]*JSON-LD[^>]*-->\s*)?<script type="application/ld\+json">.*?</script>\n?', html, re.S))
    for m in reversed(blocks):
        html = html[:m.start()] + html[m.end():]
    html = html.replace('</head>', '  ' + jsonld(cfg, title, desc).replace('\n', '\n  ') + '\n</head>', 1)
    return set_hreflang(html, cfg)


def js_strings(html, key):
    pairs = JS.get('*', []) + JS.get(key, [])
    def sub(m):
        body = m.group(0)
        for en, es in pairs:
            body = body.replace(en, es)
        return body
    return re.sub(r'<script\b(?![^>]*ld\+json)[^>]*>.*?</script>', sub, html, flags=re.S)


def main():
    check = '--check' in sys.argv
    missing = []
    for key, cfg in PAGES.items():
        src = ROOT / cfg['src']
        en_html = src.read_text()
        html = translate(clean(en_html), key, missing)
        html = apply_drops(html)
        html = absolute_assets(html, cfg['src'])
        html = rewrite_links(html)
        html = head(html, cfg)
        html = js_strings(html, key)
        html = set_lang_link(html, cfg['en'], 'en', 'English')
        html = apply_patches(html, key)
        if not check:
            dst = ROOT / cfg['dst']
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(html)
            # `tag`: la página en inglés que se sirve en esa URL cuando no es la misma que se usó como fuente.
            en_file = ROOT / cfg.get('tag', cfg['src'])
            en_old = en_file.read_text()
            en_new = set_lang_link(set_hreflang(en_old, cfg), cfg['es'], 'es-CO', 'Español')
            if en_new != en_old:
                en_file.write_text(en_new)
    if missing:
        print(f'{len(missing)} textos sin traducir:')
        for key, i, en in missing:
            print(f'  {key} {i} | {en[:110]}')
        sys.exit(1 if not check else 0)
    print('OK: todo traducido')


if __name__ == '__main__':
    main()
