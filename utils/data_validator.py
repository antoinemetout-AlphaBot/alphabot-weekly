"""Validation des données en amont pour protéger les agents en aval."""

import json
import os
from datetime import datetime, timedelta

def valider_rapport_veille(rapport):
    """Vérifie que le rapport de veille contient des données exploitables.

    Args:
        rapport: dict retourné par AgentVeille().collecter()

    Returns:
        (bool, str): (est_valide, message_erreur)
    """
    if not rapport or not isinstance(rapport, dict):
        return False, "Rapport de veille vide ou invalide"

    # Vérifier qu'au moins une source de données est présente
    has_crypto = rapport.get("crypto") and len(rapport.get("crypto", {})) > 0
    has_indices = rapport.get("indices") and len(rapport.get("indices", {})) > 0
    has_bourse = rapport.get("bourse") and len(rapport.get("bourse", {})) > 0

    if not has_crypto and not has_indices and not has_bourse:
        return False, "Ni crypto ni indices ni bourse disponibles dans le rapport"

    return True, "OK"


def valider_analyses(analyses):
    """Vérifie que les analyses sont exploitables avant la rédaction.

    Args:
        analyses: dict retourné par AgentAnalyste().analyser()

    Returns:
        (bool, str): (est_valide, message_erreur)
    """
    if not analyses or not isinstance(analyses, dict):
        return False, "Analyses vides ou invalides"

    # Au moins une section d'analyse doit contenir du texte
    sections = ["crypto", "macro", "bourse", "geopolitique", "synthese"]
    non_vides = [s for s in sections if analyses.get(s) and len(str(analyses.get(s, ""))) > 50]

    if len(non_vides) < 2:
        return False, f"Seulement {len(non_vides)} section(s) d'analyse exploitables (minimum: 2)"

    return True, "OK"


def fichier_recent(filepath, max_age_heures=24):
    """Vérifie qu'un fichier existe et date de moins de N heures."""
    if not os.path.exists(filepath):
        return False, f"Fichier manquant: {filepath}"

    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
    age = datetime.now() - mtime

    if age > timedelta(hours=max_age_heures):
        return False, f"Fichier trop ancien ({age.total_seconds()/3600:.1f}h): {filepath}"

    return True, "OK"
