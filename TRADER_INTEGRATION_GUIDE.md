# 🤖 Robot Trader — Guide d'Intégration

## Intégration avec l'Orchestrateur

### 1. Ajouter au orchestrateur.py

```python
# Dans orchestrateur.py
from agents.agent_trader import RobotTrader

def run_trading_cycle():
    """Exécute un cycle complet du robot trader."""
    robot = RobotTrader()
    resume = robot.run_cycle()
    return resume
```

### 2. Scheduler — Toutes les heures (9h-18h Paris)

```python
import schedule

# Dans la section scheduling
for hour in range(9, 18):
    schedule.every().day.at(f"{hour:02d}:00").do(run_trading_cycle)

# Alternative: exécuter sur événement
# robot.run_cycle()  # Après récupération données veille
```

### 3. Intégration avec agent_ceo_brief.py

```python
# Dans agent_ceo_brief.py, ajouter section trader

from agents.agent_trader import RobotTrader

robot = RobotTrader()
portfolio = robot.portfolio

brief += f"""
## 💹 PERFORMANCE PORTEFEUILLE
- Capital: €{portfolio['meta']['capital_actuel']:,.2f} / Objectif: €{portfolio['meta']['objectif']:,.2f}
- Performance: {portfolio['meta']['performance_totale_pct']:+.2f}%
- Positions: {len(portfolio['positions'])} | Trades: {portfolio['meta']['nb_trades']}
- Win Rate: {portfolio['meta']['win_rate']:.1f}%
- Meilleur trade: {portfolio['meta']['meilleur_trade_pct']:+.2f}% | Pire: {portfolio['meta']['pire_trade_pct']:+.2f}%
"""
```

### 4. Dashboard HTML — Afficher les données

```html
<!-- Dans investissement.html -->
<script src="../data/portfolio_live.json"></script>

<div id="trader-dashboard">
  <!-- Capital -->
  <div class="card">
    <h3>Capital Total</h3>
    <div class="value">€<span id="capital">0</span></div>
    <div class="subtext">Performance: <span id="performance" class="perf-value">0%</span></div>
  </div>

  <!-- Positions -->
  <div class="positions">
    <h3>Positions Actives (<span id="nb-positions">0</span>)</h3>
    <table id="positions-table">
      <thead>
        <tr>
          <th>Ticker</th>
          <th>Prix</th>
          <th>P&L</th>
          <th>Stratégie</th>
        </tr>
      </thead>
      <tbody id="positions-tbody"></tbody>
    </table>
  </div>

  <!-- Equity Curve -->
  <div class="chart">
    <canvas id="equity-chart"></canvas>
  </div>

  <!-- Trades Récents -->
  <div class="trades">
    <h3>Derniers Trades</h3>
    <table id="trades-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Type</th>
          <th>Ticker</th>
          <th>Montant</th>
          <th>P&L</th>
        </tr>
      </thead>
      <tbody id="trades-tbody"></tbody>
    </table>
  </div>
</div>

<script>
// Charger portfolio_live.json
async function loadPortfolioData() {
  const res = await fetch('../data/portfolio_live.json');
  const data = await res.json();

  // Maj capital
  document.getElementById('capital').textContent =
    data.meta.capital_actuel.toLocaleString('fr-FR', {maximumFractionDigits: 2});

  // Maj performance
  const perfEl = document.getElementById('performance');
  const perf = data.meta.performance_totale_pct;
  perfEl.textContent = `${perf:+.2f}%`;
  perfEl.classList.toggle('positive', perf >= 0);
  perfEl.classList.toggle('negative', perf < 0);

  // Maj positions
  const tbodyPos = document.getElementById('positions-tbody');
  tbodyPos.innerHTML = data.positions.map(p => `
    <tr>
      <td>${p.ticker}</td>
      <td>€${p.prix_actuel.toFixed(2)}</td>
      <td class="${p.pl_pct >= 0 ? 'positive' : 'negative'}">
        €${p.pl_euros.toFixed(2)} (${p.pl_pct:+.2f}%)
      </td>
      <td>${p.strategie}</td>
    </tr>
  `).join('');

  document.getElementById('nb-positions').textContent = data.positions.length;

  // Maj trades
  const tbodyTrades = document.getElementById('trades-tbody');
  tbodyTrades.innerHTML = data.trades_recent.slice(-10).reverse().map(t => `
    <tr>
      <td>${new Date(t.date).toLocaleString('fr-FR')}</td>
      <td>${t.type.toUpperCase()}</td>
      <td>${t.ticker}</td>
      <td>€${t.montant.toFixed(2)}</td>
      <td class="${t.pl_realise >= 0 ? 'positive' : 'negative'}">
        ${t.pl_realise !== null ? `€${t.pl_realise.toFixed(2)}` : '—'}
      </td>
    </tr>
  `).join('');

  // Equity curve chart
  drawEquityCurve(data.equity_curve);
}

// Rafraîchir toutes les minutes
setInterval(loadPortfolioData, 60000);
loadPortfolioData();
</script>
```

### 5. Export CSV pour rapports

```python
# Dans agent_analytics.py, ajouter fonction

import csv
from agents.agent_trader import RobotTrader

def exporter_trades_csv():
    """Exporte l'historique des trades en CSV."""
    robot = RobotTrader()
    portfolio = robot.portfolio

    with open('outputs/trades_historique.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'date', 'type', 'ticker', 'nom', 'nb_actions', 'prix', 'montant',
            'pl_realise', 'pl_pct', 'strategie', 'raison'
        ])
        writer.writeheader()

        for trade in portfolio['trades_historique']:
            writer.writerow({
                'date': trade['date'],
                'type': trade['type'],
                'ticker': trade['ticker'],
                'nom': trade['nom'],
                'nb_actions': f"{trade['nb_actions']:.4f}",
                'prix': f"{trade['prix']:.2f}",
                'montant': f"{trade['montant']:.2f}",
                'pl_realise': f"{trade.get('pl_realise', ''):.2f}" if trade.get('pl_realise') else '',
                'pl_pct': f"{trade.get('pl_realise_pct', ''):.2f}%" if trade.get('pl_realise_pct') else '',
                'strategie': trade.get('strategie', 'N/A'),
                'raison': trade.get('raison_technique', ''),
            })
```

### 6. Alertes & Notifications

```python
# Dans agent_commercial.py, ajouter alertes subscriber

from agents.agent_trader import RobotTrader

def envoyer_alerte_trade(trade):
    """Envoie une alerte de trade aux abonnés."""
    alerte = f"""
🚨 NOUVEAU TRADE — Robot Trader

{'🟢 ACHAT' if trade['type'] == 'achat' else '🔴 VENTE'} {trade['ticker']} ({trade['nom']})

Montant: €{trade['montant']:.2f}
Prix: €{trade['prix']:.2f}
Raison: {trade.get('raison_technique', 'N/A')}
Contexte: {trade.get('raison_geopolitique', 'N/A')}

Portfolio:
- Capital: €{robot.portfolio['meta']['capital_actuel']:.2f}
- Performance: {robot.portfolio['meta']['performance_totale_pct']:+.2f}%
"""

    # Envoyer aux abonnés via Brevo/Mailgun
    # ...
```

---

## Monitoring & Health Checks

### Vérifier que le robot tourne correctement

```python
def health_check_trader():
    """Vérifie la santé du robot trader."""
    robot = RobotTrader()

    checks = {
        "portfolio_loaded": len(robot.portfolio) > 0,
        "has_positions": len(robot.portfolio['positions']) >= 0,
        "capital_positive": robot.portfolio['meta']['capital_actuel'] > 0,
        "trades_logged": robot.portfolio['meta']['nb_trades'] >= 0,
        "activity_logged": os.path.exists("data/activity_log.jsonl"),
        "portfolio_saved": os.path.exists("data/portfolio.json"),
        "portfolio_live_saved": os.path.exists("data/portfolio_live.json"),
    }

    return all(checks.values()), checks
```

---

## Performance & Benchmarking

### Comparer à des benchmarks

```python
def comparer_performance():
    """Compare le robot à des indices."""
    robot = RobotTrader()

    # Récupère return du robot
    robot_return = robot.portfolio['meta']['performance_totale_pct']

    # Récupère returns des benchmarks
    # (S&P 500, DAX, etc.)

    # Calcul Sharpe ratio
    # Calcul drawdown max
    # Calcul volatilité

    return {
        "robot_return": robot_return,
        "sp500_return": ...,
        "dax_return": ...,
        "outperformance": robot_return - ...,
    }
```

---

## Troubleshooting

### Le robot ne fait pas de trades

**Checklist:**
1. ✓ Vérifier que `recuperer_prix_temps_reel()` retourne des données
2. ✓ Vérifier que `generer_signaux()` génère au moins 1 signal
3. ✓ Vérifier les règles de risque (max positions, cash min)
4. ✓ Logs dans `data/activity_log.jsonl`

```bash
# Voir derniers logs
tail -20 data/activity_log.jsonl | jq .
```

### Performance très basse

1. Vérifier les paramètres:
   ```python
   STOP_LOSS_PCT = -0.08      # Couper trop tôt?
   TAKE_PROFIT_PCT = 0.15     # Objectif trop haut?
   ```

2. Analyser win_rate:
   - < 50% → revoir filtres de signal
   - 50-60% → normal, augmenter take-profit
   - > 70% → excellent, mais attention drawdown

3. Vérifier types de signaux:
   ```python
   for trade in portfolio['trades_historique'][-20:]:
       print(f"{trade['ticker']} {trade['strategie']} {trade.get('pl_realise_pct', 'N/A')}")
   ```

---

## Coûts & Optimisation

### API Costs

- **yfinance**: Gratuit (Yahoo Finance)
- **Claude API**: ~$0.30-0.50 par cycle (800 tokens)
- **Par jour (9 cycles)**: ~$3-5
- **Par mois**: ~$90-150

### Optimisations coûts

1. **Réduire appels Claude**
   ```python
   # Toutes les 4 heures seulement
   if datetime.now().hour % 4 == 0:
       self.enrichir_avec_ia()
   ```

2. **Réduire tokens**
   ```python
   max_tokens=400  # au lieu de 800
   ```

3. **Batch processing**
   - Valider 5 signaux dans 1 appel
   - Paramétrer response format JSON

---

## Roadmap

### Phase 1 (Done ✅)
- [x] Analyse technique complète (7 indicateurs)
- [x] Gestion risque stricte
- [x] Enrichissement IA
- [x] Logging/monitoring

### Phase 2 (À faire)
- [ ] ML pour optimisation paramètres
- [ ] Backtesting engine
- [ ] Correlation analysis
- [ ] Portfolio rebalancing

### Phase 3
- [ ] Options trading
- [ ] Forex pairs
- [ ] Crypto integration (avec gouvernance)
- [ ] Multi-strategy ensemble

---

**Dernière mise à jour:** 2026-03-21
