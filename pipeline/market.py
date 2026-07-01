"""Collecte des données marchés — yfinance + CoinGecko + Fear & Greed.

Robustesse : retries avec backoff, validation des valeurs, fallbacks.
Sortie : dict normalisé, sauvegardé dans data/market_latest.json.
"""
import json
import time
from datetime import datetime, timezone

import requests

from . import config

HEADERS = {"User-Agent": "Mozilla/5.0 (AlphaBotWeekly/2.0)"}


def _retry(fn, tries=3, delay=2.0):
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(delay * (i + 1))
    raise last


def _yf_quotes(tickers: list[str]) -> dict:
    """Prix + variations via yfinance. Retourne {ticker: {prix, var_24h, var_7j}}."""
    import yfinance as yf

    out = {}
    def fetch():
        data = yf.download(tickers, period="10d", interval="1d",
                           progress=False, auto_adjust=True, threads=False)
        closes = data["Close"]
        if len(tickers) == 1:
            closes = closes.to_frame(name=tickers[0]) if hasattr(closes, "to_frame") else closes
        return closes

    closes = _retry(fetch)
    for t in tickers:
        try:
            serie = closes[t].dropna()
            if len(serie) < 2:
                continue
            prix = float(serie.iloc[-1])
            prev = float(serie.iloc[-2])
            prev7 = float(serie.iloc[0])
            if prix <= 0 or prev <= 0:
                continue
            out[t] = {
                "prix": round(prix, 4),
                "var_24h": round((prix / prev - 1) * 100, 2),
                "var_7j": round((prix / prev7 - 1) * 100, 2),
            }
        except Exception:  # noqa: BLE001
            continue
    return out


def _bitcoin() -> dict | None:
    """Bitcoin via CoinGecko, fallback yfinance."""
    try:
        def cg():
            r = requests.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                params={"vs_currency": "usd", "ids": "bitcoin",
                        "price_change_percentage": "24h,7d"},
                headers=HEADERS, timeout=15)
            r.raise_for_status()
            d = r.json()[0]
            return {
                "prix": round(float(d["current_price"]), 0),
                "var_24h": round(float(d.get("price_change_percentage_24h") or 0), 2),
                "var_7j": round(float(d.get("price_change_percentage_7d_in_currency") or 0), 2),
                "market_cap": int(d.get("market_cap") or 0),
                "source": "coingecko",
            }
        return _retry(cg, tries=2)
    except Exception:  # noqa: BLE001
        q = _yf_quotes(["BTC-USD"]).get("BTC-USD")
        if q:
            q["source"] = "yahoo"
        return q


def _fear_greed() -> dict | None:
    try:
        def fg():
            r = requests.get("https://api.alternative.me/fng/?limit=1",
                             headers=HEADERS, timeout=15)
            r.raise_for_status()
            d = r.json()["data"][0]
            return {"valeur": int(d["value"]), "label": d["value_classification"]}
        return _retry(fg, tries=2)
    except Exception:  # noqa: BLE001
        return None


def collecter(extra_tickers: list[str] | None = None) -> dict:
    """Collecte complète. extra_tickers : tickers des positions du portefeuille."""
    rapport = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "crypto": {}, "indices": {}, "commodities": {}, "watchlist": {},
        "portefeuille_prix": {}, "fear_greed": None, "erreurs": [],
    }

    btc = _bitcoin()
    if btc:
        rapport["crypto"]["Bitcoin"] = btc
    else:
        rapport["erreurs"].append("bitcoin")

    groupes = [
        ("indices", config.INDICES),
        ("commodities", config.COMMODITIES),
        ("watchlist", {n: t for n, (t, _) in config.WATCHLIST.items()}),
    ]
    for cle, mapping in groupes:
        try:
            quotes = _yf_quotes(list(mapping.values()))
            for nom, ticker in mapping.items():
                if ticker in quotes:
                    rapport[cle][nom] = {"ticker": ticker, **quotes[ticker]}
            if not rapport[cle]:
                rapport["erreurs"].append(cle)
        except Exception as e:  # noqa: BLE001
            rapport["erreurs"].append(f"{cle}: {e}")

    if extra_tickers:
        try:
            rapport["portefeuille_prix"] = _yf_quotes(sorted(set(extra_tickers)))
        except Exception as e:  # noqa: BLE001
            rapport["erreurs"].append(f"portefeuille: {e}")

    rapport["fear_greed"] = _fear_greed()

    # Validation minimale : sans indices ET sans bitcoin, la collecte a échoué.
    if not rapport["indices"] and not rapport["crypto"]:
        raise RuntimeError(f"Collecte marchés vide — erreurs: {rapport['erreurs']}")

    config.DATA.mkdir(exist_ok=True)
    (config.DATA / "market_latest.json").write_text(
        json.dumps(rapport, ensure_ascii=False, indent=1), encoding="utf-8")
    return rapport


def maj_prix_live(portfolio_tickers: list[str] | None = None) -> dict:
    """MAJ légère pour le bandeau prix du site → data/live_prices.json."""
    rapport = collecter(portfolio_tickers)
    live = {"updated_at": config.now_paris().isoformat(timespec="seconds"), "prices": {}}
    btc = rapport["crypto"].get("Bitcoin")
    if btc:
        live["prices"]["Bitcoin"] = {"prix": btc["prix"], "variation": btc["var_24h"]}
    for groupe in ("indices", "commodities"):
        for nom, d in rapport[groupe].items():
            live["prices"][nom] = {"prix": d["prix"], "variation": d["var_24h"]}
    (config.DATA / "live_prices.json").write_text(
        json.dumps(live, ensure_ascii=False, indent=1), encoding="utf-8")
    return live
