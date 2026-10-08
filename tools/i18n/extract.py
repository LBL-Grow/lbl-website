#!/usr/bin/env python3
"""Extrae los textos traducibles de cada página en inglés (public/) a i18n/es-co/src/<clave>.json.
Cada entrada lleva su posición, de modo que el mismo texto puede traducirse distinto según el contexto."""
import json, re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PAGES = json.load(open(ROOT / 'tools/i18n/pages.json'))
TOK = re.compile(r'(<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->|<[^>]+>)', re.S | re.I)
ATTR = re.compile(r'\b(alt|aria-label|placeholder|title|content|value|data-label)="([^"]*)"')
META_OK = re.compile(r'(name|property)="(description|og:title|og:description|twitter:title|twitter:description|og:image:alt)"')

SWITCH = re.compile(r'\s*(?:<span>)?<a [^>]*data-lang-switch[^>]*>[^<]*</a>(?:</span>)?')


def clean(html):
    """Quita el enlace de cambio de idioma que añade build.py, para que las posiciones no se muevan."""
    return SWITCH.sub('', html)


def segments(html):
    """Devuelve [(tipo, texto)] en orden: 'text', 'attr:<nombre>', 'title'."""
    out = []
    parts = TOK.split(clean(html))
    in_title = False
    for part in parts:
        if not part:
            continue
        if part.startswith('<'):
            low = part[:8].lower()
            if low.startswith('<script') or low.startswith('<style') or low.startswith('<!--'):
                continue
            if part.lower().startswith('<meta') and not META_OK.search(part):
                continue
            if part.lower().startswith(('<link', '<html', '<body', '<head', '</')):
                continue
            for m in ATTR.finditer(part):
                name, val = m.group(1), m.group(2)
                if name == 'content' and not part.lower().startswith('<meta'):
                    continue
                if name == 'value' and not re.search(r'type="(submit|button)"', part):
                    continue
                if re.search(r'[A-Za-z]{2}', val) and not val.startswith(('http', '/', '#')):
                    out.append(('attr:' + name, val))
        else:
            if re.search(r'[A-Za-z]{2}', part):
                out.append(('text', part))
    return out

if __name__ == '__main__':
    (ROOT / 'tools/i18n/es-co/src').mkdir(parents=True, exist_ok=True)
    for key, cfg in PAGES.items():
        html = (ROOT / cfg['src']).read_text()
        segs = segments(html)
        json.dump([{'i': i, 'k': k, 'en': v} for i, (k, v) in enumerate(segs)],
                  open(ROOT / f'tools/i18n/es-co/src/{key}.json', 'w'), ensure_ascii=False, indent=1)
        print(key, len(segs))
