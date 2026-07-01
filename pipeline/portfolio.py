"""Portefeuilles IA simulés — 3 profils (Saison 2, relancée le 1er juillet 2026).

SIMULATION PÉDAGOGIQUE : aucun argent réel, aucun conseil en investissement.
- Revalorisation quotidienne avec les prix réels du marché (code, pas d'IA).
- Décisions de trades le lundi : Claude propose, le code VALIDE et exécute
  (univers de tickers fermé, contraintes de cash et de concentration).
Valorisation en EUR (conversion USD→EUR au taux du jour).
"""
import json
from datetime import date

from . import config
from .analyst import appel_claude, _extraire_json

FICHIER = config.DATA / "portfolio.json"
MAX_POSITION_PCT = {"prudent": 0.20, "modere": 0.25, "agressif": 0.35}

PROFILS_DEFAUT = {
    "prudent": {"nom": "Le Gardien", "emoji": "🛡️",
                "description": "Préservation du capital : ETF défensifs, grandes capitalisations, horizon long"},
    "modere": {"nom": "Le Stratège", "emoji": "⚖️",
               "description": "Équilibre croissance/stabilité : mix actions de qualité et ETF"},
    "agressif": {"nom": "Le Chasseur", "emoji": "🎯",
                 "description": "Croissance maximale : tech, crypto, positions concentrées"},
}


def charger() -> dict:
    if FICHIER.exists():
        return json.loads(FICHIER.read_text(encoding="utf-8"))
    p = {"saison": 2, "demarrage": str(date.today()), "profils": {}}
    for pid, meta in PROFILS_DEFAUT.items():
        p["profils"][pid] = {**meta, "capital_initial": 10000.0, "cash": 10000.0,
                             "positions": [], "historique": [], "trades": []}
    return p


def sauver(p: dict):
    config.DATA.mkdir(exist_ok=True)
    FICHIER.write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")


def tickers_detenus(p: dict) -> list[str]:
    return [pos["ticker"] for prof in p["profils"].values() for pos in prof["positions"]]


def _eurusd(rapport: dict) -> float:
    d = rapport.get("commodities", {}).get("EUR/USD")
    return float(d["prix"]) if d else 1.08


def _prix(ticker: str, rapport: dict) -> float | None:
    for groupe in ("portefeuille_prix",):
        if ticker in rapport.get(groupe, {}):
            return float(rapport[groupe][ticker]["prix"])
    for groupe in ("indices", "commodities", "watchlist"):
        for d in rapport.get(groupe, {}).values():
            if d.get("ticker") == ticker:
                return float(d["prix"])
    if ticker == "BTC-USD" and rapport["crypto"].get("Bitcoin"):
        return float(rapport["crypto"]["Bitcoin"]["prix"])
    return None


def _prix_eur(ticker: str, rapport: dict) -> float | None:
    prix = _prix(ticker, rapport)
    if prix is None:
        return None
    return prix if ticker.endswith(".PA") else prix / _eurusd(rapport)


def revaloriser(p: dict, rapport: dict) -> dict:
    """MAJ quotidienne des valorisations. Déterministe, sans IA."""
    aujourd_hui = str(config.now_paris().date())
    for prof in p["profils"].values():
        valeur = prof["cash"]
        for pos in prof["positions"]:
            prix = _prix_eur(pos["ticker"], rapport)
            if prix is not None:
                pos["prix_actuel_eur"] = round(prix, 2)
            valeur += pos.get("prix_actuel_eur", pos["prix_entree_eur"]) * pos["quantite"]
        prof["valeur_totale"] = round(valeur, 2)
        prof["performance_pct"] = round((valeur / prof["capital_initial"] - 1) * 100, 2)
        hist = prof["historique"]
        if hist and hist[-1]["date"] == aujourd_hui:
            hist[-1]["valeur"] = prof["valeur_totale"]
        else:
            hist.append({"date": aujourd_hui, "valeur": prof["valeur_totale"]})
        prof["historique"] = hist[-400:]
    sauver(p)
    return p


PROMPT_TRADES = """Tu gères 3 portefeuilles SIMULÉS (pédagogiques) en EUR. État actuel :

{etat}

Prix disponibles aujourd'hui (EUR) :
{prix}

Univers autorisé (SEULS tickers permis) : {univers}

Profils :
- prudent (Le Gardien) : max 20% par position, privilégie ETF/défensives, peu de trades
- modere (Le Stratège) : max 25% par position, équilibre
- agressif (Le Chasseur) : max 35% par position, peut prendre du risque (tech, BTC-USD)

Propose 0 à 3 trades PAR PROFIL (0 est un choix valide si rien ne le justifie).
Réponds UNIQUEMENT en JSON :
{{"trades": [{{"profil": "prudent|modere|agressif", "action": "acheter|vendre",
  "ticker": "...", "montant_eur": 1500, "raison": "1 phrase avec un chiffre"}}]}}
Pour "vendre", montant_eur = null vend toute la position."""


def decider_trades(p: dict, rapport: dict) -> list[dict]:
    """Lundi : Claude propose, le code valide et exécute. Anti-hallucination stricte."""
    prix_dispo = {t: _prix_eur(t, rapport) for t in config.UNIVERSE}
    prix_dispo = {t: round(v, 2) for t, v in prix_dispo.items() if v}
    etat = []
    for pid, prof in p["profils"].items():
        pos = ", ".join(f"{x['ticker']} ({x['quantite']:.4g} × {x.get('prix_actuel_eur', 0):.2f}€)"
                        for x in prof["positions"]) or "aucune position"
        etat.append(f"{pid}: cash {prof['cash']:.0f}€, valeur {prof.get('valeur_totale', 10000):.0f}€ — {pos}")

    reponse = appel_claude(
        "Tu es le gérant des portefeuilles simulés d'AlphaBot Weekly. Tu réponds uniquement en JSON valide.",
        PROMPT_TRADES.format(etat="\n".join(etat),
                             prix="\n".join(f"{t}: {v}€" for t, v in prix_dispo.items()),
                             univers=", ".join(config.UNIVERSE)),
        max_tokens=1500)
    try:
        trades = _extraire_json(reponse).get("trades", [])
    except Exception:  # noqa: BLE001
        return []

    executes = []
    aujourd_hui = str(config.now_paris().date())
    for t in trades:
        pid, ticker = t.get("profil"), t.get("ticker")
        if pid not in p["profils"] or ticker not in config.UNIVERSE or ticker not in prix_dispo:
            continue
        prof, prix = p["profils"][pid], prix_dispo[ticker]
        if t.get("action") == "acheter":
            montant = float(t.get("montant_eur") or 0)
            plafond = prof.get("valeur_totale", 10000) * MAX_POSITION_PCT[pid]
            montant = min(montant, prof["cash"], plafond)
            if montant < 100:
                continue
            qte = montant / prix
            prof["cash"] = round(prof["cash"] - montant, 2)
            existante = next((x for x in prof["positions"] if x["ticker"] == ticker), None)
            if existante:
                total = existante["quantite"] + qte
                existante["prix_entree_eur"] = round(
                    (existante["prix_entree_eur"] * existante["quantite"] + prix * qte) / total, 2)
                existante["quantite"] = total
            else:
                prof["positions"].append({
                    "ticker": ticker, "nom": config.UNIVERSE[ticker],
                    "quantite": round(qte, 6), "prix_entree_eur": round(prix, 2),
                    "prix_actuel_eur": round(prix, 2), "date_entree": aujourd_hui})
        elif t.get("action") == "vendre":
            existante = next((x for x in prof["positions"] if x["ticker"] == ticker), None)
            if not existante:
                continue
            montant = t.get("montant_eur")
            qte = existante["quantite"] if montant is None else min(
                existante["quantite"], float(montant) / prix)
            prof["cash"] = round(prof["cash"] + qte * prix, 2)
            existante["quantite"] = round(existante["quantite"] - qte, 6)
            if existante["quantite"] <= 1e-6:
                prof["positions"].remove(existante)
        else:
            continue
        trade = {"date": aujourd_hui, "profil": pid, "action": t["action"], "ticker": ticker,
                 "prix_eur": round(prix, 2), "raison": str(t.get("raison", ""))[:200]}
        prof["trades"].append(trade)
        prof["trades"] = prof["trades"][-100:]
        executes.append(trade)
    sauver(p)
    return executes


def resume_texte(p: dict) -> str:
    out = []
    for prof in p["profils"].values():
        out.append(f"{prof['nom']} {prof.get('performance_pct', 0):+.2f}%")
    return " · ".join(out)
