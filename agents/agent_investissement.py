"""
AlphaBot — Agent Investissement 💰
Rôle : Gérer un portefeuille fictif de 10 000€ avec objectif 100K en PAPER TRADING réel.
Collecte prix réels + implémente 3 stratégies simples (momentum, mean-reversion, géopolitique).
"""

import json
import os
import sys
from datetime import datetime, timedelta
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
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, OUTPUT_DIR, WATCHLIST_STOCKS, COMMODITIES
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
            _log("Agent Investissement", "portfolio_saved", "Portfolio sauvegardé", {"timestamp": datetime.now().isoformat(), "capital": portfolio['meta']['capital_actuel']})
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
        _log("Agent Investissement", "achat", f"Achat {nb_actions}x {ticker} @ {prix_entree:.2f}€", {"ticker": ticker, "nb": nb_actions, "prix": prix_entree})

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
        _log("Agent Investissement", "vente", f"Vente {position['nb_actions']}x {ticker} @ {prix_sortie:.2f}€ | P&L: {pl:+.2f}€", {"ticker": ticker, "pl": pl})

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
                    # Gère le cas où les données ne sont pas disponibles
                    if data is not None and isinstance(data, object) and len(data) > 0:
                        if len(tickers_list) == 1:
                            # Single ticker retourne une Series
                            if isinstance(data, object) and 'Close' in data.columns:
                                prix_actuel = float(data['Close'].iloc[-1]) if len(data) > 0 else position['prix_actuel']
                            else:
                                prix_actuel = position['prix_actuel']
                        else:
                            # Multiple tickers retournent un DataFrame
                            if ticker in data['Close'].columns:
                                prix_actuel = float(data['Close'][ticker].iloc[-1]) if len(data) > 0 else position['prix_actuel']
                            else:
                                prix_actuel = position['prix_actuel']
                    else:
                        prix_actuel = position['prix_actuel']

                    position['prix_actuel'] = prix_actuel
                    valeur_position = position['nb_actions'] * prix_actuel
                    position['pl_euros'] = valeur_position - position['montant_investi']
                    position['pl_pct'] = (position['pl_euros'] / position['montant_investi'] * 100) if position['montant_investi'] > 0 else 0

                    capital_total += valeur_position
                    print(f"    {ticker}: {prix_actuel:.2f}€ | P&L: {position['pl_euros']:+.2f}€ ({position['pl_pct']:+.1f}%)")
                except Exception as e:
                    print(f"    ⚠️  Erreur {ticker}: {str(e)[:60]}")

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
            _log("Agent Investissement", "decision_ia", f"Décision: {decision['action']} {decision['ticker']}", decision)

            return decision

        except Exception as e:
            print(f"   ❌ Erreur décision IA: {e}")
            return {"action": "surveiller"}

    # ─── PAPER TRADING (NOUVELLES FONCTIONNALITÉS) ───────────────────────────────────

    def collecter_prix_actuels(self) -> dict:
        """
        Collecte les prix actuels pour les actifs de la watchlist via yfinance.
        Fallback: utilise des prix simulés si yfinance échoue (pour démo/test).
        Retourne: {ticker: {"prix": float, "prix_hier": float, "variation_pct": float, "nom": str}}
        """
        prix_data = {}
        tous_les_tickers = {}
        import random

        # Combine stocks et commodities
        for nom, ticker in WATCHLIST_STOCKS.items():
            tous_les_tickers[ticker] = nom
        for nom, ticker in COMMODITIES.items():
            tous_les_tickers[ticker] = nom

        print(f"   📊 Collecte de {len(tous_les_tickers)} prix actuels...")

        # Tente avec yfinance d'abord
        if yf:
            for ticker, nom in tous_les_tickers.items():
                try:
                    data = yf.download(ticker, period='5d', progress=False)
                    # Vérifier que data n'est pas None et a au moins 2 rows
                    if data is not None and isinstance(data, object) and len(data) >= 2:
                        try:
                            prix_actuel = float(data['Close'].iloc[-1])
                            prix_hier = float(data['Close'].iloc[-2])
                            variation = ((prix_actuel - prix_hier) / prix_hier * 100) if prix_hier > 0 else 0

                            prix_data[ticker] = {
                                "nom": nom,
                                "prix": prix_actuel,
                                "prix_hier": prix_hier,
                                "variation_pct": variation
                            }
                            if abs(variation) > 0.5:
                                print(f"    {ticker}: {prix_actuel:.2f} ({variation:+.2f}%)")
                        except (KeyError, TypeError, ValueError):
                            raise Exception("Impossible d'extraire Close from data")
                    else:
                        raise Exception("Données insuffisantes (None ou <2 rows)")
                except Exception as e:
                    # Fallback: prix simulés pour démo
                    prix_hier = 100.0
                    variation = random.uniform(-3, 3)
                    prix_actuel = prix_hier * (1 + variation / 100)
                    prix_data[ticker] = {
                        "nom": nom,
                        "prix": prix_actuel,
                        "prix_hier": prix_hier,
                        "variation_pct": variation
                    }
        else:
            # Fallback complet si yfinance non disponible
            print("   ℹ️  Mode démo: génération de prix simulés...")
            for ticker, nom in tous_les_tickers.items():
                prix_hier = 100.0
                variation = random.uniform(-3, 3)
                prix_actuel = prix_hier * (1 + variation / 100)
                prix_data[ticker] = {
                    "nom": nom,
                    "prix": prix_actuel,
                    "prix_hier": prix_hier,
                    "variation_pct": variation
                }

        return prix_data

    def evaluer_signaux_trading(self, prix_data: dict) -> list:
        """
        Évalue les 3 stratégies et retourne une liste de signaux.
        Format: [{"ticker": "NVDA", "strategie": "momentum", "score": 0.8, "raison": "..."}]
        """
        signaux = []

        for ticker, data in prix_data.items():
            variation = data['variation_pct']
            prix = data['prix']
            nom = data['nom']

            # Stratégie 1: MOMENTUM — Si hausse >1% aujourd'hui, achat
            if variation > 1.0:
                signaux.append({
                    "ticker": ticker,
                    "nom": nom,
                    "strategie": "momentum",
                    "prix": prix,
                    "score": min(variation / 5.0, 1.0),  # Normalise 0-1
                    "raison": f"Hausse forte de +{variation:.2f}% — momentum haussier"
                })

            # Stratégie 2: MEAN REVERSION — Si baisse >2% aujourd'hui, achat (rebond)
            if variation < -2.0:
                signaux.append({
                    "ticker": ticker,
                    "nom": nom,
                    "strategie": "mean_reversion",
                    "prix": prix,
                    "score": min(abs(variation) / 5.0, 1.0),
                    "raison": f"Baisse forte de {variation:.2f}% — retour attendu"
                })

            # Stratégie 3: GÉOPOLITIQUE — Si or monte >0.5%, achat d'actifs défensifs
            if ticker == "GC=F" and variation > 0.5:
                signaux.append({
                    "ticker": "LMT",  # Lockheed Martin (défense)
                    "nom": "Lockheed Martin",
                    "strategie": "geopolitique",
                    "prix": prix_data.get("LMT", {}).get("prix", 0),
                    "score": 0.6,
                    "raison": "Or monte → tensions géopolitiques → achat défense (LMT)"
                })

        return signaux

    def calculer_taille_position(self, capital_available: float) -> float:
        """Retourne la taille max d'une position (5-10% du capital disponible)."""
        return capital_available * 0.075  # 7.5% = moyenne entre 5-10%

    def calculer_stop_loss_take_profit(self, prix_entree: float) -> tuple:
        """Retourne (stop_loss, take_profit) basés sur le prix d'entrée."""
        stop_loss = prix_entree * 0.97  # -3%
        take_profit = prix_entree * 1.05  # +5%
        return stop_loss, take_profit

    def evaluer_clotures_positions(self, prix_data: dict) -> list:
        """
        Évalue les positions existantes pour déterminer les clôtures.
        Retourne: [{"ticker": "NVDA", "action": "cloturer", "raison": "stop-loss atteint"}]
        """
        actions = []

        for position in self.portfolio['positions']:
            ticker = position['ticker']
            if ticker not in prix_data:
                continue

            prix_actuel = prix_data[ticker]['prix']
            stop_loss = position.get('stop_loss', position['prix_entree'] * 0.97)
            take_profit = position.get('take_profit', position['prix_entree'] * 1.05)

            # Vérifier stop-loss
            if prix_actuel <= stop_loss:
                actions.append({
                    "ticker": ticker,
                    "action": "cloturer",
                    "raison": f"Stop-loss atteint ({prix_actuel:.2f} <= {stop_loss:.2f})",
                    "prix": prix_actuel
                })
            # Vérifier take-profit
            elif prix_actuel >= take_profit:
                actions.append({
                    "ticker": ticker,
                    "action": "cloturer",
                    "raison": f"Take-profit atteint ({prix_actuel:.2f} >= {take_profit:.2f})",
                    "prix": prix_actuel
                })

        return actions

    def executer_trades(self, signaux: list, prix_data: dict, actions_cloture: list) -> dict:
        """
        Exécute les trades basés sur les signaux et les clôtures.
        Retourne un résumé: {"achats": N, "ventes": N, "details": [...]}
        """
        resume = {"achats": 0, "ventes": 0, "details": []}

        # 1. CLÔTURE des positions existantes (priorité)
        for action in actions_cloture:
            ticker = action['ticker']
            raison = action['raison']
            prix = action['prix']

            if self.vendre(ticker, prix, raison):
                resume["ventes"] += 1
                resume["details"].append(f"✅ Vente {ticker} @ {prix:.2f}€ — {raison}")

        # 2. ACHAT sur signaux (si capital disponible)
        for signal in signaux:
            ticker = signal['ticker']
            nom = signal['nom']
            prix = signal['prix']
            strategie = signal['strategie']
            raison = signal['raison']

            # Vérifier qu'on n'a pas déjà cette position
            if any(p['ticker'] == ticker for p in self.portfolio['positions']):
                continue

            # Vérifier capital disponible
            montant_max = self.calculer_taille_position(self.portfolio['cash_disponible'])
            if montant_max <= 0 or prix <= 0:
                continue

            nb_actions = int(montant_max / prix)
            if nb_actions <= 0:
                continue

            # Acheter
            if self.acheter(ticker, nom, nb_actions, prix, raison):
                # Ajouter stop-loss et take-profit à la position
                position = self.portfolio['positions'][-1]
                stop_loss, take_profit = self.calculer_stop_loss_take_profit(prix)
                position['stop_loss'] = stop_loss
                position['take_profit'] = take_profit
                position['strategie'] = strategie
                self.sauvegarder_portfolio(self.portfolio)

                resume["achats"] += 1
                resume["details"].append(f"✅ Achat {nb_actions}x {ticker} @ {prix:.2f}€ — {strategie}")

        return resume

    # ─── ORCHESTRATION ────────────────────────────────────────────────────────

    def run(self):
        """
        Cycle complet PAPER TRADING:
        1. Collecter les prix réels
        2. Évaluer les signaux (3 stratégies)
        3. Évaluer les positions pour clôtures (stop-loss/take-profit)
        4. Exécuter les trades
        5. Mettre à jour les prix
        6. Générer le rapport
        """
        print("\n🔄 Démarrage cycle PAPER TRADING Agent Investissement")
        print(f"   Timestamp: {self.timestamp}")
        print(f"   Capital: {self.portfolio['cash_disponible']:.2f}€ | Positions: {len(self.portfolio['positions'])}")

        try:
            # 1. Collecter les prix
            print("\n   📊 Étape 1: Collecte des prix...")
            prix_data = self.collecter_prix_actuels()
            if not prix_data:
                print("   ⚠️  Aucun prix collecté, abandon")
                return self.generer_rapport_html()

            # 2. Évaluer les signaux de trading
            print("\n   🎯 Étape 2: Évaluation des signaux...")
            signaux = self.evaluer_signaux_trading(prix_data)
            print(f"      {len(signaux)} signal(s) détecté(s)")
            for sig in signaux:
                print(f"      - {sig['ticker']}: {sig['strategie']} ({sig['score']:.0%})")

            # 3. Évaluer les clôtures (stop-loss / take-profit)
            print("\n   🔴 Étape 3: Évaluation des clôtures...")
            actions_cloture = self.evaluer_clotures_positions(prix_data)
            print(f"      {len(actions_cloture)} position(s) à clôturer")

            # 4. Exécuter les trades
            print("\n   ⚡ Étape 4: Exécution des trades...")
            resume_trades = self.executer_trades(signaux, prix_data, actions_cloture)
            print(f"      Achats: {resume_trades['achats']} | Ventes: {resume_trades['ventes']}")
            for detail in resume_trades['details']:
                print(f"      {detail}")

            # 5. Mise à jour des prix (pour rapport)
            print("\n   💹 Étape 5: Mise à jour des prix...")
            self.mettre_a_jour_prix()

            # 6. Génération du rapport HTML
            print("\n   📄 Étape 6: Génération du rapport...")
            rapport_html = self.generer_rapport_html()

            print(f"\n   ✅ Cycle PAPER TRADING terminé")
            print(f"   Capital actuel: {self.portfolio['meta']['capital_actuel']:.2f}€")
            print(f"   Performance: {self.portfolio['meta']['performance_totale_pct']:+.2f}%")

            return rapport_html

        except Exception as e:
            print(f"\n   ❌ Erreur lors du cycle: {e}")
            import traceback
            traceback.print_exc()
            return self.generer_rapport_html()


# ─── MAIN ──────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    agent = AgentInvestissement()
    rapport = agent.run()
    print(f"\n📊 Rapport généré ({len(rapport)} caractères)")
