"""AlphaBot V2 — Configuration centrale.

Secrets attendus en variables d'environnement (GitHub Actions Secrets) :
  ANTHROPIC_API_KEY   — clé API Anthropic
  ALPHABOT_EMAIL      — adresse Gmail d'envoi
  ALPHABOT_PASSWORD   — app password Gmail
  SUBSCRIBERS_CSV     — liste abonnés, une ligne par abonné : email,prenom
                        (jamais dans le repo public — RGPD)
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
NEWSLETTERS_DIR = ROOT / "newsletters"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ALPHABOT_EMAIL = os.getenv("ALPHABOT_EMAIL", "")
ALPHABOT_PASSWORD = os.getenv("ALPHABOT_PASSWORD", "")

CLAUDE_MODEL = "claude-sonnet-4-6"

NEWSLETTER_NAME = "AlphaBot Weekly"
TAGLINE = "L'essentiel des marchés bourse & crypto, chaque jour — par l'IA"
TARGET_AUDIENCE = "investisseurs débutants francophones (25-45 ans)"
SITE_URL = "https://antoinemetout-alphabot.github.io/alphabot-weekly"
FORMSPREE_ENDPOINT = "https://formspree.io/f/xzzbqwaa"

# ─── Actifs suivis ───────────────────────────────────────────────────────────
CRYPTO = {"Bitcoin": "bitcoin"}                      # id CoinGecko
CRYPTO_YF_FALLBACK = {"Bitcoin": "BTC-USD"}          # fallback Yahoo

INDICES = {
    "CAC 40": "^FCHI",
    "S&P 500": "^GSPC",
    "Nasdaq 100": "^NDX",
    "DAX": "^GDAXI",
    "Dow Jones": "^DJI",
}

COMMODITIES = {
    "Dollar Index (DXY)": "DX-Y.NYB",
    "Pétrole WTI": "CL=F",
    "Or": "GC=F",
    "EUR/USD": "EURUSD=X",
}

WATCHLIST = {
    "Apple": ("AAPL", "apple.com"),
    "NVIDIA": ("NVDA", "nvidia.com"),
    "Tesla": ("TSLA", "tesla.com"),
    "LVMH": ("MC.PA", "lvmh.com"),
    "TotalEnergies": ("TTE.PA", "totalenergies.com"),
    "ExxonMobil": ("XOM", "exxonmobil.com"),
    "Lockheed Martin": ("LMT", "lockheedmartin.com"),
}

# Univers autorisé pour les portefeuilles simulés (anti-hallucination :
# Claude ne peut trader QUE ces tickers, validés par code).
UNIVERSE = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA", "GOOGL": "Alphabet",
    "AMZN": "Amazon", "TSLA": "Tesla", "META": "Meta", "KO": "Coca-Cola",
    "JNJ": "Johnson & Johnson", "PG": "Procter & Gamble", "XOM": "ExxonMobil",
    "LMT": "Lockheed Martin", "MC.PA": "LVMH", "TTE.PA": "TotalEnergies",
    "AIR.PA": "Airbus", "SAN.PA": "Sanofi", "SU.PA": "Schneider Electric",
    "SPY": "ETF S&P 500", "QQQ": "ETF Nasdaq 100", "GLD": "ETF Or",
    "TLT": "ETF Obligations US 20 ans", "BTC-USD": "Bitcoin",
}

MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"]
JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def date_fr(d):
    """datetime/date → 'Mercredi 1er juillet 2026'."""
    jour = "1er" if d.day == 1 else str(d.day)
    return f"{JOURS_FR[d.weekday()]} {jour} {MOIS_FR[d.month - 1]} {d.year}"


def now_paris():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("Europe/Paris"))
