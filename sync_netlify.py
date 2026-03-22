"""
AlphaBot — Sync abonnés Netlify Forms → subscribers.csv
========================================================
Récupère automatiquement les nouvelles inscriptions depuis
Netlify Forms et les ajoute dans subscribers.csv.

Usage :
  python sync_netlify.py              → Sync toutes les nouvelles inscriptions
  python sync_netlify.py --dry-run    → Affiche sans modifier
  python sync_netlify.py --stats      → Affiche les stats

Prérequis :
  Dans .env :
    NETLIFY_ACCESS_TOKEN=xxx  (app.netlify.com/user/applications)
    NETLIFY_SITE_ID=xxx       (app.netlify.com → ton site → Site settings → General → Site ID)
"""

import os, sys, csv, json, requests
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.file_lock import file_lock

# ─── CONFIG ──────────────────────────────────────────────────────────────────
NETLIFY_TOKEN   = os.getenv("NETLIFY_ACCESS_TOKEN", "")
NETLIFY_SITE_ID = os.getenv("NETLIFY_SITE_ID", "")
FORM_NAME       = "alphabot-signup"
SUBSCRIBERS_CSV = os.path.join("data", "subscribers.csv")
SYNC_STATE_FILE = os.path.join("data", "netlify_sync_state.json")
Path("data").mkdir(exist_ok=True)


def charger_emails_existants() -> set:
    """Charge tous les emails déjà dans subscribers.csv."""
    emails = set()
    try:
        with file_lock(SUBSCRIBERS_CSV):
            with open(SUBSCRIBERS_CSV, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    emails.add(row.get("email", "").lower().strip())
    except FileNotFoundError:
        pass
    return emails


def charger_etat_sync() -> dict:
    """Charge le dernier état de synchronisation (pour ne pas re-traiter)."""
    try:
        with open(SYNC_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"derniere_sync": None, "ids_traites": []}


def sauvegarder_etat(etat: dict):
    with open(SYNC_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(etat, f, indent=2)


def ajouter_abonne(email: str, source: str = "site_web", date_inscription: str = None):
    """Ajoute un abonné au CSV s'il n'existe pas déjà."""
    date = date_inscription or datetime.now().strftime("%Y-%m-%d")
    prenom = email.split("@")[0].split(".")[0].capitalize()

    with file_lock(SUBSCRIBERS_CSV):
        # Crée le CSV si absent
        if not os.path.exists(SUBSCRIBERS_CSV):
            with open(SUBSCRIBERS_CSV, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(["email", "prenom", "source", "date_inscription", "actif", "opens", "clicks"])

        with open(SUBSCRIBERS_CSV, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([email, prenom, source, date, "oui", 0, 0])


def sync_depuis_netlify(dry_run: bool = False) -> dict:
    """
    Récupère les inscriptions depuis Netlify Forms API et les ajoute au CSV.
    """
    if not NETLIFY_TOKEN or not NETLIFY_SITE_ID:
        print("⚠️  NETLIFY_ACCESS_TOKEN ou NETLIFY_SITE_ID manquant dans .env")
        print("   → Créer un token sur : https://app.netlify.com/user/applications")
        print("   → Trouver ton Site ID : app.netlify.com → ton site → Settings → General")
        return {"error": "credentials_manquants"}

    print(f"\n━━━ Sync Netlify Forms → subscribers.csv ━━━")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    if dry_run:
        print("🔍 MODE DRY-RUN — Aucune modification")

    # 1. Récupérer le form ID
    headers = {"Authorization": f"Bearer {NETLIFY_TOKEN}"}
    try:
        r = requests.get(
            f"https://api.netlify.com/api/v1/sites/{NETLIFY_SITE_ID}/forms",
            headers=headers, timeout=10
        )
        r.raise_for_status()
        forms = r.json()
    except Exception as e:
        print(f"❌ Erreur API Netlify (forms): {e}")
        return {"error": str(e)}

    form_id = None
    for form in forms:
        if form.get("name") == FORM_NAME:
            form_id = form["id"]
            print(f"✅ Formulaire trouvé : {FORM_NAME} (ID: {form_id})")
            break

    if not form_id:
        print(f"❌ Formulaire '{FORM_NAME}' introuvable sur Netlify")
        print(f"   Formulaires disponibles : {[f.get('name') for f in forms]}")
        return {"error": "form_introuvable"}

    # 2. Récupérer les soumissions
    try:
        r = requests.get(
            f"https://api.netlify.com/api/v1/forms/{form_id}/submissions?per_page=1000",
            headers=headers, timeout=10
        )
        r.raise_for_status()
        submissions = r.json()
    except Exception as e:
        print(f"❌ Erreur API Netlify (submissions): {e}")
        return {"error": str(e)}

    print(f"📬 {len(submissions)} soumission(s) totale(s) dans Netlify Forms")

    # 3. Filtrer les nouveaux
    emails_existants = charger_emails_existants()
    etat = charger_etat_sync()
    ids_traites = set(etat.get("ids_traites", []))

    nouveaux = 0
    doublons = 0

    for sub in submissions:
        sub_id = sub.get("id", "")
        if sub_id in ids_traites:
            continue

        data = sub.get("data", {})
        email = data.get("email", "").lower().strip()
        source = data.get("source", "site_web")
        date_raw = sub.get("created_at", "")[:10]  # "2026-03-20"

        if not email or "@" not in email:
            ids_traites.add(sub_id)
            continue

        if email in emails_existants:
            doublons += 1
            ids_traites.add(sub_id)
            continue

        if not dry_run:
            ajouter_abonne(email, source, date_raw)
            emails_existants.add(email)

        nouveaux += 1
        ids_traites.add(sub_id)
        print(f"  {'[DRY]' if dry_run else '✅'} Ajouté : {email} (source: {source}, date: {date_raw})")

    if not dry_run:
        etat["ids_traites"] = list(ids_traites)
        etat["derniere_sync"] = datetime.now().isoformat()
        sauvegarder_etat(etat)

    print(f"\n✅ Sync terminée : +{nouveaux} nouvel(s) abonné(s) | {doublons} doublon(s)")
    print(f"   Total CSV : {len(emails_existants)} abonné(s)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    return {"nouveaux": nouveaux, "doublons": doublons, "total": len(emails_existants)}


def ajouter_manuellement(email: str, source: str = "manuel"):
    """Ajoute un abonné manuellement (fallback si Netlify pas configuré)."""
    emails = charger_emails_existants()
    if email.lower() in emails:
        print(f"⚠️  {email} est déjà abonné.")
        return False
    ajouter_abonne(email, source)
    print(f"✅ {email} ajouté à subscribers.csv (source: {source})")
    return True


def afficher_stats():
    """Affiche les statistiques des abonnés."""
    emails = charger_emails_existants()
    try:
        with file_lock(SUBSCRIBERS_CSV):
            with open(SUBSCRIBERS_CSV, "r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
    except FileNotFoundError:
        rows = []

    reels = [r for r in rows if "simulation" not in r.get("source", "")]
    simus = [r for r in rows if "simulation" in r.get("source", "")]

    print(f"\n📊 STATS ABONNÉS")
    print(f"   Total actifs    : {len(rows)}")
    print(f"   Vrais abonnés   : {len(reels)}")
    print(f"   Simulation      : {len(simus)}")

    # Sources des vrais abonnés
    if reels:
        sources = {}
        for r in reels:
            s = r.get("source", "inconnu")
            sources[s] = sources.get(s, 0) + 1
        print(f"   Sources :")
        for src, nb in sorted(sources.items(), key=lambda x: -x[1]):
            print(f"     {src}: {nb}")
    print()


# ─── POINT D'ENTRÉE ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sync abonnés Netlify → subscribers.csv")
    parser.add_argument("--dry-run",  action="store_true", help="Affiche sans modifier")
    parser.add_argument("--stats",    action="store_true", help="Affiche les stats")
    parser.add_argument("--add",      type=str,            help="Ajouter un email manuellement")
    parser.add_argument("--source",   type=str, default="manuel", help="Source (avec --add)")
    args = parser.parse_args()

    if args.stats:
        afficher_stats()
    elif args.add:
        ajouter_manuellement(args.add, args.source)
    else:
        sync_depuis_netlify(dry_run=args.dry_run)
