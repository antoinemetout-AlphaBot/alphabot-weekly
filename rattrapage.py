"""
AlphaBot — Script de rattrapage matin
Lance tous les agents qui auraient dû tourner ce matin.
"""
import sys
import os
import json
import traceback
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ".")

print("=" * 60)
print("  ALPHABOT WEEKLY — ORCHESTRATEUR AUTOMATIQUE")
print(f"  Agents actifs de 8h a 18h tous les jours")
print("=" * 60)
print(f"\n  [INFO] Repertoire : {os.getcwd()}")
print(f"  [INFO] Rattrapage matin — {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
print()

erreurs = []

# ── 1. NEWSLETTER QUOTIDIENNE ────────────────────────────────
print("[1/6] Newsletter quotidienne (Veille → Analyse → Rédaction → Envoi)...")
try:
    from agents.agent_veille import AgentVeille
    from agents.agent_analyste import AgentAnalyste
    from agents.agent_redacteur import AgentRedacteur
    from agents.agent_growth import AgentGrowth
    from pathlib import Path

    rapport = AgentVeille().collecter()

    # Mode : hebdo le lundi, quotidien les autres jours
    jour_semaine = datetime.now().weekday()
    mode = "hebdo" if jour_semaine == 0 else "quotidien"
    analyses = AgentAnalyste().analyser(rapport, mode=mode)
    analyses["donnees_brutes"] = rapport

    # Injecter données robot trader si disponibles
    try:
        portfolio_path = Path("data/portfolio_live.json")
        if portfolio_path.exists():
            analyses["portfolio_trader"] = json.loads(portfolio_path.read_text(encoding="utf-8"))
    except Exception:
        analyses["portfolio_trader"] = None

    chemin = AgentRedacteur().rediger_newsletter(analyses)

    # Envoi aux abonnés
    growth = AgentGrowth()
    stats = growth.stats_abonnes()
    if stats["total_actifs"] > 0:
        result = growth.envoyer_newsletter(chemin)
        nb = result.get("envoyes", 0)
        print(f"  ✅ Newsletter envoyée à {nb} abonné(s) — {chemin}")
        # Notification quotidienne
        try:
            notif = growth.envoyer_notification_quotidienne(chemin)
            print(f"  ✅ Notification quotidienne → {notif.get('envoyes', 0)} abonnés")
        except Exception:
            pass
    else:
        print(f"  ⚠️  Newsletter générée ({chemin}) — aucun abonné actif")

    # Mise à jour de newsletters.json
    try:
        today_str = datetime.now().strftime("%Y-%m-%d")
        newsletters_path = Path("data/newsletters.json")
        if newsletters_path.exists():
            nl_data = json.loads(newsletters_path.read_text(encoding="utf-8"))
        else:
            nl_data = {"editions": [], "count": 0}
        dates_existantes = [e["date"] for e in nl_data["editions"]]
        if today_str not in dates_existantes:
            nl_data["editions"].insert(0, {
                "date": today_str,
                "label": datetime.now().strftime("%A %d %B %Y").capitalize(),
                "file": f"alphabot_newsletter_{today_str}.html"
            })
            nl_data["count"] = len(nl_data["editions"])
            newsletters_path.write_text(json.dumps(nl_data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  ✅ newsletters.json mis à jour")
    except Exception as e:
        print(f"  ⚠️ Mise à jour newsletters.json: {e}")

except Exception as e:
    msg = f"Newsletter: {e}"
    print(f"  ❌ {msg}")
    traceback.print_exc()
    erreurs.append(msg)

print()

# ── 2. ROBOT TRADER IA ───────────────────────────────────────
print("[2/6] Robot Trader IA (cycle de trading)...")
try:
    # Le robot ne trade que du lundi au vendredi
    if datetime.now().weekday() < 5:
        from agents.agent_trader import RobotTrader
        robot = RobotTrader()
        result = robot.run_cycle()
        nb_signaux = len(result.get("signaux", []))
        nb_ordres = len(result.get("ordres_executes", []))
        print(f"  ✅ Cycle terminé — {nb_signaux} signaux, {nb_ordres} ordres exécutés")
    else:
        print(f"  ⏭️  Weekend — le robot ne trade pas le samedi/dimanche")
except Exception as e:
    msg = f"Robot Trader: {e}"
    print(f"  ❌ {msg}")
    traceback.print_exc()
    erreurs.append(msg)

print()

# ── 3. AGENT DA SITE ────────────────────────────────────────
print("[3/6] Agent DA Site (insights + esthétique)...")
try:
    from agents.agent_da_site import AgentDASite
    result = AgentDASite().run_mission_da_complete()
    n = result.get("insights_count", 0)
    p = result.get("pages_ameliorees", 0)
    print(f"  ✅ {n} insights générés, {p} page(s) améliorée(s)")
except Exception as e:
    msg = f"DA Site: {e}"
    print(f"  ❌ {msg}")
    erreurs.append(msg)

print()

# ── 4. TWEET DE RATTRAPAGE ──────────────────────────────────
print("[4/6] Tweet du matin (rattrapage)...")
try:
    from agents.agent_twitter import AgentTwitter
    agent = AgentTwitter()
    if not agent.ready:
        print(f"  ⚠️  Twitter désactivé — credentials expirés. Régénérer sur developer.twitter.com")
    else:
        result = agent.verifier_et_poster()
        nb = len(result.get("postes", []))
        if nb > 0:
            print(f"  ✅ {nb} tweet(s) posté(s)")
        else:
            print(f"  ℹ️  Aucun tweet à poster dans cette fenêtre horaire")
except Exception as e:
    msg = f"Twitter: {e}"
    print(f"  ❌ {msg}")
    erreurs.append(msg)

print()

# ── 5. RAPPORT CEO ──────────────────────────────────────────
print("[5/6] Rapport CEO par email...")
try:
    from agents.agent_adjoint import AgentAdjoint
    AgentAdjoint().run(envoyer_email=True)
    print(f"  ✅ Rapport CEO envoyé à antoine.metout@gmail.com")
except Exception as e:
    msg = f"Rapport CEO: {e}"
    print(f"  ❌ {msg}")
    erreurs.append(msg)

print()

# ── 6. SYNC ABONNÉS NETLIFY ────────────────────────────────
print("[6/6] Sync abonnés Netlify...")
try:
    from sync_netlify import sync_netlify_forms
    result = sync_netlify_forms()
    print(f"  ✅ Sync terminée — {result.get('nouveaux', 0)} nouveau(x) abonné(s)")
except Exception as e:
    print(f"  ⚠️  Sync Netlify: {e} (non bloquant)")

print()
print("=" * 60)
if erreurs:
    print(f"  ⚠️  Terminé avec {len(erreurs)} erreur(s) :")
    for e in erreurs:
        print(f"     - {e}")
else:
    print("  ✅ Tout s'est bien passé !")
print(f"  Vérifie ta boite mail : antoine.metout@gmail.com")
print("=" * 60)

# Export du feed d'activité pour le dashboard public
try:
    from utils.activity_logger import exporter_activity_feed
    exporter_activity_feed(100)
    print(f"\n  📊 Dashboard mis à jour → data/activity_feed.json")
except Exception as ex:
    print(f"\n  ⚠️ Export feed: {ex}")

input("\nAppuyez sur Entrée pour fermer...")
