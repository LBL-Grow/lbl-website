#!/usr/bin/env python3
"""Blog en inglés como páginas propias, sitemap y redirecciones.

Uso:  python3 tools/blog/build_en.py

Los artículos en inglés viven en la base de datos (se publican desde /blog-admin) y blog/post.html los pinta
en el navegador con /blog/post?slug=...; así Google no ve título, texto ni canonical. Este script lee los
artículos publicados de /api/blog y escribe una página estática por artículo en blog/<slug>.html a partir de
blog/post.html (mismo diseño), igual que tools/i18n/build.py hace con el blog en español. Además:
  - vercel.json: redirección permanente de /blog/post?slug=<slug> a /blog/<slug> para cada artículo generado.
  - sitemap.xml: agrega /free-audit y los artículos, y pone en lastmod la fecha del último cambio de cada archivo.
Hay que correrlo de nuevo cada vez que se publique o edite un artículo en inglés. No toca blog/post.html ni
blog/index.html: un artículo nuevo sigue abriendo con /blog/post?slug=... hasta que se regenere.
"""
import html as _html, json, pathlib, re, subprocess, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
SITE = 'https://localboostlab.com'
API = SITE + '/api/blog'
MARK = 'blog-static'


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'lbl-build'})
    return json.load(urllib.request.urlopen(req, timeout=40))


def load_posts():
    data = fetch(API)
    posts = data if isinstance(data, list) else data.get('posts') or data.get('data') or []
    out = []
    for p in posts:
        if p.get('status') and p['status'] != 'published':
            continue
        if p.get('body') is None:
            full = fetch(f"{API}/{p['slug']}")
            p = full.get('post') or full
        out.append(p)
    return sorted(out, key=lambda x: x.get('published_at') or '', reverse=True)


def clean_body(post):
    """Arregla dos defectos de texto pegado desde un editor: espacios duros entre todas las palabras
    (impiden el salto de línea y desbordan la página) y un <h1> dentro del cuerpo que repite el título."""
    body = (post.get('body') or '').replace('&nbsp;', ' ').replace('\u00a0', ' ')
    norm = lambda t: re.sub(r'\W+', ' ', _html.unescape(re.sub(r'<[^>]+>', '', t))).strip().lower()
    def h1(m):
        return '' if norm(m.group(2)) == norm(post['title']) else f'<h2{m.group(1)}>{m.group(2)}</h2>'
    return re.sub(r'<h1([^>]*)>(.*?)</h1>', h1, body, flags=re.S)


def abs_url(u):
    return SITE + u if u and u.startswith('/') else u


def jsonld(post, url):
    data = {
        '@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': post['title'],
        'description': post.get('meta_description') or post.get('excerpt') or post['title'], 'inLanguage': 'en-US',
        'datePublished': post['published_at'], 'dateModified': post.get('updated_at') or post['published_at'],
        'mainEntityOfPage': url,
        'author': {'@type': 'Organization', 'name': 'Local Boost Lab', 'url': SITE},
        'publisher': {'@type': 'Organization', 'name': 'Local Boost Lab', 'url': SITE,
                      'logo': {'@type': 'ImageObject', 'url': SITE + '/Logo_vertical_yellow_white_60.png'}},
    }
    if post.get('cover_image_url'):
        data['image'] = abs_url(post['cover_image_url'])
    return '<script type="application/ld+json">\n' + json.dumps(data, ensure_ascii=False, indent=2) + '\n</script>'


def build_page(shell, post):
    slug = post['slug']
    url = f'{SITE}/blog/{slug}'
    title = _html.escape(f"{post['title']} | Local Boost Lab Blog", quote=False)
    desc = _html.escape(post.get('meta_description') or post.get('excerpt') or post['title'], quote=True)
    h = shell
    h = re.sub(r'(<title[^>]*>).*?(</title>)', lambda m: m.group(1) + title + m.group(2), h, count=1, flags=re.S)
    h = re.sub(r'(<meta name="description"[^>]*?content=")[^"]*"', lambda m: m.group(1) + desc + '"', h, count=1)
    h = re.sub(r'\s*<link rel="canonical"[^>]*>', '', h)
    data = json.dumps({k: post.get(k) for k in ('title', 'excerpt', 'body', 'tags', 'published_at', 'cover_image_url', 'slug', 'status')},
                      ensure_ascii=False).replace('</', '<\\/')
    head = (f'  <link rel="canonical" href="{url}">\n'
            f'  <meta property="og:type" content="article">\n'
            f'  <meta property="og:url" content="{url}">\n'
            f'  <meta property="og:title" content="{_html.escape(post["title"], quote=True)}">\n'
            f'  <meta property="og:description" content="{desc}">\n'
            + (f'  <meta property="og:image" content="{abs_url(post["cover_image_url"])}">\n' if post.get('cover_image_url') else '')
            + '  ' + jsonld(post, url) + '\n'
            + f'  <script data-{MARK}>window.__LBL_POST__=' + data + ';</script>\n')
    h = h.replace('</head>', head + '</head>', 1)
    # La página estática ya trae el artículo: no hace falta pedirlo a la API.
    needle = "var params = new URLSearchParams(window.location.search);"
    assert h.count(needle) == 1, 'blog/post.html cambió: revisar loadPost()'
    h = h.replace(needle, 'if (window.__LBL_POST__) { showPost(window.__LBL_POST__); return; }\n    ' + needle, 1)
    noscript = (f'\n<noscript><div style="max-width:760px;margin:0 auto;padding:120px 24px 40px;">'
                f'<h1>{_html.escape(post["title"], quote=False)}</h1>{post.get("body") or ""}</div></noscript>')
    assert re.search(r'<main[^>]*>', h), 'blog/post.html sin <main>'
    h = re.sub(r'(<main[^>]*>)', lambda m: m.group(1) + noscript, h, count=1)
    # El enlace de idioma del pie apunta al blog en español (la plantilla apunta a una página sin contenido).
    h = h.replace('href="/es-co/blog/articulo"', 'href="/es-co/blog"')
    return h


def git_date(path):
    r = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', path], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return r or None


def file_for(path):
    """Archivo del repositorio que sirve una ruta del sitio (cleanUrls)."""
    p = path.strip('/')
    for cand in ([p + '.html', p + '/index.html'] if p else ['index.html']):
        if (ROOT / cand).is_file():
            return cand
    return None


def url_block(loc, lastmod, freq, prio):
    return (f'  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n'
            f'    <changefreq>{freq}</changefreq>\n    <priority>{prio}</priority>\n  </url>\n')


def update_sitemap(posts):
    sm = ROOT / 'sitemap.xml'
    t = sm.read_text()
    # artículos en inglés: se quitan y se vuelven a poner (los de /es-co/blog los maneja tools/i18n/build.py)
    t = re.sub(r'  <url>\n    <loc>https://localboostlab\.com/blog/[^<]+</loc>.*?</url>\n', '', t, flags=re.S)
    t = re.sub(r'  <url>\n    <loc>https://localboostlab\.com/free-audit</loc>.*?</url>\n', '', t, flags=re.S)
    add = url_block(SITE + '/free-audit', git_date('free-audit.html') or '2026-10-13', 'monthly', '0.7')
    add += ''.join(url_block(f"{SITE}/blog/{p['slug']}", (p.get('updated_at') or p['published_at'])[:10], 'monthly', '0.6') for p in posts)
    anchor = '  <url>\n    <loc>https://localboostlab.com/es-co</loc>'
    t = t.replace(anchor, add + anchor, 1) if anchor in t else t.replace('</urlset>', add + '</urlset>')

    # lastmod real de las páginas fijas (los artículos conservan su fecha de publicación o edición)
    def fix(m):
        loc = m.group(1)
        path = loc.replace(SITE, '')
        if path.startswith('/blog/') or path.startswith('/es-co/blog/'):
            return m.group(0)
        f = file_for(path)
        d = git_date(f) if f else None
        return m.group(0) if not d else re.sub(r'<lastmod>[^<]*</lastmod>', f'<lastmod>{d}</lastmod>', m.group(0))
    t = re.sub(r'  <url>\n    <loc>([^<]+)</loc>.*?</url>\n', fix, t, flags=re.S)
    sm.write_text(t)


def update_redirects(posts):
    """Una línea por artículo, insertada como texto para no reordenar ni reformatear el resto de vercel.json."""
    vj = ROOT / 'vercel.json'
    t = vj.read_text()
    t = re.sub(r'    \{ "source": "/blog/post", "has": [^\n]*\n', '', t)
    lines = ''.join('    { "source": "/blog/post", "has": [{ "type": "query", "key": "slug", "value": "%s" }], '
                    '"destination": "/blog/%s", "permanent": true },\n' % (re.escape(p['slug']).replace('\\-', '-'), p['slug']) for p in posts)
    head = '  "redirects": [\n'
    assert t.count(head) == 1, 'vercel.json: no encuentro la lista de redirecciones'
    t = t.replace(head, head + lines, 1)
    json.loads(t)  # debe seguir siendo JSON válido
    vj.write_text(t)


def main():
    shell = (ROOT / 'blog/post.html').read_text()
    posts = load_posts()
    assert posts, 'la API no devolvió artículos publicados'
    for p in posts:
        p['body'] = clean_body(p)
    reserved = {'index', 'post', 'post-template'}
    for p in posts:
        assert re.fullmatch(r'[A-Za-z0-9._-]+', p['slug']) and p['slug'] not in reserved, f"slug no válido: {p['slug']}"
        (ROOT / f"blog/{p['slug']}.html").write_text(build_page(shell, p))
    update_sitemap(posts)
    update_redirects(posts)
    print(f'OK: {len(posts)} artículos en blog/, sitemap y redirecciones actualizados')


if __name__ == '__main__':
    main()
