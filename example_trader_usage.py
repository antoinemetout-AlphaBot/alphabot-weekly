#!/usr/bin/env python3
"""
ExempleS D'UTILISATION — Robot Trader AlphaBot

Ce fichier montre comment utiliser le robot trader dans différents contextes.
"""

import sys
import os
from datetime import datetime
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.agent_trader import RobotTrader

# ═══════════════════════════════════════════════════════════════════════════
# EXEMPLE 1: UN CYCLE COMPLET SIMPLE
# ═══════════════════════════════════════════════════════════════════════════

def exemple_1_cycle_simple():
    """Exécute un cycle complet du robot."""
    print("\n" + "="*80)
    print("EXEMPLE 1: Un Cycle Complet Simple")
    print("="*80)

    robot = RobotTrader()
    resume = robot.run_cycle()

    print(f"\n✅ Cycle complété!")
    print(json.dumps(resume, indent=2, default=str))


# ═══════════════════════════════════════════════════════════════════════════
# EXEMPLE 2: ACCÈS DIRECT AU PORTEFEUILLE
# ═══════════════════════════════════════════════════════════════════════════

def exemple_2_analyser_portfolio():
    """Accède directement au portefeuille et affiche les stats."""
    print("\n" + "="*80)
    print("EXEMPLE 2: Analyser le Portefeuille")
    print("="*80)

    robot = RobotTrader()
    p = robot.portfolio

    print(f"\n📊 PORTEFEUILLE")
    print(f"   Capital initial: €{p['meta']['capital_initial']:,.2f}")
    print(f"   Capital actuel:  €{p['meta']['capital_actuel']:,.2f}")
    print(f"   Performance:     {p['meta']['performance_totale_pct']:+.2f}%")
    print(f"   Objectif:        €{p['meta']['objectif']:,.2f}")

    print(f"\n📈 STATISTIQUES")
    print(f"   Trades total:    {p['meta']['nb_trades']}")
    print(f"   Trades gagnants: {p['meta']['nb_trades_gagnants']} ({p['meta']['win_rate']:.1f}%)")
    print(f"   Trades perdants: {p['meta']['nb_trades_perdants']}")
    print(f"   Meilleur trade:  {p['meta']['meilleur_trade_pct']:+.2f}%")
    print(f"   Pire trade:      {p['meta']['pire_trade_pct']:+.2f}%")

    print(f"\n💰 POSITIONS OUVERTES ({len(p['positions'])})")
    if p['positions']:
        for pos in p['positions']:
            emoji = "💚" if pos['pl_pct'] >= 0 else "❤️"
            print(f"   {emoji} {pos['ticker']:8} | {pos['nb_actions']:6.4f} actions | "
                  f"€{pos['prix_entree']:8.2f} → €{pos['prix_actuel']:8.2f} | "
                  f"P&L: {pos['pl_pct']:+6.2f}%")
    else:
        print("   Aucune position ouverte")

    print(f"\n💵 CASH DISPONIBLE: €{p['cash_disponible']:,.2f}")


# ═══════════════════════════════════════════════════════════════════════════
# EXEMPLE 3: VISUALISER LES DERNIERS TRADES
# ═══════════════════════════════════════════════════════════════════════════

def exemple_3_historique_trades():
    """Affiche les 10 derniers trades effectués."""
    print("\n" + "="*80)
    print("EXEMPLE 3: Historique des Trades")
    print("="*80)

    robot = RobotTrader()
    trades = robot.portfolio['trades_historique'][-10:]

    print(f"\nDerniers {len(trades)} trades:")
    print(f"{'Date':<20} {'Type':<8} {'Ticker':<8} {'Montant':>12} {'P&L':>12} {'Stratégie':<15}")
    print("-" * 85)

    for trade in trades:
        date = trade['date'][:10]  # Format court
        trade_type = "ACHAT" if trade['type'] == 'achat' else "VENTE"
        pl = trade.get('pl_realise', 0)
        pl_str = f"€{pl:+.2f}" if pl else "—"
        strat = trade.get('strategie', 'N/A')

        print(f"{date:<20} {trade_type:<8} {trade['ticker']:<8} "
              f"€{trade['montant']:>11.2f} {pl_str:>12} {strat:<15}")


# ═══════════════════════════════════════════════════════════════════════════
# EXEMPLE 4: ANALYSER LES SIGNAUX EN TEMPS RÉEL
# ═══════════════════════════════════════════════════════════════════════════

def exemple_4_analyser_signaux():
    """Récupère et affiche les signaux techniques actuels."""
    print("\n" + "="*80)
    print("EXEMPLE 4: Signaux Techniques Actuels")
    print("="*80)

    robot = RobotTrader()

    # Récupère les données
    print("\n📊 Récupération des données...")
    robot.recuperer_prix_temps_reel()

    # Génère les signaux
    print("🎯 Génération des signaux...")
    signaux = robot.generer_signaux()

    if not signaux:
        print("\n   Aucun signal généré actuellement")
        return

    print(f"\n✅ {len(signaux)} signaux générés:")
    print(f"{'Ticker':<10} {'Signal':<8} {'Force':<7} {'Raison':<50}")
    print("-" * 75)

    for sig in sorted(signaux, key=lambda s: s['force'], reverse=True):
        raison = sig['raison'][:47] + "..." if len(sig['raison']) > 50 else sig['raison']
        print(f"{sig['ticker']:<10} {sig['signal']:<8} {sig['force']:<7} {raison:<50}")


# ═══════════════════════════════════════════════════════════════════════════
# EXEMPLE 5: EXÉCUTER MANUELLEMENT UN TRADE
# ═══════════════════════════════════════════════════════════════════════════

def exemple_5_trade_manuel():
    """Montre comment exécuter manuellement un trade (pour tests)."""
    print("\n" + "="*80)
    print("EXEMPLE 5: Exécution Manuel d'un Trade")
    print("="*80)

    robot = RobotTrader()

    # Vérifie que nous avons du cash
    if robot.portfolio['cash_disponible'] < 200:
        print("   ❌ Pas assez de cash disponible (< 200€)")
        return

    # Récupère les prix
    robot.recuperer_prix_temps_reel()
    if not robot.market_data:
        print("   ❌ Impossible de récupérer les prix")
        return

    # Sélectionne AAPL comme exemple
    ticker = 'AAPL'
    if ticker not in robot.market_data:
        print(f"   ❌ {ticker} non disponible")
        return

    data = robot.market_data[ticker]
    prix = data['prix']

    print(f"\nAchat manuel de {ticker} @ €{prix:.2f}")
    print(f"Cash disponible avant: €{robot.portfolio['cash_disponible']:.2f}")

    # Exécute l'achat
    trade = robot._acheter(
        ticker=ticker,
        nom=data['nom'],
        prix=prix,
        montant_eur=500,  # Investit 500€
        raison_technique="Achat manuel pour test",
        raison_geopolitique="Exemple d'utilisation",
        strategie="manuel"
    )

    if trade:
        print(f"✅ Trade exécuté: {json.dumps(trade, indent=2, default=str)}")
        print(f"Cash disponible après: €{robot.portfolio['cash_disponible']:.2f}")
        robot._sauvegarder_portfolio()
    else:
        print("❌ Erreur lors de l'exécution du trade")


# ═══════════════════════════════════════════════════════════════════════════
# EXEMPLE 6: EXPORTER POUR DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

def exemple_6_export_dashboard():
    """Exporte les données pour le dashboard HTML."""
    print("\n" + "="*80)
    print("EXEMPLE 6: Export pour Dashboard")
    print("="*80)

    robot = RobotTrader()

    # Récupère les données
    robot.recuperer_prix_temps_reel()
    robot.mettre_a_jour_prix()
    robot.generer_signaux()

    # Exporte
    print("\n📤 Export des données...")
    robot.exporter_donnees_page()

    # Vérifie
    if os.path.exists("data/portfolio_live.json"):
        with open("data/portfolio_live.json", 'r') as f:
            live = json.load(f)
        print(f"\n✅ Données exportées vers data/portfolio_live.json")
        print(f"   Capital: €{live['meta']['capital_actuel']:,.2f}")
        print(f"   Positions: {len(live['positions'])}")
        print(f"   Signaux: {len(live['signaux_actifs'])}")
        print(f"   Equity curve: {len(live['equity_curve'])} points")


# ═══════════════════════════════════════════════════════════════════════════
# EXEMPLE 7: INTÉGRATION AVEC SCHEDULER
# ═══════════════════════════════════════════════════════════════════════════

def exemple_7_scheduler():
    """Montre comment intégrer avec un scheduler (schedule library)."""
    print("\n" + "="*80)
    print("EXEMPLE 7: Intégration Scheduler")
    print("="*80)

    # Code pour utiliser avec schedule library:
    code = '''
import schedule
import time
from agents.agent_trader import RobotTrader

# Initialiser le robot
robot = RobotTrader()

def run_trading_cycle():
    """Exécute un cycle de trading."""
    try:
        resume = robot.run_cycle()
        print(f"✅ Cycle exécuté: {resume['trades_executed']} trades")
    except Exception as e:
        print(f"❌ Erreur: {e}")

# Programmer les trades toutes les heures (9h-18h)
for hour in range(9, 18):
    schedule.every().day.at(f"{hour:02d}:00").do(run_trading_cycle)

# Exécuter
while True:
    schedule.run_pending()
    time.sleep(60)
'''

    print("\nCode à intégrer dans orchestrateur.py:")
    print(code)


# ═══════════════════════════════════════════════════════════════════════════
# EXEMPLE 8: COMPARAISON AVEC BENCHMARKS
# ═══════════════════════════════════════════════════════════════════════════

def exemple_8_benchmarks():
    """Compare la performance du robot avec des benchmarks."""
    print("\n" + "="*80)
    print("EXEMPLE 8: Performance vs Benchmarks")
    print("="*80)

    robot = RobotTrader()
    p = robot.portfolio

    robot_return = p['meta']['performance_totale_pct']

    # Benchmarks (à remplir avec données réelles)
    benchmarks = {
        "S&P 500 (SPY)": 8.5,      # Returns YTD fictifs
        "CAC 40": 5.2,
        "MSCI World": 6.8,
        "Robot Trader": robot_return,
    }

    print("\n📊 Performance YTD (fictif)")
    print(f"{'Index':<25} {'Return':<12} {'Status':<20}")
    print("-" * 57)

    robot_perf = benchmarks["Robot Trader"]
    for name, ret in sorted(benchmarks.items(), key=lambda x: x[1], reverse=True):
        status = "✅ Outperformance" if ret > 5 else "⚠️  Underperformance"
        print(f"{name:<25} {ret:>10.2f}% {status:<20}")

    if robot_perf > max([v for k, v in benchmarks.items() if k != "Robot Trader"]):
        print(f"\n🏆 Robot Trader outperform tous les benchmarks!")
    else:
        print(f"\n📈 Robot Trader en développement, patience...")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN — LANCER LES EXEMPLES
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Exemples d'utilisation du Robot Trader")
    parser.add_argument("--exemple", type=int, default=1,
                        choices=range(1, 9),
                        help="Numéro d'exemple à exécuter (1-8)")
    parser.add_argument("--tous", action="store_true",
                        help="Exécuter tous les exemples")

    args = parser.parse_args()

    print("\n" + "="*80)
    print("🤖 ALPHABOT ROBOT TRADER — EXEMPLES D'UTILISATION")
    print("="*80)

    exemples = {
        1: ("Cycle Complet Simple", exemple_1_cycle_simple),
        2: ("Analyser le Portefeuille", exemple_2_analyser_portfolio),
        3: ("Historique des Trades", exemple_3_historique_trades),
        4: ("Signaux Techniques", exemple_4_analyser_signaux),
        5: ("Trade Manuel", exemple_5_trade_manuel),
        6: ("Export Dashboard", exemple_6_export_dashboard),
        7: ("Scheduler Integration", exemple_7_scheduler),
        8: ("Benchmarks", exemple_8_benchmarks),
    }

    if args.tous:
        for num, (name, func) in exemples.items():
            try:
                func()
            except Exception as e:
                print(f"\n❌ Erreur exemple {num}: {e}")
                import traceback
                traceback.print_exc()
    else:
        num = args.exemple
        name, func = exemples[num]
        print(f"\nLancement: Exemple {num} — {name}\n")
        try:
            func()
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("✅ Exemples terminés\n")
