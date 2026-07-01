"""Point d'entrée du pipeline AlphaBot V2.

Commandes :
  python -m pipeline.run daily    → pipeline complet (collecte → analyse → portefeuille
                                    → newsletter → site → emails). Tous les jours 7h30 Paris.
  python -m pipeline.run prices   → MAJ prix live + rebuild site (heures de marché).
  python -m pipeline.run build    → rebuild site seul (sans IA, sans email).

Supervision : toute exception → log + email d'alerte au CEO + exit code 1
(le run GitHub Actions apparaît en rouge + notification GitHub).
"""
import json
import sys
import traceback
from datetime import datetime, timezone

from . import config, market, analyst, portfolio, render, site, mailer

LOG = config.DATA / "pipeline_log.json"


def _log(evenement: str, statut: str, detail: str = ""):
    config.DATA.mkdir(exist_ok=True)
    data = {"events": []}
    if LOG.exists():
        try:
            data = json.loads(LOG.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    data["events"].append({
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "evenement": evenement, "statut": statut, "detail": detail[:300]})
    data["events"] = data["events"][-300:]
    LOG.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def _memoire() -> dict:
    p = config.DATA / "memoire_editoriale.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"titres_recents": []}


def _sauver_memoire(m: dict):
    (config.DATA / "memoire_editoriale.json").write_text(
        json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")


def daily():
    now = config.now_paris()
    date_iso = str(now.date())
    print(f"🤖 AlphaBot V2 — pipeline quotidien {date_iso}")

    pf = portfolio.charger()

    print("📡 Collecte des marchés…")
    rapport = market.collecter(portfolio.tickers_detenus(pf))
    _log("collecte", "ok", f"{len(rapport['indices'])} indices, erreurs: {rapport['erreurs']}")

    print("💼 Portefeuilles…")
    pf = portfolio.revaloriser(pf, rapport)
    trades = []
    if now.weekday() == 0:  # lundi : décisions de trades
        trades = portfolio.decider_trades(pf, rapport)
        pf = portfolio.revaloriser(pf, rapport)
        _log("trades", "ok", f"{len(trades)} trade(s) exécuté(s)")

    print("🧠 Analyse éditoriale (Claude)…")
    memoire = _memoire()
    contenu = analyst.analyser(rapport, memoire)
    memoire["titres_recents"] = (memoire.get("titres_recents", [])
                                 + [contenu["titre_edition"], contenu["concept"]["titre"]])[-30:]
    _sauver_memoire(memoire)
    (config.DATA / "derniere_analyse.json").write_text(
        json.dumps({"date": date_iso, "contenu": contenu}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    _log("analyse", "ok", contenu["titre_edition"])

    print("📰 Rendu newsletter…")
    index_actuel = site._lire_json("newsletters.json", {"editions": []})
    numero = len([e for e in index_actuel["editions"] if e["date"] != date_iso]) + 1
    ctx = render.contexte_newsletter(rapport, contenu, pf, numero)
    page_html, email_html = render.rendre_newsletter(ctx)
    render.publier_newsletter(page_html, date_iso, contenu["titre_edition"])
    _log("newsletter", "ok", f"édition #{numero}")

    print("📊 Prix live + build site…")
    market.maj_prix_live(portfolio.tickers_detenus(pf))
    site.build()
    _log("site", "ok")

    print("📧 Envoi aux abonnés…")
    sujet = f"⚡ {contenu['titre_edition']}"
    n = mailer.envoyer_newsletter(sujet, email_html)
    _log("emails", "ok", f"{n} envoyé(s)")

    if now.weekday() == 0:  # lundi : posts LinkedIn pour le CEO
        try:
            posts = analyst.posts_linkedin(rapport, portfolio.resume_texte(pf))
            corps = "<h2>📣 Posts LinkedIn de la semaine</h2>" + "".join(
                f"<div style='background:#f1f5f9;padding:14px;border-radius:8px;margin:10px 0;"
                f"white-space:pre-wrap;font-family:sans-serif'>{p.strip()}</div>"
                for p in posts.split("---"))
            if trades:
                corps += "<h3>Trades du lundi</h3><ul>" + "".join(
                    f"<li>{t['profil']} — {t['action']} {t['ticker']} @ {t['prix_eur']}€ : "
                    f"{t['raison']}</li>" for t in trades) + "</ul>"
            mailer.email_ceo("📣 AlphaBot — posts LinkedIn + trades de la semaine", corps)
            _log("linkedin", "ok")
        except Exception as e:  # noqa: BLE001
            _log("linkedin", "erreur", str(e))  # non bloquant

    print(f"✅ Pipeline terminé — édition #{numero} publiée, {n} email(s) envoyé(s)")


def prices():
    pf = portfolio.charger()
    rapport_live = market.maj_prix_live(portfolio.tickers_detenus(pf))
    rapport = json.loads((config.DATA / "market_latest.json").read_text(encoding="utf-8"))
    portfolio.revaloriser(pf, rapport)
    site.build()
    _log("prix_live", "ok", f"{len(rapport_live['prices'])} actifs")
    print("✅ Prix live mis à jour")


def build():
    site.build()


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    try:
        {"daily": daily, "prices": prices, "build": build}[cmd]()
    except KeyError:
        print(f"Commande inconnue: {cmd} (daily|prices|build)")
        sys.exit(2)
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc()
        print(tb)
        _log(cmd, "erreur", str(e))
        mailer.alerte_ceo(f"Échec pipeline « {cmd} »", f"{e}\n\n{tb[-1500:]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
