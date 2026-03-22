"""
AlphaBot — Module de logging d'activité partagé
================================================
Tous les agents l'importent et appellent log_event() pour tracer leur activité.
Le fichier de log (data/activity_log.jsonl) est lu par monitor.py en temps réel.

Usage dans un agent :
    from utils.activity_logger import log_event
    log_event("Agent Growth", "start",   "Démarrage de l'envoi newsletter")
    log_event("Agent Growth", "success", "Newsletter envoyée à 42 abonnés", {"nb": 42})
    log_event("Agent Growth", "error",   "Erreur SMTP", {"err": str(e)})

Types d'événements :
    start     → début d'une tâche
    progress  → étape intermédiaire
    success   → tâche réussie
    error     → erreur rencontrée
    info      → information générale
    warning   → avertissement
    milestone → objectif atteint (ex: 100 abonnés)
"""

import json, os
from datetime import datetime
from pathlib import Path

LOG_FILE   = os.path.join("data", "activity_log.jsonl")
MAX_LINES  = 2000   # On garde les 2000 derniers events (rotation automatique)


def log_event(agent: str, event_type: str, message: str, data: dict = None):
    """
    Ajoute un événement dans le log d'activité.

    Args:
        agent      : Nom de l'agent (ex: "Agent Growth", "Directeur Adjoint")
        event_type : Type d'event ("start", "progress", "success", "error", "info", "milestone")
        message    : Message lisible
        data       : Données supplémentaires optionnelles (dict)
    """
    Path("data").mkdir(exist_ok=True)

    event = {
        "ts":      datetime.now().isoformat(),
        "agent":   agent,
        "type":    event_type,
        "message": message,
        "data":    data or {},
    }

    # Append dans le fichier JSONL
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    # Rotation : si le fichier dépasse MAX_LINES, on coupe les plus vieilles
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) > MAX_LINES:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.writelines(lines[-MAX_LINES:])
    except Exception:
        pass


def lire_events(n: int = 200) -> list:
    """Retourne les N derniers événements (du plus récent au plus ancien)."""
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        events = []
        for line in reversed(lines[-n:]):
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return events
    except FileNotFoundError:
        return []


def dernier_event_par_agent() -> dict:
    """Retourne le dernier événement de chaque agent (pour les status cards)."""
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        agents = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                agents[e["agent"]] = e   # écrase avec le plus récent
            except Exception:
                pass
        return agents
    except FileNotFoundError:
        return {}


def exporter_activity_feed(n: int = 100):
    """
    Exporte les N derniers événements vers data/activity_feed.json
    Ce fichier est lu par le dashboard HTML public pour affichage temps réel.
    Appelé automatiquement après chaque tâche de l'orchestrateur.
    """
    Path("data").mkdir(exist_ok=True)
    feed_file = os.path.join("data", "activity_feed.json")

    events = lire_events(n)

    # Calcul des stats par agent
    agents_status = {}
    for e in events:
        agent = e.get("agent", "Inconnu")
        if agent not in agents_status:
            agents_status[agent] = {
                "agent": agent,
                "last_event": e,
                "last_ts": e.get("ts", ""),
                "last_type": e.get("type", "info"),
                "last_message": e.get("message", ""),
                "total_today": 0,
                "errors_today": 0,
                "successes_today": 0,
            }
        today = datetime.now().strftime("%Y-%m-%d")
        if e.get("ts", "").startswith(today):
            agents_status[agent]["total_today"] += 1
            if e.get("type") in ("error",):
                agents_status[agent]["errors_today"] += 1
            if e.get("type") in ("success", "milestone"):
                agents_status[agent]["successes_today"] += 1

    feed = {
        "generated_at": datetime.now().isoformat(),
        "total_events": len(events),
        "events": events,
        "agents": list(agents_status.values()),
    }

    with open(feed_file, "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, indent=2)

    return feed_file
