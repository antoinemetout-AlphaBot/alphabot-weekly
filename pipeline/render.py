"""Rendu HTML — newsletter (page site + version email) via Jinja2.

Le convertisseur markdown est volontairement minimal et SÛR :
il échappe le HTML d'abord (pas d'injection possible), puis applique
**gras**, listes et paragraphes. Fini le bug V1 des backticks qui cassaient le site.
"""
import html as html_mod
import json
import re

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from . import config

env = Environment(
    loader=FileSystemLoader(str(config.TEMPLATES)),
    autoescape=select_autoescape(["html"]),
)


def md(texte: str) -> Markup:
    """Markdown minimal → HTML sûr (échappé d'abord, puis marqué safe pour Jinja)."""
    if not texte:
        return Markup("")
    texte = html_mod.escape(str(texte), quote=False)
    texte = re.sub(r"```[a-z]*", "", texte)  # jamais de backticks dans la sortie
    texte = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", texte)
    texte = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", texte)
    blocs = []
    for bloc in re.split(r"\n\s*\n", texte.strip()):
        lignes = bloc.strip().splitlines()
        if all(l.strip().startswith("- ") for l in lignes if l.strip()):
            items = "".join(f"<li>{l.strip()[2:]}</li>" for l in lignes if l.strip())
            blocs.append(f"<ul>{items}</ul>")
        else:
            blocs.append(f"<p>{'<br>'.join(l.strip() for l in lignes)}</p>")
    return Markup("\n".join(blocs))


env.filters["md"] = md


def _fg_context(fg: dict | None) -> dict | None:
    if not fg:
        return None
    v = fg["valeur"]
    emoji = "😱" if v < 25 else "😨" if v < 45 else "😐" if v < 55 else "😏" if v < 75 else "🤑"
    labels_fr = {"Extreme Fear": "Peur extrême", "Fear": "Peur", "Neutral": "Neutre",
                 "Greed": "Avidité", "Extreme Greed": "Avidité extrême"}
    return {**fg, "emoji": emoji, "label_fr": labels_fr.get(fg["label"], fg["label"])}


def contexte_newsletter(rapport: dict, contenu: dict, portfolio: dict, numero: int) -> dict:
    now = config.now_paris()
    kpis = []
    btc = rapport["crypto"].get("Bitcoin")
    if btc:
        kpis.append({"nom": "Bitcoin", "valeur": f"{btc['prix']:,.0f} $".replace(",", " "),
                     "var": btc["var_24h"]})
    for nom in ("S&P 500", "CAC 40"):
        d = rapport["indices"].get(nom)
        if d:
            kpis.append({"nom": nom, "valeur": f"{d['prix']:,.0f}".replace(",", " "), "var": d["var_24h"]})
    for nom, label in (("Or", "Or"), ("Pétrole WTI", "Pétrole"), ("EUR/USD", "EUR/USD")):
        d = rapport["commodities"].get(nom)
        if d:
            fmt = f"{d['prix']:,.4f}" if nom == "EUR/USD" else f"{d['prix']:,.0f} $"
            kpis.append({"nom": label, "valeur": fmt.replace(",", " "), "var": d["var_24h"]})

    watchlist = []
    for nom, d in rapport.get("watchlist", {}).items():
        domaine = config.WATCHLIST.get(nom, ("", ""))[1]
        watchlist.append({"nom": nom, "ticker": d["ticker"], "prix": d["prix"],
                          "var": d["var_24h"], "logo": f"https://logo.clearbit.com/{domaine}"})
    watchlist.sort(key=lambda x: abs(x["var"]), reverse=True)

    profils = []
    for pid, prof in portfolio.get("profils", {}).items():
        profils.append({"id": pid, **{k: prof.get(k) for k in
                        ("nom", "emoji", "description", "valeur_totale", "performance_pct")}})

    return {
        "site_url": config.SITE_URL,
        "nom": config.NEWSLETTER_NAME,
        "tagline": config.TAGLINE,
        "date_label": config.date_fr(now),
        "date_iso": str(now.date()),
        "numero": numero,
        "contenu": contenu,
        "kpis": kpis,
        "fear_greed": _fg_context(rapport.get("fear_greed")),
        "watchlist": watchlist[:7],
        "profils": profils,
        "annee": now.year,
    }


def rendre_newsletter(ctx: dict) -> tuple[str, str]:
    """Retourne (html_page_site, html_email)."""
    page = env.get_template("newsletter_edition.html").render(**ctx)
    email = env.get_template("email_newsletter.html").render(**ctx)
    for sortie in (page, email):
        if "```" in sortie:
            raise RuntimeError("Backticks détectés dans le HTML généré — publication refusée")
        if "</html>" not in sortie:
            raise RuntimeError("HTML tronqué — publication refusée")
    return page, email


def publier_newsletter(page_html: str, date_iso: str, titre: str) -> dict:
    """Écrit le fichier + met à jour l'index newsletters.json."""
    config.NEWSLETTERS_DIR.mkdir(exist_ok=True)
    fichier = f"alphabot_newsletter_{date_iso}.html"
    (config.NEWSLETTERS_DIR / fichier).write_text(page_html, encoding="utf-8")

    index_path = config.DATA / "newsletters.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() \
        else {"editions": []}
    index["editions"] = [e for e in index["editions"] if e["date"] != date_iso]
    from datetime import date as ddate
    d = ddate.fromisoformat(date_iso)
    index["editions"].insert(0, {"date": date_iso, "label": config.date_fr(d),
                                 "titre": titre, "file": f"newsletters/{fichier}"})
    index["editions"].sort(key=lambda e: e["date"], reverse=True)
    index["count"] = len(index["editions"])
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return index
