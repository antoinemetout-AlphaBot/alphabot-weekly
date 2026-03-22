"""
AlphaBot — Agent Veille 🔍
Rôle : Collecter en temps réel les données des marchés (crypto + bourse) et les actualités.
Sources :
  - CoinGecko API (crypto, gratuit sans clé)
  - Yahoo Finance via yfinance (indices + actions)
  - NewsAPI (actualités financières)
"""

import json
import time
import requests
from datetime import datetime, timedelta

try:
    import yfinance as yf
except ImportError:
    yf = None

# Import config depuis le dossier parent
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CRYPTO_IDS, STOCK_INDICES, WATCHLIST_STOCKS, COMMODITIES
from utils.api_retry import safe_api_call


class AgentVeille:
    """
    Agent de veille : collecte toutes les données de marché.
    Retourne un dict structuré prêt à être analysé par AgentAnalyste.
    """

    COINGECKO_BASE = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        print(f"🔍 Agent Veille démarré — {self.timestamp}")

    # ─── CRYPTO ──────────────────────────────────────────────────────────────

    def fetch_crypto_data(self) -> dict:
        """Récupère prix, variation 24h, market cap pour chaque crypto."""
        print("  📡 Collecte des données crypto (CoinGecko)...")
        try:
            ids = ",".join(CRYPTO_IDS)
            url = (
                f"{self.COINGECKO_BASE}/coins/markets"
                f"?vs_currency=usd"
                f"&ids={ids}"
                f"&order=market_cap_desc"
                f"&sparkline=false"
                f"&price_change_percentage=24h,7d"
            )
            resp = safe_api_call(requests.get, url, timeout=10, agent_name="Agent Veille", default=None)
            if resp is None:
                print("    ⚠️  Impossible de récupérer les données crypto après retries")
                return {}

            resp.raise_for_status()
            data = resp.json()

            result = {}
            for coin in data:
                result[coin["symbol"].upper()] = {
                    "nom":              coin["name"],
                    "prix_usd":         coin["current_price"],
                    "variation_24h":    round(coin.get("price_change_percentage_24h") or 0, 2),
                    "variation_7j":     round(coin.get("price_change_percentage_7d_in_currency") or 0, 2),
                    "market_cap_mrd":   round((coin.get("market_cap") or 0) / 1e9, 1),
                    "volume_24h_mrd":   round((coin.get("total_volume") or 0) / 1e9, 2),
                    "ath_usd":          coin.get("ath"),
                    "ath_pct":          round(coin.get("ath_change_percentage") or 0, 1),
                }
            print(f"    ✅ {len(result)} cryptos collectées")
            return result

        except Exception as e:
            print(f"    ❌ Erreur crypto: {e}")
            return {}

    def fetch_crypto_news(self) -> list:
        """Récupère les actualités crypto récentes via CoinGecko."""
        print("  📰 Collecte des news crypto...")
        try:
            url = f"{self.COINGECKO_BASE}/news"
            resp = safe_api_call(requests.get, url, timeout=10, agent_name="Agent Veille", default=None)
            if resp is None:
                print("    ⚠️  Impossible de récupérer les news crypto après retries")
                return []

            resp.raise_for_status()
            articles = resp.json().get("data", [])[:8]

            news = []
            for article in articles:
                news.append({
                    "titre":  article.get("title", ""),
                    "source": article.get("news_site", ""),
                    "url":    article.get("url", ""),
                    "date":   article.get("created_at", ""),
                })
            print(f"    ✅ {len(news)} articles crypto collectés")
            return news
        except Exception as e:
            print(f"    ❌ Erreur news crypto: {e}")
            return []

    # ─── BOURSE ──────────────────────────────────────────────────────────────

    def fetch_stock_data(self) -> dict:
        """Récupère les données des indices et actions via yfinance."""
        if yf is None:
            print("    ⚠️  yfinance non installé. Lance: pip install yfinance")
            return {"indices": {}, "actions": {}}

        print("  📈 Collecte des données boursières (Yahoo Finance)...")
        result = {"indices": {}, "actions": {}}

        # Indices
        for nom, ticker in STOCK_INDICES.items():
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="5d")
                if len(hist) >= 2:
                    close_today     = hist["Close"].iloc[-1]
                    close_yesterday = hist["Close"].iloc[-2]
                    variation       = round((close_today - close_yesterday) / close_yesterday * 100, 2)
                    close_week_ago  = hist["Close"].iloc[0]
                    variation_7j    = round((close_today - close_week_ago) / close_week_ago * 100, 2)
                    result["indices"][nom] = {
                        "valeur":        round(close_today, 2),
                        "variation_24h": variation,
                        "variation_7j":  variation_7j,
                        "ticker":        ticker,
                    }
            except Exception as e:
                print(f"    ⚠️  Erreur {nom}: {e}")

        # Actions individuelles
        for nom, ticker in WATCHLIST_STOCKS.items():
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="5d")
                info = t.fast_info
                if len(hist) >= 2:
                    close_today     = hist["Close"].iloc[-1]
                    close_yesterday = hist["Close"].iloc[-2]
                    variation       = round((close_today - close_yesterday) / close_yesterday * 100, 2)
                    result["actions"][nom] = {
                        "prix":          round(close_today, 2),
                        "variation_24h": variation,
                        "ticker":        ticker,
                        "devise":        "EUR" if ".PA" in ticker else "USD",
                        "market_cap_mrd": round((getattr(info, "market_cap", 0) or 0) / 1e9, 1),
                    }
            except Exception as e:
                print(f"    ⚠️  Erreur {nom}: {e}")

        nb_indices = len(result["indices"])
        nb_actions = len(result["actions"])
        print(f"    ✅ {nb_indices} indices + {nb_actions} actions collectés")
        return result

    def fetch_market_mood(self) -> dict:
        """Récupère le Fear & Greed Index crypto."""
        print("  🧠 Collecte du Fear & Greed Index...")
        try:
            url = "https://api.alternative.me/fng/?limit=2"
            resp = safe_api_call(requests.get, url, timeout=8, agent_name="Agent Veille", default=None)
            if resp is None:
                print("    ⚠️  Impossible de récupérer le Fear & Greed Index après retries")
                return {}

            resp.raise_for_status()
            data = resp.json()["data"]
            current = data[0]
            yesterday = data[1] if len(data) > 1 else None

            mood = {
                "valeur":        int(current["value"]),
                "sentiment":     current["value_classification"],
                "hier_valeur":   int(yesterday["value"]) if yesterday else None,
                "hier_sentiment": yesterday["value_classification"] if yesterday else None,
            }
            print(f"    ✅ Fear & Greed: {mood['valeur']} ({mood['sentiment']})")
            return mood
        except Exception as e:
            print(f"    ❌ Erreur Fear & Greed: {e}")
            return {}

    # ─── MATIÈRES PREMIÈRES & DEVISES ────────────────────────────────────────

    def fetch_commodities_data(self) -> dict:
        """Récupère DXY, pétrole WTI, or, EUR/USD via yfinance."""
        if yf is None:
            print("    ⚠️  yfinance non installé. Lance: pip install yfinance")
            return {}

        print("  🛢️  Collecte des matières premières & devises (Yahoo Finance)...")
        result = {}

        for nom, ticker in COMMODITIES.items():
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="5d")
                if len(hist) >= 2:
                    close_today     = hist["Close"].iloc[-1]
                    close_yesterday = hist["Close"].iloc[-2]
                    variation       = round((close_today - close_yesterday) / close_yesterday * 100, 2)
                    close_week_ago  = hist["Close"].iloc[0]
                    variation_7j    = round((close_today - close_week_ago) / close_week_ago * 100, 2)
                    result[nom] = {
                        "valeur":        round(close_today, 4),
                        "variation_24h": variation,
                        "variation_7j":  variation_7j,
                        "ticker":        ticker,
                    }
            except Exception as e:
                print(f"    ⚠️  Erreur {nom}: {e}")

        print(f"    ✅ {len(result)} matières premières/devises collectées")
        return result

    # ─── COLLECTE PRINCIPALE ─────────────────────────────────────────────────

    def collecter(self) -> dict:
        """
        Lance toutes les collectes et retourne un rapport structuré.
        C'est ce dict qui sera passé à l'Agent Analyste.
        """
        print("\n━━━ AGENT VEILLE : Début de la collecte ━━━")

        rapport = {
            "meta": {
                "timestamp": self.timestamp,
                "date":      datetime.now().strftime("%d/%m/%Y"),
                "semaine":   datetime.now().strftime("Semaine %W de %Y"),
            },
            "crypto":       self.fetch_crypto_data(),
            "news_crypto":  self.fetch_crypto_news(),
            "bourse":       self.fetch_stock_data(),
            "commodities":  self.fetch_commodities_data(),
            "mood":         self.fetch_market_mood(),
        }

        print("\n✅ Agent Veille : Collecte terminée !")
        print(f"   Cryptos      : {len(rapport['crypto'])} actifs")
        print(f"   Indices      : {len(rapport['bourse'].get('indices', {}))} indices")
        print(f"   Actions      : {len(rapport['bourse'].get('actions', {}))} actions")
        print(f"   Commodities  : {len(rapport['commodities'])} actifs (DXY, WTI, Or, EUR/USD)")
        print(f"   News         : {len(rapport['news_crypto'])} articles")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        return rapport


if __name__ == "__main__":
    agent = AgentVeille()
    data = agent.collecter()
    # Affiche le résultat brut pour vérification
    print(json.dumps(data, indent=2, ensure_ascii=False))
