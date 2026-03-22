"""
AlphaBot — Robot Trader Autonome 🤖📈
=====================================
Le meilleur robot trader du monde (fictif et éducatif).

Stratégies:
1. Momentum — Suit les tendances fortes (SMA20 > SMA50, RSI 30-70)
2. Mean Reversion — Achète les dips excessifs (RSI < 30, Bollinger)
3. Géopolitique — Positions basées sur thèses macro (via Claude IA)

Règles de gestion du risque:
- Max 25% du capital par position
- Max 5 positions simultanées
- Stop-loss automatique à -8%
- Take-profit automatique à +15%
- Trailing stop à -5% quand gain > +8%
- Pas de trade si cash < 10% du capital (réserve de sécurité)

Capital: 10,000€ fictif, objective 100,000€
Trades TOUTES LES HEURES pendant les heures de marché (9h-18h Paris)
Univers: Actions uniquement — AAPL, NVDA, TSLA, MC.PA, TTE.PA, XOM, LMT + indices ETFs
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import math

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import pandas as pd
    import numpy as np
except ImportError:
    pd = None
    np = None

try:
    import anthropic
except ImportError:
    anthropic = None

# Import config et utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, WATCHLIST_STOCKS, STOCK_INDICES, COMMODITIES, OUTPUT_DIR
from utils.activity_logger import log_event
from utils.api_retry import safe_api_call
from utils.file_lock import file_lock

# ─── CONSTANTES ────────────────────────────────────────────────────────────
DATA_DIR = "data"
PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolio.json")
PORTFOLIO_LIVE_FILE = os.path.join(DATA_DIR, "portfolio_live.json")
EQUITY_CURVE_FILE = os.path.join(DATA_DIR, "equity_curve.json")

# Univers des actifs tradables (actions uniquement)
TRADEABLE_STOCKS = {
    "AAPL": "Apple",
    "NVDA": "NVIDIA",
    "TSLA": "Tesla",
    "MC.PA": "LVMH",
    "TTE.PA": "TotalEnergies",
    "XOM": "ExxonMobil",
    "LMT": "Lockheed Martin",
}

TRADEABLE_ETFS = {
    "SPY": "S&P 500 ETF",
    "GLD": "SPDR Gold Trust",
}

# Tous les actifs tradables
TRADEABLE = {**TRADEABLE_STOCKS, **TRADEABLE_ETFS}

# Paramètres de risque
MAX_POSITION_PCT = 0.25          # 25% du capital par position
MAX_SIMULTANEOUS_POSITIONS = 5   # Max 5 positions ouvertes
MIN_CASH_RESERVE_PCT = 0.10      # Réserve min 10%
STOP_LOSS_PCT = -0.08            # -8%
TAKE_PROFIT_PCT = 0.15           # +15%
TRAILING_STOP_PCT = -0.05        # -5% from peak
TRAILING_STOP_THRESHOLD = 0.08   # Activation à +8% de gain

MIN_POSITION_EUR = 200            # Position minimum 200€
MAX_POSITION_EUR_FROM_CAPITAL = None  # Calcul dynamique


# ─── ROBOT TRADER ──────────────────────────────────────────────────────────

class RobotTrader:
    """
    Robot trader autonome utilisant l'analyse technique et l'IA pour les décisions.
    """

    def __init__(self):
        """Initialise le robot trader."""
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.portfolio = self._charger_portfolio()
        self.market_data = {}
        self.signals = []
        self.executed_trades = []

        log_event("Robot Trader", "start", f"Initialisation {self.timestamp}")
        print(f"🤖 Robot Trader initialisé — {self.timestamp}")
        print(f"   Capital: €{self.portfolio['meta']['capital_actuel']:.2f} / Objectif: €{self.portfolio['meta']['objectif']:.2f}")
        print(f"   Positions: {len(self.portfolio['positions'])} | Trades: {self.portfolio['meta']['nb_trades']}")

    # ════════════════════════════════════════════════════════════════════════════════
    # GESTION DU PORTFOLIO
    # ════════════════════════════════════════════════════════════════════════════════

    def _charger_portfolio(self) -> dict:
        """Charge le portfolio depuis JSON, ou retourne un portfolio vierge."""
        try:
            if os.path.exists(PORTFOLIO_FILE):
                with file_lock(PORTFOLIO_FILE):
                    with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
                        return json.load(f)
        except Exception as e:
            log_event("Robot Trader", "warning", f"Erreur chargement portfolio: {e}")
            print(f"   ⚠️  Erreur chargement portfolio: {e}")

        # Portfolio par défaut
        return {
            "meta": {
                "capital_initial": 10000,
                "capital_actuel": 10000,
                "objectif": 100000,
                "date_creation": datetime.now().strftime("%Y-%m-%d"),
                "derniere_maj": datetime.now().isoformat(),
                "devise": "EUR",
                "performance_totale_pct": 0.0,
                "nb_trades": 0,
                "nb_trades_gagnants": 0,
                "nb_trades_perdants": 0,
                "meilleur_trade_pct": 0.0,
                "pire_trade_pct": 0.0,
                "win_rate": 0.0,
                "sharpe_ratio": 0.0,
            },
            "cash_disponible": 10000,
            "positions": [],
            "trades_historique": [],
            "equity_curve": [{"date": datetime.now().strftime("%Y-%m-%d"), "valeur": 10000}],
            "signaux_actifs": [],
            "theses_investissement": {"strategie_globale": "Momentum + Mean Reversion + IA", "theses_actives": []},
        }

    def _sauvegarder_portfolio(self):
        """Sauvegarde le portfolio avec file locking."""
        try:
            Path(DATA_DIR).mkdir(exist_ok=True)
            with file_lock(PORTFOLIO_FILE):
                with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.portfolio, f, ensure_ascii=False, indent=2)
            log_event("Robot Trader", "success", f"Portfolio sauvegardé - Capital: €{self.portfolio['meta']['capital_actuel']:.2f}")
            return True
        except Exception as e:
            log_event("Robot Trader", "error", f"Erreur sauvegarde portfolio: {e}")
            print(f"   ❌ Erreur sauvegarde: {e}")
            return False

    # ════════════════════════════════════════════════════════════════════════════════
    # RÉCUPÉRATION DES DONNÉES TEMPS RÉEL
    # ════════════════════════════════════════════════════════════════════════════════

    def recuperer_prix_temps_reel(self) -> Dict:
        """
        Récupère les prix actuels via yfinance et calcule les indicateurs techniques.

        Returns:
            {ticker: {prix, variation_1h, variation_24h, volume, sma_20, sma_50, rsi_14, bollinger_upper, bollinger_lower}}
        """
        if not yf or not pd or not np:
            print("   ⚠️  yfinance/pandas/numpy non disponibles")
            return {}

        market_data = {}
        tickers_list = list(TRADEABLE.keys())

        print(f"   📊 Récupération données pour {len(tickers_list)} actifs...")

        for ticker in tickers_list:
            try:
                # Télécharge les données historiques (1 mois, hourly)
                hist = safe_api_call(
                    yf.download,
                    ticker,
                    period='1mo',
                    interval='1h',
                    progress=False,
                    agent_name="Robot Trader",
                    default=None
                )

                if hist is None or hist.empty:
                    print(f"    ⚠️  Pas de données pour {ticker}")
                    continue

                # Récupère le prix actuel (dernière clôture)
                prix_actuel = float(hist['Close'].iloc[-1])
                prix_prev_1h = float(hist['Close'].iloc[-2]) if len(hist) > 1 else prix_actuel
                prix_prev_24h = float(hist['Close'].iloc[-24]) if len(hist) > 24 else prix_actuel
                volume = float(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0

                # Variation
                var_1h = ((prix_actuel - prix_prev_1h) / prix_prev_1h * 100) if prix_prev_1h > 0 else 0
                var_24h = ((prix_actuel - prix_prev_24h) / prix_prev_24h * 100) if prix_prev_24h > 0 else 0

                # Indicateurs techniques
                sma_20 = float(hist['Close'].rolling(window=20).mean().iloc[-1]) if len(hist) >= 20 else prix_actuel
                sma_50 = float(hist['Close'].rolling(window=50).mean().iloc[-1]) if len(hist) >= 50 else prix_actuel
                rsi_14 = self._calculer_rsi(hist['Close'], 14)
                bb_upper, bb_middle, bb_lower = self._calculer_bollinger_bands(hist['Close'], 20, 2)
                macd, signal, histogram = self._calculer_macd(hist['Close'])

                market_data[ticker] = {
                    "nom": TRADEABLE[ticker],
                    "prix": prix_actuel,
                    "variation_1h": var_1h,
                    "variation_24h": var_24h,
                    "volume": volume,
                    "sma_20": sma_20,
                    "sma_50": sma_50,
                    "rsi_14": rsi_14,
                    "bollinger_upper": bb_upper,
                    "bollinger_middle": bb_middle,
                    "bollinger_lower": bb_lower,
                    "macd": macd,
                    "macd_signal": signal,
                    "macd_histogram": histogram,
                }

                print(f"    ✓ {ticker:8} €{prix_actuel:8.2f} | RSI:{rsi_14:5.1f} | SMA20/50: {sma_20:.2f}/{sma_50:.2f}")

            except Exception as e:
                log_event("Robot Trader", "warning", f"Erreur récupération {ticker}: {e}")
                print(f"    ❌ Erreur {ticker}: {e}")

        self.market_data = market_data
        return market_data

    # ════════════════════════════════════════════════════════════════════════════════
    # INDICATEURS TECHNIQUES (sans ta-lib)
    # ════════════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _calculer_rsi(closes, period=14) -> float:
        """Calcule le RSI (Relative Strength Index) sur N périodes."""
        if len(closes) < period + 1:
            return 50.0

        deltas = closes.diff().dropna()
        seed = deltas.iloc[:period]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period

        rs_list = [np.nan] * period
        for i in range(period, len(deltas)):
            delta = deltas.iloc[i]
            if delta > 0:
                up = (up * (period - 1) + delta) / period
                down = (down * (period - 1)) / period
            else:
                up = (up * (period - 1)) / period
                down = (down * (period - 1) - delta) / period

            rs = up / down if down != 0 else 0
            rs_list.append(100 - (100 / (1 + rs)))

        return float(rs_list[-1]) if rs_list[-1] is not np.nan else 50.0

    @staticmethod
    def _calculer_bollinger_bands(closes, period=20, std_dev=2) -> Tuple[float, float, float]:
        """Calcule les Bandes de Bollinger."""
        sma = closes.rolling(window=period).mean().iloc[-1]
        std = closes.rolling(window=period).std().iloc[-1]
        upper = float(sma + (std_dev * std)) if not np.isnan(sma) else float(closes.iloc[-1])
        lower = float(sma - (std_dev * std)) if not np.isnan(sma) else float(closes.iloc[-1])
        return upper, float(sma), lower

    @staticmethod
    def _calculer_macd(closes, fast=12, slow=26, signal_period=9) -> Tuple[float, float, float]:
        """Calcule le MACD (Moving Average Convergence Divergence)."""
        ema_fast = closes.ewm(span=fast).mean()
        ema_slow = closes.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal_period).mean()
        histogram = macd - signal
        return float(macd.iloc[-1]), float(signal.iloc[-1]), float(histogram.iloc[-1])

    # ════════════════════════════════════════════════════════════════════════════════
    # GÉNÉRATION DE SIGNAUX
    # ════════════════════════════════════════════════════════════════════════════════

    def generer_signaux(self) -> List[Dict]:
        """
        Génère des signaux d'achat/vente basés sur l'analyse technique.

        Returns:
            List[{ticker, signal: 'BUY'|'SELL'|'HOLD', force: 0-100, raison: str}]
        """
        signaux = []

        for ticker, data in self.market_data.items():
            raison = ""
            force = 0
            signal = "HOLD"

            # ─── SIGNAUX D'ACHAT ───
            if data['rsi_14'] < 30 and data['prix'] < data['bollinger_lower'] * 1.02:
                # Mean reversion: RSI survendu + prix proche bande inférieure
                signal = "BUY"
                force = 75
                raison = f"Mean Reversion: RSI={data['rsi_14']:.1f} (survendu), prix proche BB inférieure"

            elif data['sma_20'] > data['sma_50'] and data['prix'] > data['sma_20']:
                # Golden cross: SMA20 > SMA50 et prix > SMA20
                signal = "BUY"
                force = 60
                raison = f"Golden Cross: SMA20({data['sma_20']:.2f}) > SMA50({data['sma_50']:.2f}), Prix > SMA20"

            elif data['macd_histogram'] > 0 and data['macd'] > data['macd_signal']:
                # MACD bullish
                signal = "BUY"
                force = 50
                raison = f"MACD Bullish: MACD({data['macd']:.4f}) > Signal({data['macd_signal']:.4f})"

            elif data['prix'] > data['bollinger_upper'] * 0.98 and data['volume'] > 0 and data['variation_1h'] > 2:
                # Breakout haut avec volume
                signal = "BUY"
                force = 65
                raison = f"Breakout haut: Prix({data['prix']:.2f}) > BB sup({data['bollinger_upper']:.2f}), Vol élevé"

            # ─── SIGNAUX DE VENTE ───
            elif data['rsi_14'] > 70 and data['prix'] > data['bollinger_upper'] * 0.98:
                # Mean reversion: RSI suracheté + prix proche bande supérieure
                signal = "SELL"
                force = 75
                raison = f"Mean Reversion: RSI={data['rsi_14']:.1f} (suracheté), prix proche BB supérieure"

            elif data['sma_20'] < data['sma_50'] and data['prix'] < data['sma_20']:
                # Death cross: SMA20 < SMA50 et prix < SMA20
                signal = "SELL"
                force = 60
                raison = f"Death Cross: SMA20({data['sma_20']:.2f}) < SMA50({data['sma_50']:.2f})"

            elif data['macd_histogram'] < 0 and data['macd'] < data['macd_signal']:
                # MACD bearish
                signal = "SELL"
                force = 50
                raison = f"MACD Bearish: MACD({data['macd']:.4f}) < Signal({data['macd_signal']:.4f})"

            # ─── VÉRIFICATION DES STOP-LOSS / TAKE-PROFIT ───
            position = next((p for p in self.portfolio['positions'] if p['ticker'] == ticker), None)
            if position:
                pl_pct = position['pl_pct'] / 100.0 if position['pl_pct'] else 0

                # Take-profit hit
                if pl_pct >= TAKE_PROFIT_PCT:
                    signal = "SELL"
                    force = 100
                    raison = f"Take-Profit: P&L={position['pl_pct']:+.2f}% (target {TAKE_PROFIT_PCT*100:.0f}%)"

                # Hard stop-loss hit
                elif pl_pct <= STOP_LOSS_PCT:
                    signal = "SELL"
                    force = 100
                    raison = f"Stop-Loss: P&L={position['pl_pct']:+.2f}% (limit {STOP_LOSS_PCT*100:.0f}%)"

                # Trailing stop (activate only if gain > 8%)
                elif pl_pct > TRAILING_STOP_THRESHOLD:
                    peak_pl = ((position['prix_peak'] - position['prix_entree']) / position['prix_entree']) if position['prix_entree'] > 0 else 0
                    trailing_trigger = peak_pl + TRAILING_STOP_PCT
                    if pl_pct < trailing_trigger:
                        signal = "SELL"
                        force = 85
                        raison = f"Trailing Stop: P&L={position['pl_pct']:+.2f}%, Peak={peak_pl*100:.2f}%"

            if signal != "HOLD":
                signaux.append({
                    "ticker": ticker,
                    "nom": data['nom'],
                    "signal": signal,
                    "force": force,
                    "raison": raison,
                    "data": data,
                })

        self.signals = signaux
        return signaux

    # ════════════════════════════════════════════════════════════════════════════════
    # ENRICHISSEMENT PAR IA
    # ════════════════════════════════════════════════════════════════════════════════

    def enrichir_avec_ia(self) -> List[Dict]:
        """
        Enrichit les signaux avec analyse géopolitique via Claude.
        Limitation: 1 appel IA par cycle, max 800 tokens.
        """
        if not anthropic or not ANTHROPIC_API_KEY or not self.signals:
            return self.signals

        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

            # Prépare le contexte
            contexte = f"""
SIGNAUX TECHNIQUES (À VALIDER):
{json.dumps([{
    'ticker': s['ticker'],
    'signal': s['signal'],
    'force': s['force'],
    'raison': s['raison']
} for s in self.signals], indent=2)}

ÉTAT DU PORTEFEUILLE:
- Capital actuel: €{self.portfolio['meta']['capital_actuel']:.2f}
- Positions ouvertes: {len(self.portfolio['positions'])}
- Performance: {self.portfolio['meta']['performance_totale_pct']:+.2f}%
- Positions: {json.dumps([{
    'ticker': p['ticker'],
    'pl_pct': p['pl_pct'],
    'strategie': p.get('strategie', 'N/A')
} for p in self.portfolio['positions']], indent=2)}

DONNÉES DE MARCHÉ:
{json.dumps({k: {
    'rsi': v['rsi_14'],
    'var_24h': v['variation_24h'],
    'sma_ratio': v['sma_20']/v['sma_50'] if v['sma_50'] > 0 else 1
} for k, v in self.market_data.items()}, indent=2)}
"""

            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=800,
                system="""Tu es un analyste IA pour le trading automatisé. Tu valides les signaux techniques
et ajoutes du contexte géopolitique/macroéconomique. Sois CONCIS et DIRECT.

Réponds en JSON valide avec ce format:
{
  "validated_signals": [
    {
      "ticker": "TICKER",
      "signal": "BUY" | "SELL" | "HOLD",
      "force": 0-100,
      "raison_geopolitique": "Une ligne d'explication macro/géopolitique (si pertinent)"
    }
  ],
  "note_globale": "Contexte de marché global en 1-2 lignes"
}

Règles:
- Valide uniquement si le signal a du sens
- Ajoute du contexte macro (tensions géopolitiques, Fed, etc)
- Force = confiance du signal (0-100)
- REJETTE tout signal qui va contre la tendance globale
""",
                messages=[
                    {"role": "user", "content": f"Valide ces signaux et enrichis-les:\n\n{contexte}"}
                ]
            )

            reponse_text = message.content[0].text
            enriched = json.loads(reponse_text)

            # Fusionne les signaux enrichis avec les originaux
            for enr in enriched.get('validated_signals', []):
                for orig in self.signals:
                    if orig['ticker'] == enr['ticker']:
                        orig['raison_geopolitique'] = enr.get('raison_geopolitique', '')
                        orig['force'] = enr.get('force', orig['force'])
                        orig['signal'] = enr.get('signal', orig['signal'])

            log_event("Robot Trader", "success", f"IA enrichisseur: {len(self.signals)} signaux validés")
            print(f"   ✅ IA enrichisseur: {len(self.signals)} signaux validés")
            print(f"      Note globale: {enriched.get('note_globale', 'N/A')}")

        except Exception as e:
            log_event("Robot Trader", "warning", f"Erreur IA enrichisseur: {e}")
            print(f"   ⚠️  Erreur IA enrichisseur: {e}")

        return self.signals

    # ════════════════════════════════════════════════════════════════════════════════
    # EXÉCUTION DES TRADES
    # ════════════════════════════════════════════════════════════════════════════════

    def executer_signaux(self) -> List[Dict]:
        """
        Exécute les signaux validés en respectant toutes les règles de risque.
        """
        self.executed_trades = []

        # Tri par force (signaux les plus forts en priorité)
        signaux_sorted = sorted(self.signals, key=lambda s: s['force'], reverse=True)

        for signal in signaux_sorted:
            ticker = signal['ticker']
            prix = signal['data']['prix']

            if signal['signal'] == "BUY":
                # Vérifications de risque
                if len(self.portfolio['positions']) >= MAX_SIMULTANEOUS_POSITIONS:
                    log_event("Robot Trader", "warning", f"Max positions ({MAX_SIMULTANEOUS_POSITIONS}) atteint, skip BUY {ticker}")
                    continue

                # Vérifie si position existe déjà
                if any(p['ticker'] == ticker for p in self.portfolio['positions']):
                    log_event("Robot Trader", "info", f"Position {ticker} existe déjà, skip")
                    continue

                # Cash disponible
                cash_reserve = self.portfolio['cash_disponible'] * MIN_CASH_RESERVE_PCT
                cash_investissable = self.portfolio['cash_disponible'] - cash_reserve

                if cash_investissable < MIN_POSITION_EUR:
                    log_event("Robot Trader", "warning", f"Cash insuffisant pour {ticker}")
                    continue

                # Calcule la taille de position
                montant_eur = self._calculer_taille_position(prix)
                if montant_eur < MIN_POSITION_EUR:
                    montant_eur = min(cash_investissable, MAX_POSITION_PCT * self.portfolio['meta']['capital_actuel'])

                if montant_eur < MIN_POSITION_EUR or montant_eur > cash_investissable:
                    log_event("Robot Trader", "info", f"Montant calculé invalide pour {ticker}: €{montant_eur:.2f}")
                    continue

                # Exécute l'achat
                trade = self._acheter(
                    ticker=ticker,
                    nom=signal['nom'],
                    prix=prix,
                    montant_eur=montant_eur,
                    raison_technique=signal['raison'],
                    raison_geopolitique=signal.get('raison_geopolitique', ''),
                    strategie=self._identifier_strategie(signal)
                )
                if trade:
                    self.executed_trades.append(trade)

            elif signal['signal'] == "SELL":
                # Trouve la position
                position = next((p for p in self.portfolio['positions'] if p['ticker'] == ticker), None)
                if not position:
                    continue

                # Exécute la vente
                trade = self._vendre(
                    ticker=ticker,
                    prix=prix,
                    raison_technique=signal['raison'],
                    raison_geopolitique=signal.get('raison_geopolitique', '')
                )
                if trade:
                    self.executed_trades.append(trade)

        log_event("Robot Trader", "success", f"Exécution: {len(self.executed_trades)} trades")
        print(f"   ✅ {len(self.executed_trades)} trades exécutés")

        return self.executed_trades

    def _acheter(self, ticker: str, nom: str, prix: float, montant_eur: float,
                 raison_technique: str, raison_geopolitique: str, strategie: str) -> Optional[Dict]:
        """Exécute un achat et ajoute la position au portefeuille."""
        try:
            nb_actions = montant_eur / prix if prix > 0 else 0
            if nb_actions == 0:
                return None

            position = {
                "ticker": ticker,
                "nom": nom,
                "nb_actions": nb_actions,
                "prix_entree": prix,
                "prix_actuel": prix,
                "prix_peak": prix,
                "montant_investi": montant_eur,
                "pl_euros": 0.0,
                "pl_pct": 0.0,
                "date_achat": datetime.now().isoformat(),
                "raison_technique": raison_technique,
                "raison_geopolitique": raison_geopolitique,
                "stop_loss_prix": prix * (1 + STOP_LOSS_PCT),
                "take_profit_prix": prix * (1 + TAKE_PROFIT_PCT),
                "strategie": strategie,
            }

            self.portfolio['positions'].append(position)
            self.portfolio['cash_disponible'] -= montant_eur

            # Enregistre dans l'historique
            trade = {
                "id": self.portfolio['meta']['nb_trades'] + 1,
                "type": "achat",
                "ticker": ticker,
                "nom": nom,
                "nb_actions": nb_actions,
                "prix": prix,
                "montant": montant_eur,
                "date": datetime.now().isoformat(),
                "raison_technique": raison_technique,
                "raison_geopolitique": raison_geopolitique,
                "strategie": strategie,
                "pl_realise": None,
            }
            self.portfolio['trades_historique'].append(trade)
            self.portfolio['meta']['nb_trades'] += 1

            log_event("Robot Trader", "success", f"ACHAT: {nb_actions:.4f}x {ticker} @ €{prix:.2f} = €{montant_eur:.2f}")
            print(f"   💚 ACHAT: {nb_actions:.4f}x {ticker} @ €{prix:.2f} = €{montant_eur:.2f}")

            return trade

        except Exception as e:
            log_event("Robot Trader", "error", f"Erreur achat {ticker}: {e}")
            print(f"   ❌ Erreur achat {ticker}: {e}")
            return None

    def _vendre(self, ticker: str, prix: float, raison_technique: str, raison_geopolitique: str) -> Optional[Dict]:
        """Exécute une vente et ferme la position."""
        try:
            position = next((p for p in self.portfolio['positions'] if p['ticker'] == ticker), None)
            if not position:
                return None

            montant_realise = position['nb_actions'] * prix
            pl = montant_realise - position['montant_investi']
            pl_pct = (pl / position['montant_investi'] * 100) if position['montant_investi'] > 0 else 0

            # Enregistre dans l'historique
            trade = {
                "id": self.portfolio['meta']['nb_trades'] + 1,
                "type": "vente",
                "ticker": ticker,
                "nom": position['nom'],
                "nb_actions": position['nb_actions'],
                "prix": prix,
                "montant": montant_realise,
                "date": datetime.now().isoformat(),
                "raison_technique": raison_technique,
                "raison_geopolitique": raison_geopolitique,
                "strategie": position.get('strategie', 'N/A'),
                "pl_realise": pl,
                "pl_realise_pct": pl_pct,
            }
            self.portfolio['trades_historique'].append(trade)

            # Mises à jour stats
            self.portfolio['meta']['nb_trades'] += 1
            if pl > 0:
                self.portfolio['meta']['nb_trades_gagnants'] += 1
                self.portfolio['meta']['meilleur_trade_pct'] = max(self.portfolio['meta']['meilleur_trade_pct'], pl_pct)
            else:
                self.portfolio['meta']['nb_trades_perdants'] += 1
                self.portfolio['meta']['pire_trade_pct'] = min(self.portfolio['meta']['pire_trade_pct'], pl_pct)

            # Retire la position et ajoute le cash
            self.portfolio['positions'].remove(position)
            self.portfolio['cash_disponible'] += montant_realise

            log_event("Robot Trader", "success", f"VENTE: {position['nb_actions']:.4f}x {ticker} @ €{prix:.2f} | P&L: €{pl:+.2f} ({pl_pct:+.2f}%)")
            couleur = "❤️" if pl < 0 else "💛" if pl < 100 else "💚"
            print(f"   {couleur} VENTE: {position['nb_actions']:.4f}x {ticker} @ €{prix:.2f} | P&L: €{pl:+.2f} ({pl_pct:+.2f}%)")

            return trade

        except Exception as e:
            log_event("Robot Trader", "error", f"Erreur vente {ticker}: {e}")
            print(f"   ❌ Erreur vente {ticker}: {e}")
            return None

    @staticmethod
    def _identifier_strategie(signal: Dict) -> str:
        """Identifie la stratégie utilisée basée sur le signal."""
        raison = signal['raison'].lower()
        if 'mean reversion' in raison or 'rsi' in raison:
            return 'mean_reversion'
        elif 'cross' in raison or 'sma' in raison:
            return 'momentum'
        elif 'macd' in raison:
            return 'macd'
        elif 'breakout' in raison:
            return 'breakout'
        else:
            return 'autre'

    # ════════════════════════════════════════════════════════════════════════════════
    # GESTION DU RISQUE
    # ════════════════════════════════════════════════════════════════════════════════

    def _calculer_taille_position(self, prix_action: float) -> float:
        """
        Calcule la taille de position en euros.
        - Max 25% du capital par position
        - Min 200€
        - Laisse 10% de réserve cash
        """
        capital = self.portfolio['meta']['capital_actuel']
        cash_reserve = capital * MIN_CASH_RESERVE_PCT
        capital_investissable = capital - cash_reserve
        montant_max = min(
            capital_investissable * MAX_POSITION_PCT,
            self.portfolio['cash_disponible'] * 0.9  # 90% du cash disponible
        )
        return max(MIN_POSITION_EUR, min(montant_max, self.portfolio['cash_disponible'] * 0.8))

    # ════════════════════════════════════════════════════════════════════════════════
    # MISE À JOUR DES POSITIONS
    # ════════════════════════════════════════════════════════════════════════════════

    def mettre_a_jour_prix(self):
        """Met à jour les prix et P&L de toutes les positions."""
        capital_total = self.portfolio['cash_disponible']

        for position in self.portfolio['positions']:
            ticker = position['ticker']
            if ticker not in self.market_data:
                continue

            prix_actuel = self.market_data[ticker]['prix']
            position['prix_actuel'] = prix_actuel

            # Mise à jour du prix peak (pour trailing stop)
            if prix_actuel > position['prix_peak']:
                position['prix_peak'] = prix_actuel

            # Calcul P&L
            valeur_position = position['nb_actions'] * prix_actuel
            position['pl_euros'] = valeur_position - position['montant_investi']
            position['pl_pct'] = (position['pl_euros'] / position['montant_investi'] * 100) if position['montant_investi'] > 0 else 0

            capital_total += valeur_position

        # Mise à jour capital actuel et performance
        self.portfolio['meta']['capital_actuel'] = capital_total
        self.portfolio['meta']['derniere_maj'] = datetime.now().isoformat()

        capital_initial = self.portfolio['meta']['capital_initial']
        perf_pct = ((capital_total - capital_initial) / capital_initial * 100) if capital_initial > 0 else 0
        self.portfolio['meta']['performance_totale_pct'] = perf_pct

        # Win rate
        if self.portfolio['meta']['nb_trades'] > 0:
            self.portfolio['meta']['win_rate'] = (
                self.portfolio['meta']['nb_trades_gagnants'] / self.portfolio['meta']['nb_trades'] * 100
            )

    def _calculer_performance(self) -> Dict:
        """Calcule les métriques de performance."""
        capital = self.portfolio['meta']['capital_actuel']
        initial = self.portfolio['meta']['capital_initial']

        return {
            "capital_total": capital,
            "capital_investis": capital - self.portfolio['cash_disponible'],
            "cash_libre": self.portfolio['cash_disponible'],
            "performance_pct": self.portfolio['meta']['performance_totale_pct'],
            "performance_eur": capital - initial,
            "win_rate": self.portfolio['meta']['win_rate'],
            "nb_trades": self.portfolio['meta']['nb_trades'],
            "nb_positions": len(self.portfolio['positions']),
            "meilleur_trade": self.portfolio['meta']['meilleur_trade_pct'],
            "pire_trade": self.portfolio['meta']['pire_trade_pct'],
        }

    # ════════════════════════════════════════════════════════════════════════════════
    # EXPORT DONNÉES POUR LA PAGE WEB
    # ════════════════════════════════════════════════════════════════════════════════

    def exporter_donnees_page(self):
        """Exporte les données pour le dashboard HTML."""
        try:
            Path(DATA_DIR).mkdir(exist_ok=True)

            # Ajoute point à la courbe d'équité
            today = datetime.now().strftime("%Y-%m-%d")
            if not self.portfolio['equity_curve'] or self.portfolio['equity_curve'][-1]['date'] != today:
                self.portfolio['equity_curve'].append({
                    "date": today,
                    "valeur": self.portfolio['meta']['capital_actuel']
                })
            # Limite à 90 jours
            self.portfolio['equity_curve'] = self.portfolio['equity_curve'][-90:]

            # Données pour la page
            live_data = {
                "meta": self.portfolio['meta'],
                "cash_disponible": self.portfolio['cash_disponible'],
                "positions": self.portfolio['positions'][-10:],  # Dernières 10
                "trades_recent": self.portfolio['trades_historique'][-50:],  # Derniers 50 trades
                "performance": self._calculer_performance(),
                "equity_curve": self.portfolio['equity_curve'],
                "signaux_actifs": [
                    {
                        "ticker": s['ticker'],
                        "signal": s['signal'],
                        "force": s['force'],
                        "raison": s['raison'][:100]
                    }
                    for s in self.signals[-20:]
                ],
            }

            with open(PORTFOLIO_LIVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(live_data, f, ensure_ascii=False, indent=2)

            log_event("Robot Trader", "success", f"Données live exportées vers {PORTFOLIO_LIVE_FILE}")

        except Exception as e:
            log_event("Robot Trader", "error", f"Erreur export données: {e}")
            print(f"   ❌ Erreur export: {e}")

    # ════════════════════════════════════════════════════════════════════════════════
    # CYCLE PRINCIPAL
    # ════════════════════════════════════════════════════════════════════════════════

    def run_cycle(self) -> Dict:
        """
        Exécute un cycle complet de trading (toutes les heures).

        Étapes:
        1. Récupère les prix temps réel
        2. Met à jour les positions ouvertes
        3. Génère signaux techniques
        4. Enrichit avec l'IA
        5. Exécute signaux
        6. Sauvegarde portfolio
        7. Exporte données pour le web

        Returns: Résumé du cycle
        """
        print(f"\n🤖 ═══════════════════════════════════════════════════════════════")
        print(f"🤖 CYCLE TRADER — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🤖 ═══════════════════════════════════════════════════════════════")

        log_event("Robot Trader", "start", "Démarrage cycle trading")

        try:
            # 1. Récupère les prix temps réel
            print(f"\n📊 [1/7] Récupération données temps réel...")
            self.recuperer_prix_temps_reel()

            # 2. Met à jour les positions
            print(f"\n📊 [2/7] Mise à jour des positions...")
            self.mettre_a_jour_prix()
            for pos in self.portfolio['positions']:
                print(f"    {pos['ticker']}: €{pos['prix_actuel']:.2f} | P&L: {pos['pl_pct']:+.2f}%")

            # 3. Génère signaux techniques
            print(f"\n📊 [3/7] Génération signaux techniques...")
            self.generer_signaux()
            print(f"    {len(self.signals)} signaux générés")

            # 4. Enrichit avec l'IA
            print(f"\n📊 [4/7] Enrichissement par IA...")
            self.enrichir_avec_ia()

            # 5. Exécute signaux
            print(f"\n📊 [5/7] Exécution des signaux...")
            self.executer_signaux()

            # 6. Sauvegarde portfolio
            print(f"\n📊 [6/7] Sauvegarde portfolio...")
            self._sauvegarder_portfolio()

            # 7. Exporte données pour le web
            print(f"\n📊 [7/7] Export données pour le dashboard...")
            self.exporter_donnees_page()

            # Résumé
            performance = self._calculer_performance()
            resume = {
                "timestamp": datetime.now().isoformat(),
                "capital": performance['capital_total'],
                "performance_pct": performance['performance_pct'],
                "positions_actives": performance['nb_positions'],
                "trades_executed": len(self.executed_trades),
                "trades_total": performance['nb_trades'],
                "win_rate": performance['win_rate'],
            }

            print(f"\n📈 ═══════════════════════════════════════════════════════════════")
            print(f"📈 RÉSUMÉ CYCLE")
            print(f"📈 ═══════════════════════════════════════════════════════════════")
            print(f"   Capital: €{resume['capital']:,.2f} | Performance: {resume['performance_pct']:+.2f}%")
            print(f"   Positions: {resume['positions_actives']} | Trades exécutés: {resume['trades_executed']}")
            print(f"   Total trades: {resume['trades_total']} | Win rate: {resume['win_rate']:.1f}%")
            print(f"📈 ═══════════════════════════════════════════════════════════════\n")

            log_event("Robot Trader", "success", f"Cycle complété: {resume['trades_executed']} trades, Performance: {resume['performance_pct']:+.2f}%")

            return resume

        except Exception as e:
            log_event("Robot Trader", "error", f"Erreur cycle: {e}")
            print(f"   ❌ ERREUR CYCLE: {e}")
            return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN — TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🤖 ALPHABOT — ROBOT TRADER AUTONOME TEST")
    print("="*80 + "\n")

    robot = RobotTrader()
    print()

    # Exécute un cycle complet
    resume = robot.run_cycle()

    print(f"\n✅ Test complété avec succès")
    print(f"   Résumé: {json.dumps(resume, indent=2, default=str)}")
