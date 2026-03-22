"""
AlphaBot — Agent Investissement 💰
Rôle : Gérer un portefeuille fictif de 10 000€ avec objectif 100K.
Chaque décision est justifiée par une thèse géopolitique ou macro-économique.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import anthropic
except ImportError:
    anthropic = None

# Import config depuis le dossier parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, OUTPUT_DIR
from utils.activity_logger import log_event as _log

# Chemins
DATA_DIR = "data"
PORTFOLIO_FILE = "data/portfolio.json"
HTML_OUTPUT = os.path.join(OUTPUT_DIR, "investissement.html")


class AgentInvestissement:
    """
    Agent gestionnaire de portefeuille fictif.
    Gère positions, historique de trades, et prend des décisions basées sur Claude IA.
    """

    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.portfolio = self.lire_portfolio()
        print(f"💰 Agent Investissement initialisé — {self.timestamp}")
        print(f"   Capital: {self.portfolio['meta']['capital_actuel']:.2f}€ / Objectif: {self.portfolio['meta']['objectif']:.2f}€")

    # ─── LECTURE / SAUVEGARDE ──────────────────────────────────────────────────────

    def lire_portfolio(self) -> dict:
        """Charge le portfolio depuis JSON."""
        try:
            if os.path.exists(PORTFOLIO_FILE):
                with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"   ❌ Erreur lecture portfolio: {e}")

        # Retourne un portefeuille vide par défaut
        return {
            "meta": {
                "capital_initial": 10000,
                "capital_actuel": 10000,
                "objectif": 100000,
                "date_creation": datetime.now().strftime("%Y-%m-%d"),
                "derniere_maj": datetime.now().strftime("%Y-%m-%d"),
                "devise": "EUR",
                "performance_totale_pct": 0.0,
                "nb_trades": 0
            },
            "cash_disponible": 10000,
            "positions": [],
            "trades_historique": [],
            "theses_investissement": {
                "strategie_globale": "Portefeuille IA orienté macro-géopolitique.",
                "theses_actives": []
            }
        }

    def sauvegarder_portfolio(self, portfolio: dict) -> bool:
        """Sauvegarde le portfolio en JSON."""
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
                json.dump(portfolio, f, ensure_ascii=False, indent=2)
            self.portfolio = portfolio
            _log("portfolio_saved", {"timestamp": datetime.now().isoformat(), "capital": portfolio['meta']['capital_actuel']})
            return True
        except Exception as e:
            print(f"   ❌ Erreur sauvegarde: {e}")
            return False

    # ─── OPÉRATIONS PORTEFEUILLE ───────────────────────────────────────────────────

    def acheter(self, ticker: str, nom: str, nb_actions: float, prix_entree: float, raison_geopolitique: str) -> bool:
        """Ajoute une position au portefeuille."""
        cout_total = nb_actions * prix_entree

        if cout_total > self.portfolio['cash_disponible']:
            print(f"   ❌ Solde insuffisant. Coût: {cout_total:.2f}€, Disponible: {self.portfolio['cash_disponible']:.2f}€")
            return False

        # Crée la position
        position = {
            "ticker": ticker,
            "nom": nom,
            "nb_actions": nb_actions,
            "prix_entree": prix_entree,
            "prix_actuel": prix_entree,
            "montant_investi": cout_total,
            "pl_euros": 0.0,
            "pl_pct": 0.0,
            "date_achat": datetime.now().strftime("%Y-%m-%d"),
            "raison_geopolitique": raison_geopolitique,
            "these_id": None
        }

        # Ajoute au portefeuille
        self.portfolio['positions'].append(position)
        self.portfolio['cash_disponible'] -= cout_total

        # Enregistre le trade
        trade = {
            "type": "achat",
            "ticker": ticker,
            "nom": nom,
            "nb_actions": nb_actions,
            "prix": prix_entree,
            "montant": cout_total,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "raison": raison_geopolitique
        }
        self.portfolio['trades_historique'].append(trade)
        self.portfolio['meta']['nb_trades'] += 1

        print(f"   ✅ Achat: {nb_actions} x {ticker} @ {prix_entree:.2f}€ = {cout_total:.2f}€")
        _log("achat_position", {"ticker": ticker, "nb": nb_actions, "prix": prix_entree})

        return self.sauvegarder_portfolio(self.portfolio)

    def vendre(self, ticker: str, prix_sortie: float, raison: str) -> bool:
        """Ferme une position au portefeuille."""
        position = next((p for p in self.portfolio['positions'] if p['ticker'] == ticker), None)

        if not position:
            print(f"   ❌ Position {ticker} introuvable")
            return False

        montant_realise = position['nb_actions'] * prix_sortie
        pl = montant_realise - position['montant_investi']

        # Enregistre le trade
        trade = {
            "type": "vente",
            "ticker": ticker,
            "nom": position['nom'],
            "nb_actions": position['nb_actions'],
            "prix": prix_sortie,
            "montant": montant_realise,
            "pl_realise": pl,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "raison": raison
        }
        self.portfolio['trades_historique'].append(trade)

        # Retire la position
        self.portfolio['positions'].remove(position)
        self.portfolio['cash_disponible'] += montant_realise
        self.portfolio['meta']['nb_trades'] += 1

        print(f"   ✅ Vente: {position['nb_actions']} x {ticker} @ {prix_sortie:.2f}€ | P&L: {pl:+.2f}€")
        _log("vente_position", {"ticker": ticker, "pl": pl})

        return self.sauvegarder_portfolio(self.portfolio)

    # ─── MISE À JOUR DES PRIX ──────────────────────────────────────────────────────

    def mettre_a_jour_prix(self) -> bool:
        """Récupère les prix actuels via yfinance et met à jour le P&L."""
        if not yf:
            print("   ⚠️  yfinance non disponible, skip mise à jour prix")
            return False

        if not self.portfolio['positions']:
            print("   ℹ️  Aucune position, skip mise à jour")
            return True

        print("  📈 Mise à jour des prix...")
        try:
            tickers_list = [p['ticker'] for p in self.portfolio['positions']]
            data = yf.download(tickers_list, period='1d', progress=False)

            capital_total = self.portfolio['cash_disponible']

            for position in self.portfolio['positions']:
                ticker = position['ticker']
                try:
                    if len(tickers_list) == 1:
                        prix_actuel = data['Close'].iloc[-1]
                    else:
                        prix_actuel = data['Close'][ticker].iloc[-1]

                    position['prix_actuel'] = float(prix_actuel)
                    valeur_position = position['nb_actions'] * prix_actuel
                    position['pl_euros'] = valeur_position - position['montant_investi']
                    position['pl_pct'] = (position['pl_euros'] / position['montant_investi'] * 100) if position['montant_investi'] > 0 else 0

                    capital_total += valeur_position
                    print(f"    {ticker}: {prix_actuel:.2f}€ | P&L: {position['pl_euros']:+.2f}€ ({position['pl_pct']:+.1f}%)")
                except Exception as e:
                    print(f"    ⚠️  Erreur {ticker}: {e}")

            # Recalcule métriques globales
            self.portfolio['meta']['capital_actuel'] = capital_total
            self.portfolio['meta']['derniere_maj'] = datetime.now().strftime("%Y-%m-%d")

            capital_initial = self.portfolio['meta']['capital_initial']
            perf_totale = ((capital_total - capital_initial) / capital_initial * 100) if capital_initial > 0 else 0
            self.portfolio['meta']['performance_totale_pct'] = perf_totale

            print(f"    📊 Capital total: {capital_total:.2f}€ | Performance: {perf_totale:+.2f}%")
            return self.sauvegarder_portfolio(self.portfolio)

        except Exception as e:
            print(f"    ❌ Erreur mise à jour: {e}")
            return False

    # ─── GÉNÉRATION HTML ───────────────────────────────────────────────────────────

    def generer_rapport_html(self) -> str:
        """Génère le contenu HTML du rapport portfolio."""
        portfolio = self.portfolio
        capital = portfolio['meta']['capital_actuel']
        objectif = portfolio['meta']['objectif']
        progression = min(100, (capital / objectif) * 100)

        # Positions HTML
        positions_html = ""
        if portfolio['positions']:
            for pos in portfolio['positions']:
                pl_classe = "pos" if pos['pl_euros'] >= 0 else "neg"
                var_classe = "up" if pos['pl_pct'] >= 0 else "down"
                positions_html += f"""
                <tr>
                    <td class="pos-nom">{pos['nom']}</td>
                    <td class="pos-ticker">{pos['ticker']}</td>
                    <td class="pos-qty">{pos['nb_actions']:.4f}</td>
                    <td class="pos-entry">€{pos['prix_entree']:.2f}</td>
                    <td class="pos-current">€{pos['prix_actuel']:.2f}</td>
                    <td class="pos-var {var_classe}">{pos['pl_pct']:+.2f}%</td>
                    <td class="pos-pl {pl_classe}">€{pos['pl_euros']:+.2f}</td>
                    <td class="pos-raison">{pos['raison_geopolitique']}</td>
                </tr>
                """
        else:
            positions_html = '<tr><td colspan="8" style="text-align:center;color:var(--muted);">Aucune position — Portefeuille 100% cash</td></tr>'

        # Trades HTML
        trades_html = ""
        for trade in reversed(portfolio['trades_historique'][-10:]):  # Derniers 10 trades
            trade_type = "achat" if trade['type'] == "achat" else "vente"
            trades_html += f"""
            <div class="trade-item {trade_type}">
                <div class="trade-type">{trade_type.upper()}</div>
                <div class="trade-ticker">{trade['ticker']}</div>
                <div class="trade-qty">{trade['nb_actions']:.4f}</div>
                <div class="trade-prix">€{trade['prix']:.2f}</div>
                <div class="trade-date">{trade['date']}</div>
            </div>
            """

        # Thèses HTML
        theses_html = ""
        for these in portfolio['theses_investissement']['theses_actives']:
            badge_color = "active" if these['statut'] == 'active' else 'surveillance'
            theses_html += f"""
            <div class="these-card">
                <div class="these-header">
                    <h3>{these['titre']}</h3>
                    <span class="these-badge {badge_color}">{these['statut'].upper()}</span>
                </div>
                <p class="these-desc">{these['description']}</p>
                <div class="these-ticker">Actif ciblé: <strong>{these['action_ciblee']}</strong></div>
            </div>
            """

        html = f"""
        <!-- Portfolio Data (embedded JS const) -->
        <script>
        const PORTFOLIO_DATA = {json.dumps(portfolio)};
        </script>

        <!-- Portfolio Summary Cards -->
        <div class="portfolio-summary">
            <div class="summary-card">
                <div class="summary-label">Valeur du portefeuille</div>
                <div class="summary-value">€{capital:,.2f}</div>
                <div class="summary-progress">€10,000 <span style="font-size:11px;color:var(--muted);">→</span> €100,000</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Cash disponible</div>
                <div class="summary-value">€{portfolio['cash_disponible']:,.2f}</div>
                <div class="summary-progress">{(portfolio['cash_disponible']/capital*100):.1f}% du portefeuille</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Performance globale</div>
                <div class="summary-value {('pos' if portfolio['meta']['performance_totale_pct'] >= 0 else 'neg')}">
                    {portfolio['meta']['performance_totale_pct']:+.2f}%
                </div>
                <div class="summary-progress">€{(capital - portfolio['meta']['capital_initial']):+,.2f}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Positions actives</div>
                <div class="summary-value">{len(portfolio['positions'])}</div>
                <div class="summary-progress">{portfolio['meta']['nb_trades']} trades total</div>
            </div>
        </div>

        <!-- Progress Bar -->
        <div class="progress-wrapper">
            <div class="progress-bar">
                <div class="progress-fill" style="width:{progression:.1f}%"></div>
                <div class="progress-marker" style="left:10%;">€10K</div>
                <div class="progress-marker" style="left:50%;">€55K</div>
                <div class="progress-marker" style="left:100%;">€100K</div>
            </div>
            <div class="progress-label">{progression:.1f}% vers l'objectif</div>
        </div>

        <!-- Positions Table -->
        <div class="positions-section">
            <h3>Positions actives</h3>
            <div class="positions-table">
                <table>
                    <thead>
                        <tr>
                            <th>Actif</th>
                            <th>Ticker</th>
                            <th>Nb actions</th>
                            <th>Prix entrée</th>
                            <th>Prix actuel</th>
                            <th>Variation %</th>
                            <th>P&L €</th>
                            <th>Raison géopolitique</th>
                        </tr>
                    </thead>
                    <tbody>
                        {positions_html}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Investment Theses -->
        <div class="theses-section">
            <h3>Thèses d'investissement actives</h3>
            <div class="theses-grid">
                {theses_html}
            </div>
        </div>

        <!-- Trade History -->
        <div class="trades-section">
            <h3>Historique des trades</h3>
            <div class="trades-timeline">
                {trades_html}
            </div>
        </div>
        """

        return html

    # ─── DÉCISIONS IA ──────────────────────────────────────────────────────────────

    def prendre_decision_investissement(self, donnees_veille: dict) -> dict:
        """
        Demande à Claude de prendre une décision d'investissement.
        Retourne: {"action": "acheter"|"vendre"|"conserver"|"surveiller", "ticker": ..., "montant_eur": ..., ...}
        """
        if not anthropic or not ANTHROPIC_API_KEY:
            print("   ⚠️  Anthropic API non disponible")
            return {"action": "surveiller"}

        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

            # Prépare le contexte
            contexte = f"""
Données de marché:
{json.dumps(donnees_veille, indent=2)}

Portefeuille actuel:
- Capital: €{self.portfolio['meta']['capital_actuel']:.2f}
- Objectif: €{self.portfolio['meta']['objectif']:.2f}
- Cash disponible: €{self.portfolio['cash_disponible']:.2f}
- Positions: {len(self.portfolio['positions'])}
- Thèses actives:
{json.dumps(self.portfolio['theses_investissement']['theses_actives'], indent=2)}

Historique des 3 derniers trades:
{json.dumps(self.portfolio['trades_historique'][-3:] if self.portfolio['trades_historique'] else [], indent=2)}
"""

            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                system="""Tu es un gestionnaire de portefeuille IA pour AlphaBot Weekly. Tu gères un portefeuille fictif éducatif de 10 000€ avec objectif 100K.
Chaque décision doit être justifiée par un angle géopolitique ou macro-économique concret (pas juste technique).
Tu es agressif mais pas téméraire. Positions max 30% du capital. Stop-loss mental à -15% par position.
Tu raisonnes en JSON uniquement.

Réponds TOUJOURS en JSON valide avec ce format:
{
  "action": "acheter" | "vendre" | "conserver" | "surveiller",
  "ticker": "TICKER",
  "nom": "Nom complet",
  "montant_eur": 1000,
  "raison_courte": "Une ligne",
  "raison_complete": "Explications géopolitiques sur 3-5 lignes",
  "these_id": "these_btc_dxy" ou null
}""",
                messages=[
                    {"role": "user", "content": f"Analyse ces données et recommande une action:\n\n{contexte}"}
                ]
            )

            reponse = message.content[0].text
            decision = json.loads(reponse)

            print(f"   🤖 Décision IA: {decision['action']} {decision['ticker']}")
            _log("decision_ia", decision)

            return decision

        except Exception as e:
            print(f"   ❌ Erreur décision IA: {e}")
            return {"action": "surveiller"}

    # ─── ORCHESTRATION ────────────────────────────────────────────────────────────

    def run(self):
        """Cycle complet: mise à jour prix, génération rapport."""
        print("\n🔄 Démarrage cycle complet Agent Investissement")

        # 1. Mise à jour des prix
        self.mettre_a_jour_prix()

        # 2. Génération du rapport HTML
        rapport_html = self.generer_rapport_html()

        # 3. Sauvegarde en fichier HTML (pour embedding dans investissement.html)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        print("   ✅ Cycle complet terminé")

        return rapport_html


# ─── MAIN ──────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    agent = AgentInvestissement()
    rapport = agent.run()
    print(f"\n📊 Rapport généré ({len(rapport)} caractères)")
