# 🤖 AlphaBot Robot Trader — Documentation Complète

## Vue d'ensemble

Le **Robot Trader** (`agents/agent_trader.py`) est un système de trading entièrement autonome qui:
- **Trade TOUTES LES HEURES** pendant les heures de marché (9h-18h Paris)
- **Trades UNIQUEMENT les actions** — univers: AAPL, NVDA, TSLA, MC.PA, TTE.PA, XOM, LMT, SPY, GLD
- **Utilise 3 stratégies techniques** + Claude IA pour les décisions
- **Gère le risque strictement** avec stop-loss, take-profit, position sizing
- **Enregistre CHAQUE décision** pour transparence totale aux abonnés
- **Capital fictif**: 10,000€ → Objectif: 100,000€

---

## Architecture

### Classes principales

```python
class RobotTrader:
    """Robot trader autonome avec analyse technique + IA"""
```

### Flux de données

```
1. recuperer_prix_temps_reel()
   ↓ Télécharge données 1 mois, intervalle 1h via yfinance

2. calculer_indicateurs_techniques()
   ↓ SMA 20/50, RSI 14, Bollinger Bands 20/2, MACD 12/26/9

3. generer_signaux()
   ↓ Identifie opportunités: Golden Cross, Death Cross, Mean Reversion, MACD, Breakout

4. enrichir_avec_ia()
   ↓ Claude valide signaux + ajoute contexte géopolitique (800 tokens max)

5. executer_signaux()
   ↓ Exécute achats/ventes en respectant limites de risque

6. mettre_a_jour_prix()
   ↓ Recalcule positions, P&L, capital

7. exporter_donnees_page()
   ↓ Génère portfolio_live.json pour le dashboard HTML
```

---

## Stratégies de Trading

### 1. 📈 Momentum (Golden Cross / Death Cross)

**Signal d'ACHAT:**
- SMA 20 > SMA 50 (golden cross)
- Prix > SMA 20
- Force: 60

**Signal de VENTE:**
- SMA 20 < SMA 50 (death cross)
- Prix < SMA 20
- Force: 60

### 2. 🔄 Mean Reversion (RSI + Bollinger Bands)

**Signal d'ACHAT:**
- RSI < 30 (survendu)
- Prix < Bande Bollinger inférieure × 1.02
- Force: 75

**Signal de VENTE:**
- RSI > 70 (suracheté)
- Prix > Bande Bollinger supérieure × 0.98
- Force: 75

### 3. 📊 MACD (Moving Average Convergence Divergence)

**Signal d'ACHAT:**
- MACD > Signal line
- MACD histogram > 0
- Force: 50

**Signal de VENTE:**
- MACD < Signal line
- MACD histogram < 0
- Force: 50

### 4. 🚀 Breakout avec Volume

**Signal d'ACHAT:**
- Prix > Bande Bollinger supérieure × 0.98
- Volume > Moyenne 20 périodes
- Variation 1h > +2%
- Force: 65

---

## Gestion du Risque

### Position Sizing

```python
MAX_POSITION_PCT = 0.25          # 25% du capital max par position
MIN_POSITION_EUR = 200            # Montant minimum 200€
MAX_SIMULTANEOUS_POSITIONS = 5   # Max 5 positions ouvertes
MIN_CASH_RESERVE_PCT = 0.10      # Réserve cash min 10%
```

**Calcul de la taille:**
```
1. Reserve = Capital × 10%
2. Capital investissable = Capital total - Reserve
3. Position size = min(
     Capital investissable × 25%,
     Cash disponible × 90%
   )
```

### Stop-Loss & Take-Profit

| Règle | Déclencheur | Logique |
|-------|-------------|---------|
| **Hard Stop-Loss** | P&L ≤ -8% | Coupe les pertes rapidement |
| **Take-Profit** | P&L ≥ +15% | Cristallise les gains |
| **Trailing Stop** | P&L ≤ -5% depuis peak | Laisse courir les gagnants |
| | (activation @ +8%) | |

**Exemple:**
```
Achat AAPL @ €180
→ Stop-loss: €165.60 (-8%)
→ Take-profit: €207 (+15%)
→ Si +10% → Peak = €198, Trailing stop @ €188.10 (-5% from peak)
```

---

## Indicateurs Techniques (sans ta-lib)

### SMA 20/50 (Simple Moving Averages)
```python
sma_20 = closes.rolling(window=20).mean()
sma_50 = closes.rolling(window=50).mean()
```

### RSI 14 (Relative Strength Index)
```python
Calcul standard avec période 14
RSI = 100 - (100 / (1 + RS))
où RS = avg_gain / avg_loss
```

### Bollinger Bands (20, 2 std dev)
```python
SMA = closes.rolling(20).mean()
STD = closes.rolling(20).std()
Upper = SMA + 2 * STD
Lower = SMA - 2 * STD
```

### MACD (12, 26, 9)
```python
MACD = EMA12 - EMA26
Signal = EMA9(MACD)
Histogram = MACD - Signal
```

---

## Enrichissement par IA (Claude)

### Flux Claude

1. **Contexte fourni:**
   - Signaux techniques candidats (ticker, signal, force, raison)
   - État du portefeuille (capital, positions, performance)
   - Données de marché (RSI, variations, ratios SMA)

2. **Claude valide et enrichit:**
   - Accepte/rejette signaux basés sur contexte macro
   - Ajoute raison géopolitique (1 ligne)
   - Ajuste force du signal (0-100)
   - Fournit note globale de marché

3. **Optimisation coûts:**
   - 1 appel IA par cycle (max)
   - max_tokens=800 (contrôle coûts)
   - Dégradation gracieuse si API échoue

### Prompt système

```
Tu es un analyste IA pour trading automatisé.
Valide signaux techniques + ajoute contexte géopolitique.
Sois CONCIS et DIRECT.

Rejette signaux contraires à la tendance globale.
Raison géopolitique: une ligne (tensions, Fed, etc.)
```

---

## Structure du Portfolio JSON

### Meta (Statistiques globales)

```json
{
  "meta": {
    "capital_initial": 10000,
    "capital_actuel": 12500,
    "objectif": 100000,
    "date_creation": "2026-03-21",
    "derniere_maj": "2026-03-21T15:30:00",
    "devise": "EUR",
    "performance_totale_pct": 25.0,
    "nb_trades": 42,
    "nb_trades_gagnants": 28,
    "nb_trades_perdants": 14,
    "meilleur_trade_pct": 18.5,
    "pire_trade_pct": -7.8,
    "win_rate": 66.7,
    "sharpe_ratio": 1.2
  }
}
```

### Position (Titre ouvert)

```json
{
  "ticker": "AAPL",
  "nom": "Apple",
  "nb_actions": 5.234,
  "prix_entree": 178.50,
  "prix_actuel": 182.20,
  "prix_peak": 185.00,
  "montant_investi": 934.67,
  "pl_euros": 18.97,
  "pl_pct": 2.03,
  "date_achat": "2026-03-21T10:00:00",
  "raison_technique": "Golden Cross: SMA20 > SMA50",
  "raison_geopolitique": "Apple bénéficie détente USA-Chine",
  "stop_loss_prix": 164.22,
  "take_profit_prix": 205.28,
  "strategie": "momentum"
}
```

### Trade (Historique)

```json
{
  "id": 1,
  "type": "achat",
  "ticker": "AAPL",
  "nom": "Apple",
  "nb_actions": 5.234,
  "prix": 178.50,
  "montant": 934.67,
  "date": "2026-03-21T10:00:00",
  "raison_technique": "Golden Cross",
  "raison_geopolitique": "Détente USA-Chine",
  "strategie": "momentum",
  "pl_realise": null  // null pour achats, montant pour ventes
}
```

### Equity Curve (Performance historique)

```json
{
  "equity_curve": [
    { "date": "2026-03-21", "valeur": 10000 },
    { "date": "2026-03-22", "valeur": 10250 },
    { "date": "2026-03-23", "valeur": 10412 }
  ]
}
```

---

## Fichiers Générés

### data/portfolio.json
Sauvegarde complète du portefeuille (positions, historique, stats)

### data/portfolio_live.json
Fichier léger pour le dashboard (positions actuelles, derniers trades, equity curve)

### data/activity_log.jsonl
Log de tous les événements (un event par ligne)

---

## Utilisation

### Initialisation simple

```python
from agents.agent_trader import RobotTrader

robot = RobotTrader()
```

### Exécution d'un cycle complet

```python
resume = robot.run_cycle()

# Retourne:
# {
#   "timestamp": "2026-03-21T15:30:00",
#   "capital": 12500.50,
#   "performance_pct": 25.0,
#   "positions_actives": 3,
#   "trades_executed": 2,
#   "trades_total": 42,
#   "win_rate": 66.7
# }
```

### Exécution planifiée (toutes les heures)

```python
import schedule
import time

robot = RobotTrader()

def run_trading_cycle():
    robot.run_cycle()

# Schedule every hour during market hours (9-18h Paris)
for hour in range(9, 18):
    schedule.every().day.at(f"{hour:02d}:00").do(run_trading_cycle)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Test en ligne de commande

```bash
cd /sessions/awesome-kind-sagan/mnt/Alphabot
python3 agents/agent_trader.py
```

---

## Logs & Monitoring

### Événements loggés

Chaque action importante crée un événement:

```json
{
  "ts": "2026-03-21T15:30:00",
  "agent": "Robot Trader",
  "type": "success",
  "message": "ACHAT: 5.2340x AAPL @ €178.50 = €934.67",
  "data": {}
}
```

### Types d'événements

| Type | Usage |
|------|-------|
| `start` | Début cycle |
| `success` | Trade exécuté |
| `warning` | Position max atteint, cash insuffisant |
| `error` | Exception |
| `info` | Information générale |

### Lecture des logs

```python
from utils.activity_logger import lire_events, exporter_activity_feed

# Lire derniers 100 événements
events = lire_events(100)

# Exporter pour dashboard HTML
exporter_activity_feed(100)
```

---

## Optimisations & Tips

### Pour augmenter la profitabilité

1. **Ajuster tailles de position**
   ```python
   MAX_POSITION_PCT = 0.30  # Augmenter à 30% si confiant
   ```

2. **Affiner stop-loss/take-profit**
   ```python
   STOP_LOSS_PCT = -0.10    # -10% (plus tolérant)
   TAKE_PROFIT_PCT = 0.20   # +20% (objectif plus haut)
   ```

3. **Ajouter filtres par volatilité**
   - Ne trade que RSI dans [20, 80] durant haute volatilité
   - Skip trades si variation 24h > 5%

4. **Adapter à l'heure du jour**
   - 9h-11h: Momentum fort → favoriser Golden Cross
   - 14h-16h: Range-bound → favoriser Mean Reversion
   - 16h-18h: Fermer positions (fin de séance)

### Dépannage

**Pas de trades exécutés**
- Vérifier yfinance disponible: `python3 -c "import yfinance; print(yfinance.__version__)"`
- Vérifier pandas/numpy: `python3 -c "import pandas, numpy; print('OK')"`
- Vérifier connectivité: `curl -s https://query2.finance.yahoo.com`

**Erreurs API Claude**
- Robot continue avec signaux non enrichis
- Logs dans `data/activity_log.jsonl`

**Portfolio corrompu**
- Backup automatique crée un `.lock`
- Si bloqué: supprimer `data/portfolio.json.lock`

---

## Limites & Considérations

### Limitations

1. **Données horaires uniquement** → pas scalpe minute
2. **Pas de slippage/frais** → simulations optimistes
3. **Pas d'analyse de corrélation** → peut concentrer dans secteur
4. **IA peut refuser signaux** → dépend contexte macro

### Améliorations futures

- [ ] Ajouter VIX hedge pour haute volatilité
- [ ] Machine learning pour optimiser stop-loss
- [ ] Corrélation avec indices (diversification)
- [ ] Rebalance quotidien selon volatilité
- [ ] Alerts Telegram/Email pour chaque trade

---

## Fichiers Associés

| Fichier | Rôle |
|---------|------|
| `agents/agent_trader.py` | Code principal (43 KB) |
| `data/portfolio.json` | Sauvegarde portefeuille |
| `data/portfolio_live.json` | Données dashboard |
| `data/activity_log.jsonl` | Logs transactions |
| `config.py` | Tickers, API keys |
| `utils/file_lock.py` | Prévient corruptions |
| `utils/api_retry.py` | Retry avec backoff |
| `utils/activity_logger.py` | Logging centralisé |

---

## Contact & Support

**Questions?** Voir `orchestrateur.py` pour intégration complète.

**Document généré:** 2026-03-21
