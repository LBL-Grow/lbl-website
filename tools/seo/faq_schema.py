#!/usr/bin/env python3
"""FAQPage JSON-LD generado desde las preguntas visibles de cada página.

El marcado sale del mismo HTML que ve el visitante (`.faq-item` > `.faq-question` + `.faq-answer`), así que no puede
contar nada que la página no muestre. Es idempotente: reemplaza el bloque anterior y no toca una página que ya tenga un
FAQPage escrito a mano.

Uso:  python3 tools/seo/faq_schema.py how-it-works.html [otras.html ...]
      (las páginas de /es-co/ lo reciben solas desde tools/i18n/build.py)
"""
import html as _html
import json
import re
import sys

START, END = '<!-- faq-schema:start -->', '<!-- faq-schema:end -->'
ITEM = re.compile(
    r'<div class="faq-item[^"]*">\s*<button class="faq-(?:question|btn)"[^>]*>(?P<q>.*?)</button>\s*'
    r'<div[^>]*class="faq-answer[^"]*"[^>]*>(?P<a>.*?)</div>\s*</div>', re.S)


def text(fragment):
    fragment = re.sub(r'<span class="icon">.*?</span>|<svg.*?</svg>', '', fragment, flags=re.S)
    fragment = re.sub(r'<[^>]+>', ' ', fragment)
    return re.sub(r'\s+', ' ', _html.unescape(fragment)).strip()


def faq_schema(page):
    # Una página con su propio FAQPage manual (inglés) se deja como está.
    manual = re.sub(re.escape(START) + r'.*?' + re.escape(END), '', page, flags=re.S)
    if re.search(r'"@type"\s*:\s*"FAQPage"', manual):
        return page
    items = [(text(m['q']), text(m['a'])) for m in ITEM.finditer(page)]
    items = [(q, a) for q, a in items if q and a]
    page = re.sub(r'\s*' + re.escape(START) + r'.*?' + re.escape(END), '', page, flags=re.S)
    if not items:
        return page
    data = {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in items],
    }
    block = f'  {START}\n  <script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>\n  {END}\n'
    return page.replace('</head>', block + '</head>', 1)


if __name__ == '__main__':
    for path in sys.argv[1:]:
        src = open(path, encoding='utf-8').read()
        out = faq_schema(src)
        if out != src:
            open(path, 'w', encoding='utf-8').write(out)
            print('FAQPage actualizado:', path)
        else:
            print('sin cambios:', path)
