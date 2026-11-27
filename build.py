"""Build the static wiki from _src bundles. Open index.html afterwards."""

from html import escape
from html.parser import HTMLParser
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent
SITE = "https://notnomoro.github.io/teams-scraper-wiki"

UI = {
    "es": {
        "lang": "es",
        "other_prefix": "en/",
        "other_name": "English",
        "this_name": "Español",
        "search": "Buscar",
        "toc": "En esta página",
        "menu": "Menú",
        "copy": "Copiar",
        "copied": "Copiado",
        "prev": "Anterior",
        "next": "Siguiente",
        "version": "Guía 1.0.0",
        "footer": 'Paquete público <a href="https://github.com/notnomoro/teams-scraper">teams-scraper</a> · MIT · <a href="https://github.com/notnomoro/teams-scraper/issues">Problemas</a> · <a href="https://github.com/notnomoro/teams-scraper/releases">Descargas</a>',
    },
    "en": {
        "lang": "en",
        "other_prefix": "../",
        "other_name": "Español",
        "this_name": "English",
        "search": "Search",
        "toc": "On this page",
        "menu": "Menu",
        "copy": "Copy",
        "copied": "Copied",
        "prev": "Previous",
        "next": "Next",
        "version": "Guide 1.0.0",
        "footer": 'Public package <a href="https://github.com/notnomoro/teams-scraper">teams-scraper</a> · MIT · <a href="https://github.com/notnomoro/teams-scraper/issues">Issues</a> · <a href="https://github.com/notnomoro/teams-scraper/releases">Releases</a>',
    },
}


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = False

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def plain(html):
    parser = TextExtractor()
    parser.feed(html)
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def parse_bundle(lang):
    raw = (ROOT / "_src" / f"{lang}.bundle").read_text(encoding="utf-8")
    groups = []
    pages = []
    current = None
    for block in re.split(r"\n(?=##### |===== )", raw.strip()):
        if block.startswith("##### "):
            group_id, label = block[6:].strip().split(" | ", 1)
            current = {"id": group_id, "label": label}
            groups.append(current)
            continue
        header, body = block.split("\n", 1)
        slug, nav, title = header[6:].split(" | ", 2)
        if "\n---\n" in body:
            body = body.split("\n---\n", 1)[1]
        pages.append({
            "slug": slug.strip(),
            "nav": nav.strip(),
            "title": title.strip(),
            "group": current["id"] if current else "",
            "group_label": current["label"] if current else "",
            "html": body.strip(),
        })
    return groups, pages


def href_for(slug):
    return "index.html" if slug == "index" else f"{slug}.html"


def meta_description(html_body):
    match = re.search(r'<p class="lede">(.*?)</p>', html_body, re.S)
    if not match:
        match = re.search(r"<p>(.*?)</p>", html_body, re.S)
    text = plain(match.group(1) if match else html_body)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= 160:
        return text
    return text[:157].rsplit(" ", 1)[0] + "…"


def page_url(lang, slug):
    if lang == "es":
        return SITE + ("/" if slug == "index" else f"/{slug}.html")
    return SITE + ("/en/" if slug == "index" else f"/en/{slug}.html")


def document_title(ui, page):
    if page["slug"] == "index" and ui["lang"] == "es":
        return "Teams Scraper: guía para leer el Microsoft Teams de clase"
    if page["slug"] == "index":
        return "Teams Scraper: guide for reading class Microsoft Teams"
    return f'{page["title"]} · Teams Scraper'


def seo_head(ui, page, description):
    lang = ui["lang"]
    other = "en" if lang == "es" else "es"
    canon = page_url(lang, page["slug"])
    alt = page_url(other, page["slug"])
    title = escape(document_title(ui, page), quote=True)
    desc = escape(description, quote=True)
    locale = "es_MX" if lang == "es" else "en_US"
    alt_locale = "en_US" if lang == "es" else "es_MX"
    blocks = [
        f'<meta name="description" content="{desc}">',
        f'<link rel="canonical" href="{canon}">',
        f'<link rel="alternate" hreflang="{lang}" href="{canon}">',
        f'<link rel="alternate" hreflang="{other}" href="{alt}">',
        f'<link rel="alternate" hreflang="x-default" href="{page_url("es", page["slug"])}">',
        f'<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="Teams Scraper">',
        f'<meta property="og:locale" content="{locale}">',
        f'<meta property="og:locale:alternate" content="{alt_locale}">',
        f'<meta property="og:title" content="{title}">',
        f'<meta property="og:description" content="{desc}">',
        f'<meta property="og:url" content="{canon}">',
        f'<meta name="twitter:card" content="summary">',
        f'<meta name="twitter:title" content="{title}">',
        f'<meta name="twitter:description" content="{desc}">',
    ]
    if page["slug"] == "index":
        data = {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "Teams Scraper",
            "applicationCategory": "EducationalApplication",
            "operatingSystem": "Windows, macOS, Linux",
            "softwareRequirements": "Python 3.11, Selenium 4",
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "description": description,
            "url": "https://github.com/notnomoro/teams-scraper",
            "softwareHelp": {"@type": "WebSite", "name": "Teams Scraper guide", "url": canon},
            "inLanguage": ["es", "en"],
            "license": "https://opensource.org/license/mit",
        }
        raw = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
        blocks.append(f'<script type="application/ld+json">{raw}</script>')
    return "\n  ".join(blocks)


def page_shell(ui, page, pages, asset, media, search_src, description):
    index = pages.index(page)
    prev_link = ""
    next_link = ""
    if index > 0:
        prev_page = pages[index - 1]
        prev_link = f'<a href="{href_for(prev_page["slug"])}"><small>{ui["prev"]}</small>{prev_page["nav"]}</a>'
    if index + 1 < len(pages):
        next_page = pages[index + 1]
        next_link = f'<a href="{href_for(next_page["slug"])}"><small>{ui["next"]}</small>{next_page["nav"]}</a>'

    nav = []
    last = None
    for item in pages:
        if item["group"] != last:
            nav.append(f'<div class="nav-group">{item["group_label"]}</div>')
            last = item["group"]
        cls = ' class="active"' if item["slug"] == page["slug"] else ""
        current = ' aria-current="page"' if item["slug"] == page["slug"] else ""
        nav.append(f'<a{cls}{current} href="{href_for(item["slug"])}">{item["nav"]}</a>')

    other = ui["other_prefix"] + href_for(page["slug"])
    body = page["html"].replace("{{M}}", media)
    return f"""<!DOCTYPE html>
<html lang="{ui["lang"]}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(document_title(ui, page))}</title>
  {seo_head(ui, page, description)}
  <link rel="icon" href="{media}logo.svg">
  <link rel="stylesheet" href="{asset}css/site.css">
</head>
<body data-copy="{ui["copy"]}" data-copied="{ui["copied"]}">
  <a class="skip" href="#doc">{ui["toc"]}</a>
  <div class="layout">
    <aside class="sidebar">
      <a class="brand" href="index.html">
        <img src="{media}logo.svg" alt="Teams Scraper">
        <small>{ui["version"]}</small>
      </a>
      <div class="search">
        <input id="q" type="search" placeholder="{ui["search"]}" autocomplete="off">
        <div id="search-results"></div>
      </div>
      <nav>
        {"".join(nav)}
      </nav>
    </aside>
    <div class="main">
      <header class="topbar">
        <div class="crumbs"><button class="menu" id="nav-toggle" type="button">{ui["menu"]}</button> <b>{page["group_label"]}</b> / {page["nav"]}</div>
        <div class="langs"><span class="on">{ui["this_name"]}</span><a href="{other}">{ui["other_name"]}</a></div>
      </header>
      <div class="content-grid">
        <div>
          <article id="doc">
            {body}
            <div class="pager">{prev_link}{next_link}</div>
            <footer class="site">{ui["footer"]}</footer>
          </article>
        </div>
        <aside class="toc">
          <p>{ui["toc"]}</p>
          <div id="toc-links"></div>
        </aside>
      </div>
    </div>
  </div>
  <script src="{search_src}"></script>
  <script src="{asset}js/site.js"></script>
</body>
</html>
"""


def build_lang(lang):
    ui = UI[lang]
    groups, pages = parse_bundle(lang)
    out = ROOT if lang == "es" else ROOT / "en"
    out.mkdir(parents=True, exist_ok=True)
    asset = "" if lang == "es" else "../"
    media = "media/" if lang == "es" else "../media/"
    search_name = "search-es.js" if lang == "es" else "search-en.js"
    search = []
    for page in pages:
        text = plain(page["html"])
        search.append({
            "title": page["nav"],
            "group": page["group_label"],
            "href": href_for(page["slug"]),
            "text": text[:1200],
        })
        description = meta_description(page["html"])
        html = page_shell(ui, page, pages, asset, media, f"{asset}js/{search_name}", description)
        (out / href_for(page["slug"])).write_text(html, encoding="utf-8")
    payload = "window.WIKI_SEARCH = " + json.dumps(search, ensure_ascii=False) + ";\n"
    (ROOT / "js" / search_name).write_text(payload, encoding="utf-8")
    print(f"{lang}: {len(pages)} pages -> {out}")
    return pages


def write_findability(pages_by_lang):
    urls = []
    for lang, pages in pages_by_lang.items():
        for page in pages:
            urls.append(page_url(lang, page["slug"]))
    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    body.extend(f"  <url><loc>{url}</loc></url>" for url in urls)
    body.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(body) + "\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: "
        + SITE
        + "/sitemap.xml\n",
        encoding="utf-8",
    )
    print(f"sitemap: {len(urls)} urls")


if __name__ == "__main__":
    built = {
        "es": build_lang("es"),
        "en": build_lang("en"),
    }
    write_findability(built)
