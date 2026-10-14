#!/usr/bin/env python3
"""MODSTORE static site builder.
   python3 build.py [data/apps.json] --domain https://tumhara-domain.com --out site
Layout fixed hai; yahan sirf APK ka data chhap ke pages bante hain."""
import argparse, base64, collections, html, json, os, re, shutil
from datetime import datetime, timezone
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('data', nargs='?', default=HERE + '/data/apps.json')
ap.add_argument('--out', default=HERE + '/site'); ap.add_argument('--domain', default='https://YOURSITE.com')
A = ap.parse_args(); D = A.domain.rstrip('/'); OUT = A.out
raw = json.load(open(A.data, encoding='utf-8')); raw = raw['apps'] if isinstance(raw, dict) else raw
apps = list({x['app_id']: x for x in raw}.values())
E = lambda s: html.escape(str(s if s is not None else ''), quote=True)
slugify = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower().replace('&', 'and')).strip('-') or 'other'
fmt = lambda n: f'{n/1e6:.1f}M' if n >= 1e6 else f'{n/1e3:.1f}k' if n >= 1e3 else str(n)
today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
SEC = {'safe': 'Safe', 'malware': 'Malware flagged', 'suspicious': 'Suspicious', 'unknown': 'Not scanned'}
SORTS = [('dn', 'Most downloaded'), ('new', 'Latest'), ('r', 'Top rated'), ('n', 'A to Z'), ('sz', 'Smallest')]
pk = collections.Counter(x['package'] for x in apps)
for x in apps:
    x['slug'] = x['package'] if pk[x['package']] == 1 else x['package'] + '-' + x['app_id']
    x['category'] = x.get('category') or 'Other'; x['cs'] = slugify(x['category'])
    x['author'] = x.get('author') or ''; x['security'] = x.get('security') or 'unknown'
    for k in ('description', 'whats_new'):
        x[k] = re.sub(r'https?://appteka\.store/app/\S*', '', x.get(k) or '').strip()
    m = re.search(r'/download/(\d+)/', x.get('download_link') or ''); x['nid'] = int(m.group(1)) if m else 0
    x['downloads'] = x.get('downloads') or 0; x['rating'] = x.get('rating') or 0; x['size_mb'] = x.get('size_mb') or 0
bycat = collections.defaultdict(list)
for x in apps: bycat[(x['cs'], x['category'])].append(x)
for k in bycat: bycat[k].sort(key=lambda x: -x['downloads'])
cats = sorted(bycat.items(), key=lambda kv: -len(kv[1]))
top = sorted(apps, key=lambda x: -x['downloads']); latest = sorted(apps, key=lambda x: -x['nid'])

def img(x, cls='ic', size=56):
    return f'<img class="{cls}" src="{E(x.get("icon"))}" width="{size}" height="{size}" alt="{E(x["name"])} icon" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.visibility=\'hidden\'">'
def card(x, r):
    return (f'<a class="card" href="{r}app/{x["slug"]}.html">{img(x)}<span class="ct"><b>{E(x["name"])}</b><small>{E(x["author"])}</small>'
            f'<small>{E(x["category"])} · v{E(x.get("version"))} · {x["size_mb"]} MB</small></span></a>')
def ldjson(o): return '<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False).replace('</', '<\\/') + '</script>'

def layout(r, title, desc, path, body, cur='', ld=(), noindex=False, image=''):
    can = f'{D}/{path}'
    opts = ''.join(f'<option value="{s}">{E(n)} ({len(v)})</option>' for (s, n), v in cats)
    links = ''.join(f'<a href="{r}category/{s}.html">{E(n)}<small>{len(v)}</small></a>' for (s, n), v in cats)
    sorts = ''.join(f'<option value="{k}">{n}</option>' for k, n in SORTS)
    nav = lambda k, href, ic, t: f'<a href="{r}{href}"{" aria-current=page" if cur == k else ""}><span aria-hidden="true">{ic}</span>{t}</a>'
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        f'<title>{E(title)}</title><meta name="description" content="{E(desc)}">'
        f'<meta name="robots" content="{"noindex,follow" if noindex else "index,follow,max-image-preview:large"}"><link rel="canonical" href="{can}">'
        f'<meta name="theme-color" content="#14213d"><meta property="og:type" content="website"><meta property="og:site_name" content="MODSTORE">'
        f'<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{can}">'
        + (f'<meta property="og:image" content="{E(image)}">' if image else '') +
        f'<meta name="twitter:card" content="summary"><link rel="preconnect" href="https://appteka.store"><link rel="stylesheet" href="{r}assets/style.css">'
        + ''.join(ldjson(o) for o in ld) + '</head><body>'
        f'<header class="top"><button id="mb" aria-label="Open filter menu" aria-expanded="false" aria-controls="sb">☰</button>'
        f'<a class="logo" href="{r}index.html">MOD<b>STORE</b></a><a class="sq" href="{r}search.html" aria-label="Search">⌕</a></header>'
        f'<aside id="sb" aria-label="Filter apps"><b style="font-size:20px">Filter apps</b><form action="{r}apps.html" method="get">'
        f'<label>Search<input type="search" name="q" placeholder="App name"></label><label>Category<select name="cat"><option value="">All categories</option>{opts}</select></label>'
        f'<label>Sort by<select name="sort">{sorts}</select></label><label class="chk"><input type="checkbox" name="safe" value="1"> Safe only</label>'
        f'<button class="btn" type="submit">Apply filter</button></form><nav class="cats" aria-label="Categories"><b>Categories</b>{links}</nav></aside><div id="ov"></div>'
        f'<main class="w">{body}</main>'
        f'<footer><div class="w"><p>© 2026 <b>TWMODS</b></p><p>Powered by <b>TWMODS</b></p></div></footer>'
        f'<nav class="bn" aria-label="Main">{nav("home","index.html","⌂","Home")}{nav("apps","apps.html","▦","Apps")}{nav("search","search.html","⌕","Search")}</nav>'
        f'<script src="{r}assets/site.js" defer></script></body></html>')

def write(path, s):
    p = os.path.join(OUT, path); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w', encoding='utf-8').write(s)

shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
shutil.copytree(HERE + '/assets', OUT + '/assets')
N = len(apps)
# index.json (listing/search ke liye halka data)
json.dump([dict(n=x['name'], s=x['slug'], p=x['package'], i=x.get('icon'), a=x['author'], c=x['category'], cs=x['cs'], v=x.get('version'),
                mb=x['size_mb'], dn=x['downloads'], r=x['rating'], sec=x['security'], id=x['nid']) for x in apps],
          open(OUT + '/index.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# HOME
sec = lambda t, l: f'<h2>{t}</h2><div class="grid">' + ''.join(card(x, '') for x in l) + '</div>'
chips = '<div class="chips">' + ''.join(f'<a href="category/{s}.html">{E(n)} ({len(v)})</a>' for (s, n), v in cats) + '</div>'
write('index.html', layout('', 'MODSTORE – Free Android APK Downloads, Apps & Mods',
    f'Download {N} Android APK apps and mods free. Check version, size and security scan, then get the APK fast on MODSTORE.', '',
    f'<section class="hero"><h1>Free Android APK downloads</h1><p>{N} apps and mods with version, size and security info. Pick an app, wait 10 seconds, download the APK.</p>'
    f'<form class="sf" action="search.html" method="get" role="search"><input type="search" name="q" placeholder="Search apps…" aria-label="Search apps"><button class="btn" type="submit">Search</button></form></section>'
    + sec('Top downloads', top[:24]) + sec('Latest apps', latest[:24]) + f'<h2>Categories</h2>{chips}', 'home',
    [{"@context": "https://schema.org", "@type": "WebSite", "name": "MODSTORE", "url": D + '/',
      "potentialAction": {"@type": "SearchAction", "target": D + "/search.html?q={q}", "query-input": "required name=q"}}]))
# APPS + SEARCH (JS listing)
lst = lambda h, extra: f'<section class="hero"><h1>{h}</h1>{extra}</section><div class="meta" id="meta" aria-live="polite"></div><div class="grid" id="grid"></div><button class="btn alt" id="more" hidden>Load more</button><div id="list"></div>'
write('apps.html', layout('', 'All Android APK Apps & Mods – MODSTORE', f'Browse all {N} Android APK apps. Filter by category, safety and sort by downloads, rating or size.', 'apps.html', lst('All apps', '<p>Use the ☰ menu to filter by category, safety and sort.</p>'), 'apps'))
write('search.html', layout('', 'Search APK apps – MODSTORE', 'Search Android APK apps and mods on MODSTORE.', 'search.html',
    lst('Search apps', '<div class="sf"><input id="sq" type="search" placeholder="Type app name, developer or package…" aria-label="Search apps" autocomplete="off"></div>'), 'search', noindex=True))
# CATEGORY pages
for (s, n), v in cats:
    write(f'category/{s}.html', layout('../', f'{n} APK Downloads ({len(v)} apps) – MODSTORE', f'Download {len(v)} free {n} Android APK apps and mods. Compare versions, sizes and security scans.', f'category/{s}.html',
        f'<nav class="crumb" aria-label="Breadcrumb"><a href="../index.html">Home</a> › {E(n)}</nav><section class="hero"><h1>{E(n)} APKs</h1><p>{len(v)} apps, sorted by downloads.</p></section><div class="grid">' + ''.join(card(x, '../') for x in v) + '</div>', 'apps',
        [{"@context": "https://schema.org", "@type": "CollectionPage", "name": f"{n} APKs", "url": f"{D}/category/{s}.html"}]))
# APP pages
for x in apps:
    s, n = x['slug'], x['name']; url = f'{D}/app/{s}.html'
    d = re.sub(r'\s+', ' ', x['description']).strip()
    desc = f'Download {n} APK v{x.get("version")} ({x["size_mb"]} MB) for Android. ' + (d[:110] + '…' if len(d) > 110 else d)
    shots = [(p.get('preview') or p.get('original'), p.get('original') or p.get('preview')) for p in (x.get('screenshots') or [])] or [(u, u) for u in (x.get('images') or [])]
    shots = [(a, b) for a, b in shots if a]
    rows = [('Package', x['package']), ('Version', f'{x.get("version")} ({x.get("version_code")})'), ('Size', f'{x["size_mb"]} MB'), ('Downloads', f'{x["downloads"]:,}'), ('Category', x['category']), ('Developer', x['author'] or '-')]
    if x['rating']: rows.append(('Rating', f'★ {x["rating"]}'))
    ext = ''.join(f'<a class="btn alt" href="{E(u)}" target="_blank" rel="noopener nofollow">{t}</a>' for t, u in [('Source code', x.get('source_url')), ('Play Store', x.get('play_store_url'))] if u)
    sim = [y for y in bycat[(x['cs'], x['category'])] if y is not x][:6]
    u64 = base64.b64encode((x.get('download_link') or '').encode()).decode()
    warn = f'<div class="warn">Scan result: <b>{SEC[x["security"]].lower()}</b>. Install karne se pehle soch lo.</div>' if x['security'] in ('malware', 'suspicious') else ''
    body = (f'<nav class="crumb" aria-label="Breadcrumb"><a href="../index.html">Home</a> › <a href="../category/{x["cs"]}.html">{E(x["category"])}</a> › {E(n)}</nav>'
        f'<article><div class="ah">{img(x, "ic big", 104)}<div><h1>{E(n)} APK</h1><div>{E(x["author"])} · {E(x["category"])}</div>'
        f'<div class="row"><span class="tag s-{E(x["security"])}">{SEC.get(x["security"], "Not scanned")}</span><span class="tag">v{E(x.get("version"))}</span><span class="tag">{x["size_mb"]} MB</span><span class="tag">{fmt(x["downloads"])} downloads</span></div>'
        f'<div id="dl" data-u="{u64}" data-s="{E(x["security"])}"><button class="btn xl" id="go" type="button">⬇ Download APK</button></div></div></div>{warn}'
        + (f'<div class="shots">' + ''.join(f'<a href="{E(b)}" target="_blank" rel="noopener"><img src="{E(a)}" alt="{E(n)} screenshot" loading="lazy" referrerpolicy="no-referrer"></a>' for a, b in shots) + '</div>' if shots else '')
        + f'<div class="panel"><h2>About {E(n)}</h2><p>{E(x["description"]) or "No description."}</p></div>'
        + (f'<div class="panel"><h2>What\'s new</h2><p>{E(x["whats_new"])}</p></div>' if x['whats_new'] else '')
        + f'<div class="panel"><h2>App info</h2><dl class="i">' + ''.join(f'<div><dt>{k}</dt><dd>{E(v)}</dd></div>' for k, v in rows) + f'</dl><div class="row" style="margin-top:14px">{ext}</div></div></article>'
        + (f'<h2>More {E(x["category"])} apps</h2><div class="grid">' + ''.join(card(y, '../') for y in sim) + '</div>' if sim else ''))
    ld = [{"@context": "https://schema.org", "@type": "SoftwareApplication", "name": n, "operatingSystem": "ANDROID", "applicationCategory": "MobileApplication",
           "softwareVersion": str(x.get('version') or ''), "fileSize": f'{x["size_mb"]} MB', "description": d[:300], "url": url, **({"image": x['icon']} if x.get('icon') else {}),
           **({"author": {"@type": "Organization", "name": x['author']}} if x['author'] else {})},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": D + '/'},
              {"@type": "ListItem", "position": 2, "name": x['category'], "item": f"{D}/category/{x['cs']}.html"},
              {"@type": "ListItem", "position": 3, "name": n, "item": url}]}]
    write(f'app/{s}.html', layout('../', f'{n} APK v{x.get("version")} Download – MODSTORE', desc, f'app/{s}.html', body, 'apps', ld, image=x.get('icon') or ''))
# SITEMAP (har build pe sab pages se auto)
urls = [('', 1.0, 'daily'), ('apps.html', 0.8, 'daily')] + [(f'category/{s}.html', 0.7, 'weekly') for (s, _), _ in cats] + [(f'app/{x["slug"]}.html', 0.6, 'weekly') for x in apps]
def smap(us): return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{E(D + "/" + p)}</loc><lastmod>{today}</lastmod><changefreq>{c}</changefreq><priority>{pr}</priority></url>\n' for p, pr, c in us) + '</urlset>'
if len(urls) <= 45000: write('sitemap.xml', smap(urls))
else:
    ch = [urls[i:i + 45000] for i in range(0, len(urls), 45000)]
    for i, c in enumerate(ch, 1): write(f'sitemap-{i}.xml', smap(c))
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<sitemap><loc>{D}/sitemap-{i}.xml</loc><lastmod>{today}</lastmod></sitemap>\n' for i in range(1, len(ch) + 1)) + '</sitemapindex>')
write('robots.txt', f'User-agent: *\nAllow: /\nDisallow: /search.html\n\nSitemap: {D}/sitemap.xml\n')
write('404.html', f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Page not found – MODSTORE</title></head><body style="font-family:system-ui;text-align:center;padding:60px 20px"><h1>404 – Page not found</h1><p><a href="{D}/">Go to MODSTORE home</a></p></body></html>')
print(f'built {N} app pages, {len(cats)} category pages, {len(urls)} sitemap urls -> {OUT}')
