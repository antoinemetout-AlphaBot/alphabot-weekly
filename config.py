"""
AlphaBot - Configuration centrale
Les secrets sont dans .env — ne jamais les écrire ici directement.
"""

import os

# Charge le .env si présent (développement local)
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)  # override=True pour écraser les variables système si besoin
except ImportError:
    pass  # En prod sans python-dotenv : les variables doivent être dans l'environnement

# ─── CLÉ API ANTHROPIC ────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ─── PARAMÈTRES DE LA NEWSLETTER ─────────────────────────────────────────────
NEWSLETTER_NAME = "AlphaBot Weekly"
NEWSLETTER_TAGLINE = "L'essentiel des marchés bourse & crypto, chaque semaine — par l'IA"
TARGET_AUDIENCE = "investisseurs débutants francophones"

# ─── ACTIFS SUIVIS ────────────────────────────────────────────────────────────

# Cryptos à surveiller — Focus Bitcoin uniquement
CRYPTO_IDS = [
    "bitcoin",
]

# Indices boursiers à surveiller (tickers Yahoo Finance)
STOCK_INDICES = {
    "CAC 40":       "^FCHI",
    "S&P 500":      "^GSPC",
    "Nasdaq 100":   "^NDX",
    "DAX":          "^GDAXI",
    "Dow Jones":    "^DJI",
}

# Matières premières & devises (nouveaux)
COMMODITIES = {
    "Dollar Index (DXY)":   "DX-Y.NYB",
    "Pétrole WTI":          "CL=F",
    "Or (XAU/USD)":         "GC=F",
    "EUR/USD":              "EURUSD=X",
}

# Actions individuelles à suivre (tickers Yahoo Finance)
WATCHLIST_STOCKS = {
    "Apple":         "AAPL",
    "NVIDIA":        "NVDA",
    "Tesla":         "TSLA",
    "LVMH":          "MC.PA",
    "TotalEnergies": "TTE.PA",
    "ExxonMobil":    "XOM",
    "Lockheed Martin": "LMT",
}

# ─── PARAMÈTRES TECHNIQUES ───────────────────────────────────────────────────
CLAUDE_MODEL = "claude-sonnet-4-6"
OUTPUT_DIR = "outputs"
