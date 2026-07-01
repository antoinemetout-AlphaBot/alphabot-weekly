"""Build du site statique — templates Jinja2 → racine du repo (GitHub Pages).

Une seule source pour nav/footer/CSS (templates/base.html + static/site.css) :
fini la duplication V1 et les incohérences entre pages.
"""
import json

from . import config
from .render import env

PAGES = {
    "index.html": "index.html",
    "newsletter.html": "newsletter.html",
    "newsletters.html": "newsletters.html",
    "investissement.html": "investissement.html",
    "coulisses.html": "coulisses.html",
    "mentions.html": "mentions.html",
    "404.html": "404.html",
}

REDIRECTIONS = {
    # anciennes URLs V1 → nouvelles pages
    "arena.html": "investissement.html",
    "dashboard-agents.html": "coulisses.html",
    "communaute.html": "index.html",
    "landing_page.html": "index.html",
}


def _lire_json(nom: str, defaut):
    p = config.DATA / nom
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return defaut


def contexte_global() -> dict:
    newsletters = _lire_json("newsletters.json", {"editions": [], "count": 0})
    portfolio = _lire_json("portfolio.json", {"profils": {}})
    live = _lire_json("live_prices.json", {"prices": {}, "updated_at": ""})
    log = _lire_json("pipeline_log.json", {"events": []})

    profils = []
    for pid, prof in portfolio.get("profils", {}).items():
        profils.append({"id": pid, **prof})
    now = config.now_paris()
    return {
        "site_url": config.SITE_URL,
        "nom": config.NEWSLETTER_NAME,
        "tagline": config.TAGLINE,
        "formspree": config.FORMSPREE_ENDPOINT,
        "newsletters": newsletters,
        "derniere_edition": newsletters["editions"][0] if newsletters["editions"] else None,
        "profils": profils,
        "portfolio_demarrage": portfolio.get("demarrage", ""),
        "portfolio_saison": portfolio.get("saison", 2),
        "live": live,
        "pipeline_events": log.get("events", [])[-60:][::-1],
        "date_label": config.date_fr(now),
        "annee": now.year,
        "maj": now.strftime("%d/%m/%Y %H:%M"),
    }


def build():
    ctx = contexte_global()
    for sortie, tpl in PAGES.items():
        html = env.get_template(tpl).render(**ctx)
        if "</html>" not in html or "```" in html:
            raise RuntimeError(f"Page invalide: {sortie} — publication refusée")
        (config.ROOT / sortie).write_text(html, encoding="utf-8")

    tpl_redirect = env.get_template("_redirect.html")
    for ancien, nouveau in REDIRECTIONS.items():
        (config.ROOT / ancien).write_text(
            tpl_redirect.render(cible=nouveau, site_url=config.SITE_URL), encoding="utf-8")

    _sitemap(ctx)
    print(f"  ✅ Site généré ({len(PAGES)} pages + {len(REDIRECTIONS)} redirections)")


def _sitemap(ctx):
    urls = [f"{config.SITE_URL}/{p}" for p in PAGES if p != "404.html"]
    urls.insert(0, config.SITE_URL + "/")
    corps = "".join(f"<url><loc>{u}</loc></url>" for u in urls)
    (config.ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{corps}</urlset>',
        encoding="utf-8")
    (config.ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {config.SITE_URL}/sitemap.xml\n", encoding="utf-8")
