"""
AlphaBot — Orchestrateur Principal 🎯
Fait tourner l'entreprise IA complète : 5 agents, 0 intervention humaine.

╔══════════════════════════════════════════════════════════════╗
║                    COMMANDES DISPONIBLES                     ║
╠══════════════════════════════════════════════════════════════╣
║  python main.py                → Pipeline newsletter complet ║
║  python main.py --demo         → Démo sans clé API           ║
║  python main.py --veille       → Test Agent Veille seul      ║
║  python main.py --growth       → Stats & gestion abonnés     ║
║  python main.py --commercial   → Lancer campagne prospection ║
║  python main.py --relances     → Envoyer relances sponsors   ║
║  python main.py --analytics    → Dashboard métriques HTML    ║
║  python main.py --cfo          → Rapport financier + projec. ║
║  python main.py --adjoint      → Directeur Adjoint IA        ║
║  python main.py --booster      → Growth Booster (abonnés)    ║
║  python main.py --ceo-brief    → Brief stratégique CEO       ║
║  python main.py --full         → TOUS les agents d'un coup   ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys, json, argparse
from datetime import datetime

from agents.agent_veille      import AgentVeille
from agents.agent_analyste    import AgentAnalyste
from agents.agent_redacteur   import AgentRedacteur
from agents.agent_growth      import AgentGrowth
from agents.agent_commercial  import AgentCommercial
from agents.agent_analytics   import AgentAnalytics
from agents.agent_cfo         import AgentCFO
from agents.agent_adjoint        import AgentAdjoint
from agents.agent_growth_booster import AgentGrowthBooster
from agents.agent_ceo_brief     import AgentCEOBrief
from config import OUTPUT_DIR


# ─── BANNER ──────────────────────────────────────────────────────────────────

def _banner(titre: str, sous_titre: str = ""):
    print("\n")
    print("╔══════════════════════════════════════════════════╗")
    print(f"║  {titre:<48}║")
    if sous_titre:
        print(f"║  {sous_titre:<48}║")
    print("╚══════════════════════════════════════════════════╝")


# ─── PIPELINE NEWSLETTER ─────────────────────────────────────────────────────

def pipeline_newsletter() -> str:
    """
    Pipeline principal : Veille → Analyse → Rédaction → Newsletter HTML.
    Retourne le chemin du fichier HTML généré.
    """
    debut = datetime.now()
    _banner("🤖  AlphaBot  — Pipeline Newsletter",
            "Bourse + Crypto Newsletter 100% IA")
    print(f"   Démarrage : {debut.strftime('%d/%m/%Y à %H:%M:%S')}\n")

    # Étape 1 : Collecte
    print("▶ Étape 1/3 — Agent Veille : collecte des marchés...")
    rapport  = AgentVeille().collecter()

    # Étape 2 : Analyse
    print("▶ Étape 2/3 — Agent Analyste : analyse avec Claude...")
    analyses = AgentAnalyste().analyser(rapport)
    analyses["donnees_brutes"] = rapport   # injecte les données brutes pour les visuels

    # Étape 3 : Rédaction
    print("▶ Étape 3/3 — Agent Rédacteur : assemblage de la newsletter...")
    chemin = AgentRedacteur().rediger_newsletter(analyses)

    duree = (datetime.now() - debut).seconds
    _banner("✅  Pipeline terminé !")
    print(f"   Durée       : {duree}s")
    print(f"   Newsletter  : {chemin}")
    print(f"   Cryptos     : {len(rapport['crypto'])}")
    print(f"   Indices     : {len(rapport['bourse'].get('indices', {}))}")
    print(f"   Actions     : {len(rapport['bourse'].get('actions', {}))}")
    print(f"   Articles    : {len(rapport['news_crypto'])}\n")
    return chemin


# ─── PIPELINE COMPLET (TOUS LES AGENTS) ──────────────────────────────────────

def pipeline_full():
    """
    Pipeline complet de l'entreprise IA :
    Newsletter → Envoi abonnés → Prospection sponsors
    """
    debut = datetime.now()
    _banner("🚀  AlphaBot FULL — Entreprise IA Complète",
            "5 agents • 0 intervention humaine")

    # 1. Newsletter
    print("\n[1/3] 📰 Génération de la newsletter...")
    chemin = pipeline_newsletter()

    # 2. Growth : envoi
    print("\n[2/3] 📧 Agent Growth : envoi aux abonnés...")
    growth = AgentGrowth()
    stats  = growth.stats_abonnes()
    if stats["total_actifs"] > 0:
        result = growth.envoyer_newsletter(chemin)
        if result.get("success"):
            print(f"   ✅ Newsletter envoyée à {result['envoyes']} abonnés")
        else:
            print(f"   ⚠️  Envoi partiel : {result.get('erreur','')}")
    else:
        print("   ℹ️  Aucun abonné actif — envoi ignoré")
        print("   → Ajoutez des abonnés : growth.ajouter_abonne('email@ex.com', 'Prenom')")

    # 3. Commercial : campagne hebdomadaire
    print("\n[3/4] 💼 Agent Commercial : prospection sponsors...")
    commercial = AgentCommercial()
    campagne = commercial.lancer_campagne(nb_prospects=2)
    if campagne.get("success"):
        print(f"   ✅ {campagne['nb_emails']} emails de prospection générés")

    # 4. Analytics + CFO : rapport hebdomadaire
    print("\n[4/4] 📊 Agents Analytics & CFO : rapports de pilotage...")
    analytics = AgentAnalytics()
    dash_path = analytics.generer_dashboard()
    print(f"   ✅ Dashboard généré : {dash_path}")

    cfo = AgentCFO()
    print(cfo.rapport_mensuel(nb_abonnes=stats["total_actifs"]))

    # Rapport final
    duree = (datetime.now() - debut).seconds
    _banner("🎉  Entreprise AlphaBot — Cycle hebdomadaire terminé")
    print(f"   Durée totale       : {duree}s")
    print(f"   Newsletter         : générée et envoyée")
    print(f"   Abonnés actifs     : {stats['total_actifs']}")
    print(f"   Emails commerciaux : {campagne.get('nb_emails', 0)} rédigés")
    print(f"   Dashboard          : {dash_path}\n")


# ─── MODES STANDALONE ────────────────────────────────────────────────────────

def mode_veille_seul():
    """Teste uniquement l'Agent Veille."""
    print("\n🔍 Mode Veille seul\n")
    rapport = AgentVeille().collecter()
    print(json.dumps(rapport, indent=2, ensure_ascii=False))


def mode_growth():
    """Affiche les stats de la liste et du pipeline Growth."""
    print("\n📈 Agent Growth — Tableau de bord\n")
    growth = AgentGrowth()
    print(growth.rapport_performance())

    # Exemples d'abonnés si liste vide
    stats = growth.stats_abonnes()
    if stats["total_actifs"] == 0:
        print("━━━ Aucun abonné — ajout d'exemples de démonstration ━━━")
        growth.ajouter_abonne("alice@example.com",   "Alice",   "site_web")
        growth.ajouter_abonne("bob@example.com",     "Bob",     "linkedin")
        growth.ajouter_abonne("charlie@example.com", "Charlie", "bouche_a_oreille")
        print(growth.rapport_performance())


def mode_commercial():
    """Lance une campagne de prospection commerciale."""
    print("\n💼 Agent Commercial — Campagne de prospection\n")
    commercial = AgentCommercial()
    print(commercial.rapport_pipeline())
    print("\n⚡ Lancement de la campagne (3 prospects prioritaires)...")
    result = commercial.lancer_campagne(nb_prospects=3, priorite="parfait")
    if result.get("success"):
        print(f"\n✅ {result['nb_emails']} emails générés dans : {result['dossier']}/")
        for e in result.get("emails", []):
            print(f"   → {e['prospect']} ({e['contact']}) : {e['fichier'].split('/')[-1]}")


def mode_relances():
    """Envoie les relances aux prospects qui n'ont pas répondu."""
    print("\n📨 Agent Commercial — Campagne de relances\n")
    commercial = AgentCommercial()
    result = commercial.campagne_relances(delai_jours=7)
    relances = result.get("relances", [])
    if relances:
        print(f"✅ {len(relances)} relance(s) générée(s)")
    else:
        print("ℹ️  Aucune relance nécessaire pour l'instant")


def mode_analytics():
    """Génère le dashboard analytics HTML."""
    print("\n📊 Agent Analytics — Dashboard hebdomadaire\n")
    analytics = AgentAnalytics()
    print(analytics.rapport_texte())
    chemin = analytics.generer_dashboard()
    print(f"\n✅ Dashboard ouvert : {chemin}")


def mode_cfo():
    """Génère le rapport financier et les projections."""
    print("\n💰 Agent CFO — Rapport financier mensuel\n")
    growth = AgentGrowth()
    stats  = growth.stats_abonnes()
    cfo    = AgentCFO()
    print(cfo.rapport_mensuel(nb_abonnes=stats["total_actifs"]))
    print("\n💡 Pour générer les conseils IA (nécessite la clé API) :")
    print("   cfo.rapport_avec_conseils(nb_abonnes=X)")


def mode_adjoint(no_email: bool = False):
    """Lance le cycle complet du Directeur Adjoint IA."""
    print("\n🤝 Agent Directeur Adjoint — Cycle quotidien\n")
    adjoint = AgentAdjoint()
    result  = adjoint.run(envoyer_email=not no_email)
    if result.get("success"):
        print(f"\n✅ Cycle terminé — Rapport : {result['rapport']}")
    else:
        print("\n❌ Cycle terminé avec erreurs")


def mode_booster(simulation: bool = False, nb: int = 5):
    """Lance le Growth Booster pour maximiser les abonnés."""
    print("\n🚀 Agent Growth Booster — Croissance abonnés\n")
    booster = AgentGrowthBooster()
    result  = booster.run(mode_simulation=simulation, nb_simulations=nb)
    if result.get("fichier_strategie"):
        print(f"\n✅ Stratégie générée : {result['fichier_strategie']}")


def mode_ceo_brief():
    """Génère le brief stratégique CEO."""
    print("\n📋 Agent CEO Brief — Brief stratégique\n")
    brief = AgentCEOBrief()
    result = brief.lancer_reunion()
    if result:
        print(f"\n✅ Brief CEO généré avec succès")
    else:
        print("\n❌ Erreur lors de la génération du brief")


def mode_demo():
    """Mode démo sans clé API — données simulées."""
    print("\n🎭 Mode Démo — Données simulées\n")

    rapport_simule = {
        "meta": {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "date":      datetime.now().strftime("%d/%m/%Y"),
            "semaine":   datetime.now().strftime("Semaine %W de %Y"),
        },
        "crypto": {
            "BTC": {"nom": "Bitcoin",   "prix_usd": 67450, "variation_24h":  2.3,
                    "variation_7j":  5.1, "market_cap_mrd": 1320, "volume_24h_mrd": 28.4, "ath_usd": 73750, "ath_pct": -8.5},
            "ETH": {"nom": "Ethereum",  "prix_usd":  3210, "variation_24h": -1.2,
                    "variation_7j":  3.4, "market_cap_mrd":  385, "volume_24h_mrd": 14.2, "ath_usd":  4878, "ath_pct": -34.2},
            "SOL": {"nom": "Solana",    "prix_usd":   142, "variation_24h":  4.7,
                    "variation_7j": 12.3, "market_cap_mrd":   65, "volume_24h_mrd":  3.8, "ath_usd":   260, "ath_pct": -45.4},
            "BNB": {"nom": "BNB",       "prix_usd":   580, "variation_24h":  0.9,
                    "variation_7j":  2.1, "market_cap_mrd":   84, "volume_24h_mrd":  1.2, "ath_usd":   692, "ath_pct": -16.2},
            "XRP": {"nom": "XRP",       "prix_usd":  0.62, "variation_24h": -0.5,
                    "variation_7j": -1.8, "market_cap_mrd":   33, "volume_24h_mrd":  2.1, "ath_usd":  3.84, "ath_pct": -83.8},
        },
        "bourse": {
            "indices": {
                "CAC 40":  {"valeur":  8125.40, "variation_24h":  0.45, "variation_7j":  1.2, "ticker": "^FCHI"},
                "S&P 500": {"valeur":  5248.10, "variation_24h": -0.30, "variation_7j":  0.8, "ticker": "^GSPC"},
                "Nasdaq":  {"valeur": 16420.50, "variation_24h":  0.70, "variation_7j":  2.1, "ticker": "^NDX"},
                "DAX":     {"valeur": 18320.00, "variation_24h":  0.25, "variation_7j": -0.4, "ticker": "^GDAXI"},
            },
            "actions": {
                "Apple":   {"prix": 172.50, "variation_24h":  1.2, "ticker": "AAPL",  "devise": "USD", "market_cap_mrd": 2650},
                "NVIDIA":  {"prix": 785.30, "variation_24h":  3.4, "ticker": "NVDA",  "devise": "USD", "market_cap_mrd": 1940},
                "LVMH":    {"prix": 748.00, "variation_24h": -0.8, "ticker": "MC.PA", "devise": "EUR", "market_cap_mrd":  374},
            },
        },
        "news_crypto": [
            {"titre": "Bitcoin dépasse les 67 000$ — les ETF Bitcoin atteignent un record de flux entrants", "source": "CoinDesk",   "url": "#", "date": "2026-03-20"},
            {"titre": "La Fed maintient ses taux — impact positif attendu sur les actifs risqués",           "source": "Bloomberg",  "url": "#", "date": "2026-03-20"},
            {"titre": "Ethereum prépare une mise à jour majeure — ce que ça change pour les investisseurs",  "source": "Decrypt",    "url": "#", "date": "2026-03-19"},
            {"titre": "Solana s'impose comme alternative sérieuse à Ethereum en termes de volume DeFi",      "source": "The Block",  "url": "#", "date": "2026-03-19"},
            {"titre": "Pourquoi les grandes banques s'intéressent de plus en plus aux cryptos institutionnelles", "source": "FT",    "url": "#", "date": "2026-03-18"},
        ],
        "mood": {"valeur": 68, "sentiment": "Greed", "hier_valeur": 64, "hier_sentiment": "Greed"},
    }

    analyses_simulees = {
        "meta":    rapport_simule["meta"],
        "intro":   "Cette semaine, les marchés financiers envoient des signaux encourageants. Bitcoin consolide au-dessus des 67 000$, les grands indices boursiers progressent modestement, et le sentiment général reste optimiste. Une semaine idéale pour comprendre comment fonctionne ce jeu fascinant qu'est l'investissement.",
        "crypto":  "**Vue d'ensemble** : Le marché crypto affiche une belle dynamique cette semaine, avec Bitcoin en hausse de +2.3% et Solana particulièrement en forme à +4.7%.\n\n**Les mouvements notables** : Solana se distingue avec une progression de +12.3% sur 7 jours, portée par une adoption croissante de son écosystème DeFi. Bitcoin reste roi avec 1 320 milliards de dollars de capitalisation.\n\n**Ce que ça signifie** : Pour un débutant, retenir que lorsque Bitcoin monte, c'est souvent bon signe pour tout le marché. Mais Solana montre qu'il y a des opportunités en dehors du Bitcoin.\n\n**Point clé** : Ne jamais mettre tous ses œufs dans le même panier — même dans la crypto, la diversification est essentielle.",
        "bourse":  "**Ambiance des marchés** : Les bourses mondiales sont globalement en légère hausse cette semaine. Le CAC 40 gagne +0.45% et le Nasdaq +0.7%, signe que les investisseurs restent confiants malgré les incertitudes macro.\n\n**Actions à surveiller** : NVIDIA continue sa trajectoire spectaculaire (+3.4% sur la journée) portée par la demande en chips IA. LVMH recule légèrement (-0.8%) après des résultats mitigés en Asie.\n\n**Ce qu'il faut comprendre** : Les marchés boursiers réagissent fortement aux décisions des banques centrales. Quand la Fed garde les taux stables, c'est généralement positif pour les actions.\n\n**Point clé** : NVIDIA illustre parfaitement comment investir dans une mégatendance (l'IA) peut générer des rendements exceptionnels.",
        "concept": "💡 Le concept de la semaine : **L'ETF (Exchange-Traded Fund)**\n\nUn ETF est un panier d'actions ou de cryptos que tu achètes en une seule fois.\n\n**Analogie** : Imagine que tu veuilles goûter la cuisine de 500 restaurants. Au lieu de les visiter un par un, tu achètes un forfait « Top 500 ». Un ETF S&P 500, c'est pareil : une seule action pour investir dans 500 grandes entreprises américaines.\n\n**Pourquoi c'est utile** : Diversification facile, frais très bas. Le meilleur point d'entrée pour un débutant.",
        "news_raw":       rapport_simule["news_crypto"],
        "mood":           rapport_simule["mood"],
        "donnees_brutes": rapport_simule,
    }

    chemin = AgentRedacteur().rediger_newsletter(analyses_simulees)
    print(f"\n🎭 Newsletter démo générée : {chemin}\n")
    return chemin


# ─── POINT D'ENTRÉE ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AlphaBot — Entreprise newsletter IA Bourse & Crypto",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python main.py               # Pipeline newsletter complet
  python main.py --demo        # Démo sans clé API
  python main.py --growth      # Stats abonnés
  python main.py --commercial  # Génère emails prospection sponsors
  python main.py --full        # Tout lancer d'un coup
        """
    )
    parser.add_argument("--demo",       action="store_true", help="Mode démo sans clé API")
    parser.add_argument("--veille",     action="store_true", help="Agent Veille seul")
    parser.add_argument("--growth",     action="store_true", help="Agent Growth (abonnés + stats)")
    parser.add_argument("--commercial", action="store_true", help="Agent Commercial (prospection)")
    parser.add_argument("--relances",   action="store_true", help="Agent Commercial (relances)")
    parser.add_argument("--analytics",  action="store_true", help="Agent Analytics (dashboard)")
    parser.add_argument("--cfo",        action="store_true", help="Agent CFO (rapport financier)")
    parser.add_argument("--adjoint",    action="store_true", help="Directeur Adjoint IA (cycle complet)")
    parser.add_argument("--no-email",   action="store_true", help="Désactiver l'envoi email (avec --adjoint)")
    parser.add_argument("--booster",    action="store_true", help="Growth Booster (stratégies + simulation)")
    parser.add_argument("--ceo-brief",  action="store_true", help="Brief stratégique CEO")
    parser.add_argument("--simulation", action="store_true", help="Mode simulation abonnés (avec --booster)")
    parser.add_argument("--nb",         type=int, default=5, help="Nb abonnés simulation (avec --booster --simulation)")
    parser.add_argument("--full",       action="store_true", help="Pipeline complet tous agents")
    args = parser.parse_args()

    if args.demo:
        mode_demo()
    elif args.veille:
        mode_veille_seul()
    elif args.growth:
        mode_growth()
    elif args.commercial:
        mode_commercial()
    elif args.relances:
        mode_relances()
    elif args.analytics:
        mode_analytics()
    elif args.cfo:
        mode_cfo()
    elif args.adjoint:
        mode_adjoint(no_email=args.no_email)
    elif args.booster:
        mode_booster(simulation=args.simulation, nb=args.nb)
    elif args.ceo_brief:
        mode_ceo_brief()
    elif args.full:
        pipeline_full()
    else:
        pipeline_newsletter()
