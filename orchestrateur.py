"""
AlphaBot — Orchestrateur Intelligent ⚡
Planning optimisé : actif 8h-18h, veille la nuit.
Coût estimé : ~3-5€/mois maximum.

╔══════════════════════════════════════════════════════════════╗
║  python orchestrateur.py          → Lance l'orchestrateur    ║
║  python orchestrateur.py --status → Affiche le planning      ║
║  python orchestrateur.py --reset  → Relance tout maintenant  ║
╚══════════════════════════════════════════════════════════════╝

PLANNING JOURNALIER (lundi-vendredi) :
  07:30 → Newsletter complète (lundi uniquement)
  08:00 → Directeur Adjoint — bilan nuit + briefing
  08:30 → Veille marchés — ouverture
  10:00 → Growth Booster 🔥 — contenu + abonnés
  11:00 → Commercial — prospection matin
  12:00 → Veille marchés — mi-journée
  13:30 → Growth Booster 🔥 — contenu + abonnés
  14:30 → Veille marchés — après-midi
  15:30 → Growth Booster 🔥 — contenu + abonnés
  16:00 → Commercial — relances
  16:30 → Analytics + CFO — bilans
  17:30 → Directeur Adjoint — bilan journée + rapport CEO
  18:00 → PAUSE — agents en veille jusqu'au lendemain 7h30
"""

import sys, json, time, argparse, traceback, os, atexit
from datetime import datetime, timedelta, date
from pathlib import Path

# ─── ANTI-DOUBLON : empêche deux orchestrateurs de tourner en même temps ─────
LOCK_FILE = Path("data") / "orchestrateur.lock"

def verifier_instance_unique():
    """Vérifie qu'aucun autre orchestrateur ne tourne. Retourne True si OK."""
    Path("data").mkdir(exist_ok=True)
    if LOCK_FILE.exists():
        try:
            contenu = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
            pid = contenu.get("pid", 0)
            started = contenu.get("started", "")
            # Vérifier si le processus est encore vivant
            try:
                os.kill(pid, 0)  # signal 0 = teste si le process existe
                # Le process existe encore → doublon
                print(f"\n  ⚠️  Un orchestrateur tourne déjà (PID {pid}, démarré {started}).")
                print(f"  ⚠️  Fermez l'autre fenêtre d'abord, ou supprimez data/orchestrateur.lock")
                print(f"  ⚠️  Arrêt automatique de cette instance.\n")
                return False
            except (OSError, ProcessLookupError):
                # Le process n'existe plus → ancien lock orphelin, on le supprime
                pass
        except Exception:
            pass
    # Écrire notre PID
    LOCK_FILE.write_text(json.dumps({
        "pid": os.getpid(),
        "started": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }), encoding="utf-8")
    return True

def liberer_lock():
    """Supprime le lock file à l'arrêt."""
    try:
        if LOCK_FILE.exists():
            contenu = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
            if contenu.get("pid") == os.getpid():
                LOCK_FILE.unlink()
    except Exception:
        pass

atexit.register(liberer_lock)

try:
    from utils.activity_logger import log_event
    def _log(agent, type_, msg, data=None): log_event(agent, type_, msg, data)
except Exception:
    def _log(agent, type_, msg, data=None): print(f"[{datetime.now().strftime('%H:%M')}] [{agent}] {type_.upper()}: {msg}")

from utils.data_validator import valider_rapport_veille, valider_analyses

ORCHESTRATEUR = "Orchestrateur"
DATA_DIR = Path("data")
MEMORY_FILE  = DATA_DIR / "agent_memory.json"
SCHEDULE_FILE = DATA_DIR / "orchestrateur_schedule.json"
DATA_DIR.mkdir(exist_ok=True)

# ─── PLAGES HORAIRES ──────────────────────────────────────────────────────────
HEURE_DEBUT   = 7    # 7h30 (newsletter lundi)
HEURE_FIN     = 18   # 18h00

# ─── PLANNING FIXE JOURNALIER ─────────────────────────────────────────────────
# (heure, minute, jours, fonction, nom, description)
# jours : None = tous les jours, 0=lundi, 1=mardi... 6=dimanche
PLANNING_FIXE = [
    # NEWSLETTER — quotidienne à 7h30
    {
        "heure": 7, "minute": 30,
        "jours": None,  # Tous les jours
        "fonction": "run_newsletter_complete",
        "nom": "Newsletter Quotidienne 📰",
        "description": "Pipeline Veille → Analyse → Rédaction → Envoi abonnés (quotidien)",
        "id": "newsletter_lundi",
    },
    # 07:45 — Sync abonnés Netlify (chaque jour)
    {
        "heure": 7, "minute": 45,
        "jours": None,
        "fonction": "run_sync_netlify",
        "nom": "Sync Abonnés Netlify 🔄",
        "description": "Récupère les nouvelles inscriptions depuis Netlify Forms → subscribers.csv",
        "id": "sync_netlify",
    },
    # 08:00 — Directeur Adjoint (briefing matin)
    {
        "heure": 8, "minute": 0,
        "jours": None,  # Tous les jours
        "fonction": "run_adjoint",
        "nom": "Directeur Adjoint — Matin 🤝",
        "description": "Bilan nuit, scan projet, supervision équipe, directives du jour",
        "id": "adjoint_matin",
    },
    # 08:30 — Veille marchés (ouverture)
    {
        "heure": 8, "minute": 30,
        "jours": None,
        "fonction": "run_veille",
        "nom": "Veille Marchés — Ouverture 🔍",
        "description": "Collecte Bitcoin, DXY, Pétrole, Or, indices à l'ouverture",
        "id": "veille_matin",
    },
    # 10:00 — Growth Booster #1
    {
        "heure": 10, "minute": 0,
        "jours": None,
        "fonction": "run_growth_booster",
        "nom": "Growth Booster 🚀 — Session 1",
        "description": "Génère contenu LinkedIn, stratégies croissance, profils simulation",
        "id": "booster_1",
    },
    # 09:30 — DA Site (insights géopolitiques + contenu)
    {
        "heure": 9, "minute": 30,
        "jours": None,
        "fonction": "run_da_site",
        "nom": "DA Site 🎨 — Insights Géopolitiques",
        "description": "Génère les cartes géopolitiques→marchés→actions pour le site",
        "id": "da_site",
    },
    # 09:45 — Investissement IA (mise à jour portefeuille)
    {
        "heure": 9, "minute": 45,
        "jours": None,
        "fonction": "run_investissement",
        "nom": "Investissement IA 📈 — Mise à jour portefeuille",
        "description": "Met à jour les prix, calcule P&L, évalue nouvelles opportunités",
        "id": "investissement",
    },
    # 11:00 — Commercial (prospection matin)
    {
        "heure": 11, "minute": 0,
        "jours": None,
        "fonction": "run_commercial",
        "nom": "Commercial — Prospection 💼",
        "description": "Génère emails prospection nouveaux sponsors",
        "id": "commercial_matin",
    },
    # 12:00 — Veille marchés (midi)
    {
        "heure": 12, "minute": 0,
        "jours": None,
        "fonction": "run_veille",
        "nom": "Veille Marchés — Midi 🔍",
        "description": "Collecte marchés mi-journée, actualités géopolitiques",
        "id": "veille_midi",
    },
    # 13:30 — Growth Booster #2
    {
        "heure": 13, "minute": 30,
        "jours": None,
        "fonction": "run_growth_booster",
        "nom": "Growth Booster 🚀 — Session 2",
        "description": "Nouveaux contenus Twitter/Reddit, stratégies SEO",
        "id": "booster_2",
    },
    # 14:30 — Veille marchés (après-midi)
    {
        "heure": 14, "minute": 30,
        "jours": None,
        "fonction": "run_veille",
        "nom": "Veille Marchés — Après-midi 🔍",
        "description": "Suivi marchés après-midi, événements géopolitiques",
        "id": "veille_apm",
    },
    # 15:30 — Growth Booster #3
    {
        "heure": 15, "minute": 30,
        "jours": None,
        "fonction": "run_growth_booster",
        "nom": "Growth Booster 🚀 — Session 3",
        "description": "Contenu viral, partenariats, campagne abonnés",
        "id": "booster_3",
    },
    # 16:00 — Commercial (relances)
    {
        "heure": 16, "minute": 0,
        "jours": None,
        "fonction": "run_commercial_relances",
        "nom": "Commercial — Relances 📨",
        "description": "Relance prospects sans réponse depuis 7 jours",
        "id": "commercial_relances",
    },
    # 16:30 — Analytics
    {
        "heure": 16, "minute": 30,
        "jours": None,
        "fonction": "run_analytics",
        "nom": "Analytics 📊",
        "description": "Génère dashboard métriques du jour",
        "id": "analytics",
    },
    # 16:45 — CFO
    {
        "heure": 16, "minute": 45,
        "jours": None,
        "fonction": "run_cfo",
        "nom": "CFO 💰",
        "description": "Rapport financier et projections",
        "id": "cfo",
    },
    # 08:50 — Email quotidien CEO (titres newsletter + lien vers le site)
    {
        "heure": 8, "minute": 50,
        "jours": None,
        "fonction": "run_email_quotidien_ceo",
        "nom": "Email Quotidien CEO 📧",
        "description": "Envoie à Antoine les titres du jour + lien newsletter",
        "id": "email_ceo_matin",
    },
    # 08:35 — Tweet matin @AlphaBot_Weekly
    {
        "heure": 8, "minute": 35,
        "jours": None,
        "fonction": "run_twitter",
        "nom": "Twitter — Tweet Matin 🐦",
        "description": "Poste le tweet du matin sur @AlphaBot_Weekly (thread / donnée choc)",
        "id": "twitter_matin",
    },
    # 12:30 — Tweet midi @AlphaBot_Weekly
    {
        "heure": 12, "minute": 30,
        "jours": None,
        "fonction": "run_twitter",
        "nom": "Twitter — Tweet Midi 🐦",
        "description": "Poste le tweet de midi sur @AlphaBot_Weekly (question / réaction actu)",
        "id": "twitter_midi",
    },
    # 17:45 — Tweet soir @AlphaBot_Weekly
    {
        "heure": 17, "minute": 45,
        "jours": None,
        "fonction": "run_twitter",
        "nom": "Twitter — Tweet Soir 🐦",
        "description": "Poste le tweet du soir sur @AlphaBot_Weekly (CTA doux / stat)",
        "id": "twitter_soir",
    },
    # 17:30 — Directeur Adjoint (bilan soir + rapport CEO)
    {
        "heure": 17, "minute": 30,
        "jours": None,
        "fonction": "run_adjoint_soir",
        "nom": "Directeur Adjoint — Soir + Rapport CEO 🤝",
        "description": "Bilan journée, actions correctives, rapport CEO par email",
        "id": "adjoint_soir",
    },
    # ── ROBOT TRADER — Cycles horaires (9h-17h, lundi-vendredi) ──
    {
        "heure": 9, "minute": 0,
        "jours": [0, 1, 2, 3, 4],  # Lundi-vendredi
        "fonction": "run_robot_trader",
        "nom": "🤖 Robot Trader — Ouverture",
        "description": "Analyse marchés à l'ouverture, décisions d'achat/vente",
        "id": "trader_09h",
    },
    {
        "heure": 10, "minute": 0,
        "jours": [0, 1, 2, 3, 4],
        "fonction": "run_robot_trader",
        "nom": "🤖 Robot Trader — 10h",
        "description": "Cycle trading horaire — suivi positions + opportunités",
        "id": "trader_10h",
    },
    {
        "heure": 11, "minute": 0,
        "jours": [0, 1, 2, 3, 4],
        "fonction": "run_robot_trader",
        "nom": "🤖 Robot Trader — 11h",
        "description": "Cycle trading horaire — suivi positions + opportunités",
        "id": "trader_11h",
    },
    {
        "heure": 12, "minute": 0,
        "jours": [0, 1, 2, 3, 4],
        "fonction": "run_robot_trader",
        "nom": "🤖 Robot Trader — Midi",
        "description": "Cycle trading mi-journée — réévaluation positions",
        "id": "trader_12h",
    },
    {
        "heure": 13, "minute": 0,
        "jours": [0, 1, 2, 3, 4],
        "fonction": "run_robot_trader",
        "nom": "🤖 Robot Trader — 13h",
        "description": "Cycle trading horaire — suivi positions + opportunités",
        "id": "trader_13h",
    },
    {
        "heure": 14, "minute": 0,
        "jours": [0, 1, 2, 3, 4],
        "fonction": "run_robot_trader",
        "nom": "🤖 Robot Trader — 14h",
        "description": "Cycle trading horaire — US market opening",
        "id": "trader_14h",
    },
    {
        "heure": 15, "minute": 0,
        "jours": [0, 1, 2, 3, 4],
        "fonction": "run_robot_trader",
        "nom": "🤖 Robot Trader — 15h",
        "description": "Cycle trading horaire — suivi positions + opportunités",
        "id": "trader_15h",
    },
    {
        "heure": 16, "minute": 0,
        "jours": [0, 1, 2, 3, 4],
        "fonction": "run_robot_trader",
        "nom": "🤖 Robot Trader — 16h",
        "description": "Cycle trading horaire — suivi positions + opportunités",
        "id": "trader_16h",
    },
    {
        "heure": 17, "minute": 0,
        "jours": [0, 1, 2, 3, 4],
        "fonction": "run_robot_trader",
        "nom": "🤖 Robot Trader — Clôture",
        "description": "Dernier cycle — évaluation fin de journée, sécurisation positions",
        "id": "trader_17h",
    },
]


# ─── MÉMOIRE ─────────────────────────────────────────────────────────────────

def charger_memoire() -> dict:
    if MEMORY_FILE.exists():
        try: return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        except: pass
    return {"cycles": 0, "strategies_testees": [], "insights": [], "alertes": []}

def sauvegarder_memoire(m: dict):
    m["updated"] = datetime.now().isoformat()
    MEMORY_FILE.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")


# ─── SUIVI DES TÂCHES EXÉCUTÉES AUJOURD'HUI ──────────────────────────────────

def charger_executions_jour() -> dict:
    if SCHEDULE_FILE.exists():
        try:
            d = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
            # Si c'est un autre jour, reset
            if d.get("date") != date.today().isoformat():
                return {"date": date.today().isoformat(), "completed": {}}
            return d
        except: pass
    return {"date": date.today().isoformat(), "completed": {}}

def sauvegarder_executions(etat: dict):
    SCHEDULE_FILE.write_text(json.dumps(etat, ensure_ascii=False, indent=2), encoding="utf-8")

def a_deja_tourne_aujourd_hui(etat: dict, task_id: str) -> bool:
    return task_id in etat.get("completed", {})

def marquer_comme_execute(etat: dict, task_id: str, success: bool):
    etat.setdefault("completed", {})[task_id] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


# ─── FONCTIONS AGENTS ─────────────────────────────────────────────────────────

def run_sync_netlify(memoire: dict) -> bool:
    """Sync les nouvelles inscriptions depuis Netlify Forms."""
    try:
        from sync_netlify import sync_depuis_netlify
        result = sync_depuis_netlify()
        nb = result.get("nouveaux", 0)
        _log(ORCHESTRATEUR, "success", f"Sync Netlify : +{nb} nouvel(s) abonné(s)")
        return True
    except Exception as e:
        _log(ORCHESTRATEUR, "warning", f"Sync Netlify (non bloquant): {str(e)[:80]}")
        return True  # Non bloquant — continue même si Netlify pas configuré

def run_growth_booster(memoire: dict) -> bool:
    try:
        from agents.agent_growth_booster import AgentGrowthBooster
        cycles = memoire.get("cycles", 0)
        # Alterner : 1 simulation sur 3 cycles pour rester dans le budget
        mode_sim = (cycles % 3 == 0)
        booster = AgentGrowthBooster()
        result = booster.run(mode_simulation=mode_sim, nb_simulations=3)
        memoire["cycles"] = cycles + 1
        _log(ORCHESTRATEUR, "success", f"Growth Booster {'(sim)' if mode_sim else '(réel)'} terminé — score: {result.get('score', '?')} pts")
        return True
    except Exception as e:
        _log(ORCHESTRATEUR, "error", f"Growth Booster: {str(e)[:80]}")
        return False

def run_adjoint(memoire: dict) -> bool:
    try:
        from agents.agent_adjoint import AgentAdjoint
        result = AgentAdjoint().run(envoyer_email=False)
        _log(ORCHESTRATEUR, "success", "DA matin — supervision terminée")
        return True
    except Exception as e:
        _log(ORCHESTRATEUR, "error", f"DA matin: {str(e)[:80]}")
        return False

def run_adjoint_soir(memoire: dict) -> bool:
    """Bilan soir avec envoi du rapport CEO par email."""
    try:
        from agents.agent_adjoint import AgentAdjoint
        result = AgentAdjoint().run(envoyer_email=True)  # Email CEO le soir
        _log(ORCHESTRATEUR, "success", "DA soir — rapport CEO envoyé")
        return True
    except Exception as e:
        _log(ORCHESTRATEUR, "error", f"DA soir: {str(e)[:80]}")
        return False

def run_veille(memoire: dict) -> bool:
    try:
        from agents.agent_veille import AgentVeille
        rapport = AgentVeille().collecter()
        (DATA_DIR / "dernier_rapport_veille.json").write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        nb_crypto = len(rapport.get("crypto", {}))
        nb_indices = len(rapport.get("bourse", {}).get("indices", {}))
        _log(ORCHESTRATEUR, "success", f"Veille terminée — {nb_crypto} crypto(s), {nb_indices} indices")
        return True
    except Exception as e:
        _log(ORCHESTRATEUR, "error", f"Veille: {str(e)[:80]}")
        return False

def run_commercial(memoire: dict) -> bool:
    try:
        from agents.agent_commercial import AgentCommercial
        result = AgentCommercial().lancer_campagne(nb_prospects=2)
        _log(ORCHESTRATEUR, "success", f"Commercial: {result.get('nb_emails', 0)} emails prospection")
        return True
    except Exception as e:
        _log(ORCHESTRATEUR, "error", f"Commercial: {str(e)[:80]}")
        return False

def run_commercial_relances(memoire: dict) -> bool:
    try:
        from agents.agent_commercial import AgentCommercial
        result = AgentCommercial().campagne_relances(delai_jours=7)
        nb = len(result.get("relances", []))
        _log(ORCHESTRATEUR, "success", f"Commercial relances: {nb} relance(s) envoyée(s)")
        return True
    except Exception as e:
        _log(ORCHESTRATEUR, "error", f"Relances: {str(e)[:80]}")
        return False

def run_twitter(memoire: dict) -> bool:
    # Si déjà échoué aujourd'hui (credentials invalides), on skip pour ne pas spammer le log
    if memoire.get("twitter_disabled_today"):
        _log(ORCHESTRATEUR, "info", "Twitter : désactivé aujourd'hui (credentials expirés)")
        return True
    try:
        from agents.agent_twitter import AgentTwitter
        agent  = AgentTwitter()
        if not agent.ready:
            memoire["twitter_disabled_today"] = True
            _log(ORCHESTRATEUR, "warning", "Twitter : credentials invalides — désactivé pour la journée. Régénérer sur developer.twitter.com")
            return True
        result = agent.verifier_et_poster()
        nb     = len(result.get("postes", []))
        if nb > 0:
            _log(ORCHESTRATEUR, "success", f"Twitter : {nb} tweet(s) posté(s) sur @AlphaBot_Weekly", result)
        else:
            _log(ORCHESTRATEUR, "info", "Twitter : aucun tweet à poster dans cette fenêtre")
        return True
    except Exception as e:
        _log(ORCHESTRATEUR, "warning", f"Twitter (non bloquant) : {str(e)[:80]}")
        return True  # Non bloquant : le reste du pipeline continue

def run_da_site(memoire: dict) -> bool:
    try:
        from agents.agent_da_site import AgentDASite
        from agents.agent_veille import AgentVeille
        donnees = AgentVeille().collecter()
        agent   = AgentDASite()
        result  = agent.run(donnees_veille=donnees)
        nb = len(result.get("insights", []))
        _log(ORCHESTRATEUR, "success", f"DA Site : {nb} insight(s) géopolitiques générés", result)
        return True
    except Exception as e:
        _log(ORCHESTRATEUR, "warning", f"DA Site (non bloquant) : {str(e)[:80]}")
        return True

def run_email_quotidien_ceo(memoire: dict) -> bool:
    """Envoie à Antoine les titres du jour + lien newsletter chaque matin à 8h50."""
    try:
        from agents.agent_growth import AgentGrowth
        import glob, os
        from datetime import datetime

        # Trouve la newsletter la plus récente
        pattern = os.path.join("outputs", "alphabot_newsletter_*.html")
        fichiers = sorted(glob.glob(pattern), reverse=True)
        chemin = fichiers[0] if fichiers else None

        growth = AgentGrowth()
        if chemin:
            result = growth.envoyer_notification_quotidienne(chemin)
            _log(ORCHESTRATEUR, "success", f"Email quotidien CEO envoyé ({result.get('envoyes',0)} destinataires)")
        else:
            _log(ORCHESTRATEUR, "warning", "Email quotidien CEO: aucune newsletter trouvée")
        return True
    except Exception as e:
        _log(ORCHESTRATEUR, "error", f"Email quotidien CEO: {str(e)[:80]}")
        return False


def run_robot_trader(memoire: dict) -> bool:
    """Lance un cycle complet du Robot Trader autonome."""
    try:
        from agents.agent_trader import RobotTrader
        robot = RobotTrader()
        result = robot.run_cycle()
        capital = result.get("capital_actuel", 0)
        nb_trades = result.get("trades_executes", 0)
        nb_positions = result.get("nb_positions", 0)
        perf = result.get("performance_pct", 0)
        _log(ORCHESTRATEUR, "success",
             f"🤖 Robot Trader : {capital:.0f}€ ({perf:+.2f}%) | {nb_positions} positions | {nb_trades} trade(s) ce cycle",
             result)
        return True
    except Exception as e:
        _log(ORCHESTRATEUR, "error", f"Robot Trader : {str(e)[:120]}")
        traceback.print_exc()
        return False

def run_investissement(memoire: dict) -> bool:
    """Redirige vers le Robot Trader (rétrocompatibilité)."""
    return run_robot_trader(memoire)

def run_analytics(memoire: dict) -> bool:
    try:
        from agents.agent_analytics import AgentAnalytics
        chemin = AgentAnalytics().generer_dashboard()
        _log(ORCHESTRATEUR, "success", f"Analytics dashboard généré")
        return True
    except Exception as e:
        _log(ORCHESTRATEUR, "error", f"Analytics: {str(e)[:80]}")
        return False

def run_cfo(memoire: dict) -> bool:
    try:
        from agents.agent_growth import AgentGrowth
        from agents.agent_cfo import AgentCFO
        stats = AgentGrowth().stats_abonnes()
        AgentCFO().rapport_mensuel(nb_abonnes=stats["total_actifs"])
        _log(ORCHESTRATEUR, "success", "CFO rapport généré")
        return True
    except Exception as e:
        _log(ORCHESTRATEUR, "error", f"CFO: {str(e)[:80]}")
        return False

def run_newsletter_complete(memoire: dict) -> bool:
    try:
        from agents.agent_veille import AgentVeille
        from agents.agent_analyste import AgentAnalyste
        from agents.agent_redacteur import AgentRedacteur
        from agents.agent_growth import AgentGrowth

        _log(ORCHESTRATEUR, "start", "📰 Newsletter hebdomadaire — démarrage pipeline")

        # Étape 1: Veille
        rapport = AgentVeille().collecter()

        # Validation des données en amont
        est_valide, msg = valider_rapport_veille(rapport)
        if not est_valide:
            _log(ORCHESTRATEUR, "error", f"Validation rapport veille échouée: {msg}")
            return False
        _log(ORCHESTRATEUR, "success", f"Rapport veille validé: {msg}")

        # Étape 2: Analyse
        # Lundi = newsletter hebdo complète, autres jours = quotidienne
        mode = "hebdo" if datetime.now().weekday() == 0 else "quotidien"
        analyses = AgentAnalyste().analyser(rapport, mode=mode)

        # Validation des analyses en amont
        est_valide, msg = valider_analyses(analyses)
        if not est_valide:
            _log(ORCHESTRATEUR, "error", f"Validation analyses échouée: {msg}")
            return False
        _log(ORCHESTRATEUR, "success", f"Analyses validées: {msg}")

        # Ajoute les données du Robot Trader pour la section investissement
        try:
            portfolio_path = Path("data/portfolio_live.json")
            if portfolio_path.exists():
                analyses["portfolio_trader"] = json.loads(portfolio_path.read_text(encoding="utf-8"))
        except Exception:
            analyses["portfolio_trader"] = None

        # Étape 3: Rédaction
        analyses["donnees_brutes"] = rapport
        chemin = AgentRedacteur().rediger_newsletter(analyses)

        # Étape 4: Envoi
        growth = AgentGrowth()
        stats = growth.stats_abonnes()
        if stats["total_actifs"] > 0:
            # 1. Envoi newsletter complète
            result = growth.envoyer_newsletter(chemin)
            _log(ORCHESTRATEUR, "milestone", f"Newsletter envoyée à {result.get('envoyes', 0)} abonnés")
            # 2. Notification quotidienne avec gros titres + lien
            notif = growth.envoyer_notification_quotidienne(chemin)
            _log(ORCHESTRATEUR, "success", f"Notification quotidienne → {notif.get('envoyes', 0)} abonnés")
        else:
            _log(ORCHESTRATEUR, "warning", "Aucun abonné actif — newsletter générée mais non envoyée")
        return True
    except Exception as e:
        _log(ORCHESTRATEUR, "error", f"Newsletter: {str(e)[:80]}")
        traceback.print_exc()
        return False


# ─── AFFICHAGE PLANNING ───────────────────────────────────────────────────────

def afficher_planning():
    now = datetime.now()
    jour_semaine = now.weekday()  # 0=lundi
    jours_noms = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║     ALPHABOT — PLANNING 8H-18H (optimisé budget)            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"  📅 {jours_noms[jour_semaine]} {now.strftime('%d/%m/%Y')} — {now.strftime('%H:%M')}\n")

    print("  🌅 AUJOURD'HUI :")
    for tache in PLANNING_FIXE:
        jours = tache.get("jours")
        if jours is not None and jour_semaine not in jours:
            continue
        h, m = tache["heure"], tache["minute"]
        heure_str = f"{h:02d}:{m:02d}"
        heure_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
        status = "✅" if heure_dt < now else ("🔜" if (heure_dt - now).total_seconds() < 3600 else "⏳")
        print(f"    {status} {heure_str} — {tache['nom']}")

    print(f"\n  🌙 18h00 — VEILLE NOCTURNE (agents en pause)")
    print(f"\n  💰 Coût estimé : ~3-5€/mois")
    print(f"  🤖 Appels Claude/jour : ~10-15\n")


# ─── BOUCLE PRINCIPALE ────────────────────────────────────────────────────────

def boucle_principale():
    print("\n  ████████████████████████████████████████████████████████")
    print("  ██                                                    ██")
    print("  ██    ⚡ ALPHABOT — ORCHESTRATEUR INTELLIGENT         ██")
    print("  ██    Planning 8h-18h • Budget < 5€/mois             ██")
    print("  ██    Growth Booster × 3/jour • DA × 2/jour          ██")
    print("  ██                                                    ██")
    print("  ████████████████████████████████████████████████████████\n")

    _log(ORCHESTRATEUR, "start", "🚀 Orchestrateur démarré — Planning 8h-18h actif")

    memoire = charger_memoire()
    etat_jour = charger_executions_jour()

    print("  ✅ Prêt. Surveillance du planning en cours...\n")

    while True:
        try:
            now = datetime.now()
            jour_semaine = now.weekday()
            heure_actuelle = now.hour + now.minute / 60.0

            # Réinitialiser l'état au début d'un nouveau jour
            if etat_jour.get("date") != date.today().isoformat():
                _log(ORCHESTRATEUR, "info", f"📅 Nouveau jour — {date.today().isoformat()}")
                etat_jour = {"date": date.today().isoformat(), "completed": {}}
                sauvegarder_executions(etat_jour)

            # Chercher une tâche à lancer
            tache_lancee = False
            for tache in PLANNING_FIXE:
                task_id = tache["id"]

                # Vérifier si déjà exécutée aujourd'hui (anti-duplicate) — pas de log pour éviter le spam
                if a_deja_tourne_aujourd_hui(etat_jour, task_id):
                    continue

                # Vérifier le jour
                jours = tache.get("jours")
                if jours is not None and jour_semaine not in jours:
                    continue

                # Vérifier l'heure (dans les 5 prochaines minutes)
                heure_tache = tache["heure"] + tache["minute"] / 60.0
                if now.hour == tache["heure"] and abs(now.minute - tache["minute"]) <= 5:

                    # C'est l'heure !
                    print(f"\n  {'═'*56}")
                    print(f"  🤖 {tache['nom']}")
                    print(f"  📋 {tache['description']}")
                    print(f"  🕒 {now.strftime('%H:%M:%S')}")
                    print(f"  {'═'*56}")

                    _log(ORCHESTRATEUR, "start", f"Lancement : {tache['nom']}")

                    debut = datetime.now()
                    try:
                        fn = globals()[tache["fonction"]]
                        success = fn(memoire)
                    except Exception as e:
                        _log(ORCHESTRATEUR, "error", f"Crash {tache['nom']}: {str(e)[:80]}")
                        traceback.print_exc()
                        success = False

                    duree = (datetime.now() - debut).seconds
                    marquer_comme_execute(etat_jour, task_id, success)
                    sauvegarder_executions(etat_jour)
                    sauvegarder_memoire(memoire)

                    # Export feed JSON pour le dashboard public
                    try:
                        from utils.activity_logger import exporter_activity_feed
                        exporter_activity_feed(100)
                    except Exception:
                        pass

                    print(f"\n  {'✅' if success else '⚠️'} Terminé en {duree}s\n")
                    tache_lancee = True
                    break

            if not tache_lancee:
                # Affichage du statut en mode veille
                if heure_actuelle < HEURE_DEBUT or heure_actuelle >= HEURE_FIN:
                    # Mode nuit
                    heure_reveil = now.replace(hour=7, minute=25, second=0, microsecond=0)
                    if heure_reveil < now:
                        heure_reveil += timedelta(days=1)
                    delta = heure_reveil - now
                    h, m = divmod(int(delta.total_seconds() / 60), 60)
                    print(f"\r  🌙 Mode veille nocturne | Réveil dans {h}h{m:02d}m   ", end="", flush=True)
                    time.sleep(60)
                else:
                    # Mode bureau — trouver la prochaine tâche
                    prochaines = []
                    for tache in PLANNING_FIXE:
                        task_id = tache["id"]
                        if a_deja_tourne_aujourd_hui(etat_jour, task_id):
                            continue
                        jours = tache.get("jours")
                        if jours is not None and jour_semaine not in jours:
                            continue
                        heure_tache = now.replace(hour=tache["heure"], minute=tache["minute"], second=0, microsecond=0)
                        if heure_tache > now:
                            prochaines.append((heure_tache, tache["nom"]))

                    if prochaines:
                        prochaines.sort()
                        prochain_dt, prochain_nom = prochaines[0]
                        delta = prochain_dt - now
                        h, m = divmod(int(delta.total_seconds() / 60), 60)
                        print(f"\r  ⚡ Actif | Prochain : {prochain_nom[:35]} dans {h}h{m:02d}m   ", end="", flush=True)
                    else:
                        print(f"\r  ✅ Toutes les tâches du jour terminées | Veille à 18h   ", end="", flush=True)

                    time.sleep(30)  # Check toutes les 30s pendant les heures de bureau

        except KeyboardInterrupt:
            print("\n\n  ⏹️  Arrêt demandé.")
            _log(ORCHESTRATEUR, "info", "Orchestrateur arrêté manuellement")
            sauvegarder_memoire(memoire)
            sauvegarder_executions(etat_jour)
            print("  💾 État sauvegardé. Bonne nuit !\n")
            break
        except Exception as e:
            _log(ORCHESTRATEUR, "error", f"Erreur boucle: {str(e)[:80]}")
            traceback.print_exc()
            time.sleep(60)


# ─── POINT D'ENTRÉE ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AlphaBot Orchestrateur 8h-18h")
    parser.add_argument("--status", action="store_true", help="Affiche le planning du jour")
    parser.add_argument("--reset", action="store_true", help="Remet toutes les tâches comme non exécutées")
    args = parser.parse_args()

    if args.status:
        afficher_planning()
    elif args.reset:
        etat = {"date": date.today().isoformat(), "completed": {}}
        SCHEDULE_FILE.write_text(json.dumps(etat, ensure_ascii=False, indent=2), encoding="utf-8")
        print("✅ Planning remis à zéro — toutes les tâches relancées aujourd'hui.")
    else:
        # Anti-doublon : empêche deux orchestrateurs simultanés
        if not verifier_instance_unique():
            sys.exit(1)
        boucle_principale()
