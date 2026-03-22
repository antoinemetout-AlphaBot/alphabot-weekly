"""
AlphaBot — Agent Directeur Adjoint 🤝
======================================
Rôle : Pilote autonome du projet AlphaBot Weekly.
       Analyse l'état complet du projet, identifie les problèmes, exécute des actions
       correctives en autonomie et rapporte quotidiennement au CEO (Antoine Metout).

Périmètre d'action (full autonome) :
  - Code Python  : corriger les agents existants, créer de nouveaux fichiers
  - HTML         : index.html, newsletter, landing page
  - Emails       : subscribers.csv, envois, templates
  - Stratégie    : KPIs, priorités, rapport CEO quotidien

Canal CEO → Agent : directives.txt  (Antoine écrit ses instructions ici)
Canal Agent → CEO : email quotidien + outputs/rapport_adjoint_YYYY-MM-DD.html
Mémoire           : data/adjoint_log.json (historique des sessions)
Backups           : data/backups/ (avant chaque modification de fichier)
"""

import os, sys, csv, json, subprocess, smtplib, shutil, ast
from datetime import datetime
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import anthropic

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, OUTPUT_DIR
from utils.activity_logger import log_event as _log

_AGENT = "Directeur Adjoint"


# ─── HELPER FUNCTION FOR REQUIRED ENV VARS ───────────────────────────────────
def _require_env(key):
    """Charge une variable d'environnement requise. Lève une erreur si elle est manquante."""
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Variable d'environnement requise manquante : {key}")
    return val


# ─── CONFIG ──────────────────────────────────────────────────────────────────
EMAIL_SENDER    = _require_env("ALPHABOT_EMAIL")
EMAIL_PASSWORD  = _require_env("ALPHABOT_PASSWORD")
EMAIL_CEO       = "antoine.metout@gmail.com"
SMTP_HOST       = "smtp.gmail.com"
SMTP_PORT       = 587

DATA_DIR        = "data"
AGENTS_DIR      = "agents"
DIRECTIVES_FILE = "directives.txt"
LOG_FILE        = os.path.join("data", "adjoint_log.json")
BACKUP_DIR      = os.path.join("data", "backups")


# ─── CLASSE PRINCIPALE ───────────────────────────────────────────────────────

class AgentAdjoint:
    """
    Agent Directeur Adjoint d'AlphaBot Weekly.

    Cycle d'une session :
      1. Scanner  → lire tous les fichiers du projet
      2. Analyser → envoyer le contexte à Claude, obtenir un plan JSON
      3. Exécuter → appliquer les actions du plan (fix_code, run_agent, etc.)
      4. Rapporter → générer un rapport HTML + envoyer par email au CEO
    """

    def __init__(self):
        self.client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.today   = datetime.now().strftime("%Y-%m-%d")
        self.now_str = datetime.now().strftime("%d/%m/%Y à %H:%M")

        Path(OUTPUT_DIR).mkdir(exist_ok=True)
        Path(DATA_DIR).mkdir(exist_ok=True)
        Path(BACKUP_DIR).mkdir(exist_ok=True)
        self._init_log()

        print("🤝 Agent Directeur Adjoint initialisé ✅")

    # ═══════════════════════════════════════════════════════════════════════════
    # 1. MÉMOIRE & LOG
    # ═══════════════════════════════════════════════════════════════════════════

    def _init_log(self):
        """Crée le fichier de log JSON s'il n'existe pas."""
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                json.dump({"sessions": []}, f, indent=2, ensure_ascii=False)

    def _lire_log(self) -> dict:
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"sessions": []}

    def _sauvegarder_log(self, session: dict):
        log = self._lire_log()
        log["sessions"].append(session)
        log["sessions"] = log["sessions"][-30:]   # 30 sessions max
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)

    def _resume_historique(self) -> str:
        """Résumé des 5 dernières sessions pour context mémoire."""
        sessions = self._lire_log().get("sessions", [])[-5:]
        if not sessions:
            return "Première session de l'agent Directeur Adjoint."
        lignes = []
        for s in sessions:
            nb  = len(s.get("actions_executees", []))
            lignes.append(f"- {s.get('date','?')} : {nb} action(s) — {s.get('resume','?')[:120]}")
        return "\n".join(lignes)

    # ═══════════════════════════════════════════════════════════════════════════
    # 2. SCAN DU PROJET
    # ═══════════════════════════════════════════════════════════════════════════

    def scanner_projet(self) -> dict:
        """
        Scanne l'intégralité du projet et retourne un snapshot complet.
        Appelé en début de chaque session.
        """
        print("  🔍 Scan du projet en cours...")
        return {
            "date":               self.now_str,
            "directives_ceo":     self._lire_directives(),
            "agents":             self._lire_agents(),
            "donnees":            self._lire_donnees(),
            "outputs_recents":    self._lister_outputs(),
            "historique_actions": self._resume_historique(),
            "problemes_connus":   self._problemes_connus(),
        }

    # ── Directives CEO ───────────────────────────────────────────────────────
    def _lire_directives(self) -> str:
        try:
            with open(DIRECTIVES_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            return "Aucune directive spécifique. Agir selon les priorités naturelles du projet."

    # ── Agents Python ────────────────────────────────────────────────────────
    def _lire_agents(self) -> dict:
        agents = {}
        try:
            fnames = [f for f in os.listdir(AGENTS_DIR)
                      if f.endswith(".py") and not f.startswith("__")]
        except FileNotFoundError:
            return {}

        for fname in fnames:
            path = os.path.join(AGENTS_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Vérification syntaxe Python
                valide, erreur = True, None
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    valide, erreur = False, str(e)

                agents[fname] = {
                    "path":           path,
                    "lignes":         len(content.splitlines()),
                    "syntaxe_valide": valide,
                    "erreur_syntaxe": erreur,
                    # Extrait pour contexte Claude (3 000 chars max)
                    "extrait":        content[:3000],
                }
            except Exception as e:
                agents[fname] = {"path": path, "erreur_lecture": str(e)}
        return agents

    # ── Données CSV ──────────────────────────────────────────────────────────
    def _lire_donnees(self) -> dict:
        def lire_csv(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return list(csv.DictReader(f))
            except Exception:
                return []

        abonnes  = lire_csv(os.path.join(DATA_DIR, "subscribers.csv"))
        send_log = lire_csv(os.path.join(DATA_DIR, "send_log.csv"))
        prospects= lire_csv(os.path.join(DATA_DIR, "prospects.csv"))
        revenues = lire_csv(os.path.join(DATA_DIR, "revenues.csv"))
        actifs   = [a for a in abonnes if a.get("actif") == "oui"]

        return {
            "nb_abonnes_actifs":   len(actifs),
            "nb_editions_envoyees": len(send_log),
            "nb_prospects":        len(prospects),
            "revenus_total":       sum(float(r.get("montant", 0)) for r in revenues),
            "derniers_envois":     send_log[-3:] if send_log else [],
        }

    # ── Outputs récents ──────────────────────────────────────────────────────
    def _lister_outputs(self) -> list:
        try:
            files = list(Path(OUTPUT_DIR).glob("*.html")) + list(Path(OUTPUT_DIR).glob("*.txt"))
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            return [{"fichier": f.name, "taille_kb": round(f.stat().st_size / 1024, 1)}
                    for f in files[:10]]
        except Exception:
            return []

    # ── Problèmes connus (base de connaissance du projet) ────────────────────
    def _problemes_connus(self) -> list:
        return [
            "Email de bienvenue pointe vers la landing page au lieu de la newsletter du jour",
            "Template EmailJS encore générique ('Welcome to [Company Name]')",
            "Formspree n'alimente pas automatiquement subscribers.csv",
            "Newsletter preview dans index.html pointe vers une date fixe",
            "Adresse email dédiée alphabotweekly@gmail.com impossible à créer pour l'instant",
            "Scheduled tasks dépendent de l'ordinateur d'Antoine allumé",
        ]

    # ═══════════════════════════════════════════════════════════════════════════
    # 3. ANALYSE & PLANIFICATION (Claude)
    # ═══════════════════════════════════════════════════════════════════════════

    def analyser_et_planifier(self, etat: dict) -> dict:
        """
        Envoie le snapshot du projet à Claude.
        Retourne un plan d'actions structuré en JSON.
        """
        print("  🧠 Analyse du projet par Claude...")

        donnees = etat["donnees"]

        # Résumé des agents
        agents_resume = ""
        for fname, info in etat["agents"].items():
            status = "✅" if info.get("syntaxe_valide", True) else "❌ ERREUR SYNTAXE"
            agents_resume += f"- {fname} ({info.get('lignes','?')} lignes) {status}\n"
            if info.get("erreur_syntaxe"):
                agents_resume += f"  └ ERREUR: {info['erreur_syntaxe']}\n"

        problemes_str = "\n".join(f"- {p}" for p in etat["problemes_connus"])

        system = """Tu es le Directeur Adjoint IA d'AlphaBot Weekly, newsletter financière 100% automatisée.
Tu travailles en autonomie totale pour faire avancer le projet sous la direction du CEO Antoine Metout.
Tu es pragmatique, orienté résultats. Tu analyses, tu priorises, tu agis.
Tu génères des plans d'action concrets et exécutables en JSON strict."""

        user = f"""SNAPSHOT DU PROJET — {etat['date']}

══════════ DIRECTIVES CEO ══════════
{etat['directives_ceo']}

══════════ DONNÉES ENTREPRISE ══════════
- Abonnés actifs          : {donnees['nb_abonnes_actifs']}
- Éditions envoyées       : {donnees['nb_editions_envoyees']}
- Revenus totaux          : {donnees['revenus_total']}€
- Prospects pipeline      : {donnees['nb_prospects']}

══════════ ÉTAT DES AGENTS PYTHON ══════════
{agents_resume}

══════════ PROBLÈMES CONNUS ══════════
{problemes_str}

══════════ HISTORIQUE DES SESSIONS ══════════
{etat['historique_actions']}

══════════ OUTPUTS RÉCENTS ══════════
{json.dumps(etat['outputs_recents'], ensure_ascii=False)}

══════════ INSTRUCTION ══════════
Génère un plan d'action JSON pour cette session quotidienne.
Priorise 3 à 5 actions maximum. Sois très précis.

TYPES D'ACTIONS DISPONIBLES :
  "run_agent"         → exécuter un agent Python (commande shell exacte)
  "fix_code"          → corriger un fichier Python/HTML (old_string / new_string EXACTS)
  "update_html"       → modifier un fichier HTML (old_string / new_string EXACTS)
  "note_action"       → action manuelle à faire par Antoine (l'agent ne peut pas le faire)

RÈGLES IMPORTANTES :
- Pour fix_code / update_html : old_string doit être un extrait EXACT du fichier (copiable)
- Ne refais pas une action réussie lors de la session précédente
- run_agent doit utiliser --demo si la vraie API n'est pas disponible en dehors du sandbox
- Chaque action doit avoir une valeur ajoutée concrète

Réponds UNIQUEMENT avec un JSON valide (pas de texte autour) :
{{
  "analyse": "État du projet en 2-3 phrases synthétiques",
  "priorites_semaine": ["priorité 1", "priorité 2", "priorité 3"],
  "actions": [
    {{
      "type": "run_agent|fix_code|update_html|note_action",
      "description": "Ce que fait cette action",
      "priorite": "haute|moyenne|basse",
      "fichier": "chemin/relatif/au/projet.py",
      "old_string": "extrait exact à remplacer (pour fix_code/update_html)",
      "new_string": "nouveau code (pour fix_code/update_html)",
      "commande": "python main.py --demo (pour run_agent)",
      "message_antoine": "Instruction précise pour Antoine (pour note_action)"
    }}
  ],
  "message_ceo": "Message du DA à Antoine : bilan, actions du jour, cap. Inspirant, direct, 3-4 phrases.",
  "kpis_cibles": {{
    "abonnes_actuel": {donnees['nb_abonnes_actifs']},
    "abonnes_objectif": 1000,
    "editions_actuel": {donnees['nb_editions_envoyees']},
    "editions_objectif": 50,
    "revenus_actuel": {donnees['revenus_total']},
    "revenus_objectif": 1000
  }}
}}"""

        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=3000,
            messages=[{"role": "user", "content": user}],
            system=system,
        )
        texte = response.content[0].text.strip()

        # Extraction du JSON (robuste)
        try:
            debut = texte.find("{")
            fin   = texte.rfind("}") + 1
            if debut != -1 and fin > debut:
                return json.loads(texte[debut:fin])
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback
        print("  ⚠️  Impossible de parser le plan JSON — mode dégradé")
        return {
            "analyse":          "Erreur de parsing du plan. Mode dégradé activé.",
            "priorites_semaine":["Corriger le parsing JSON de l'agent Directeur Adjoint"],
            "actions":          [],
            "message_ceo":      "Session en mode dégradé — le plan JSON n'a pas pu être parsé.",
            "kpis_cibles":      {"abonnes_actuel": donnees["nb_abonnes_actifs"],
                                 "abonnes_objectif": 1000,
                                 "editions_actuel":  donnees["nb_editions_envoyees"],
                                 "editions_objectif": 50,
                                 "revenus_actuel":   donnees["revenus_total"],
                                 "revenus_objectif": 1000},
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # 4. EXÉCUTION DES ACTIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def executer_actions(self, plan: dict, etat: dict) -> list:
        """
        Exécute chaque action du plan et retourne la liste des résultats.
        """
        actions = plan.get("actions", [])
        print(f"\n  ⚡ Exécution de {len(actions)} action(s)...")
        resultats = []

        for i, action in enumerate(actions, 1):
            atype = action.get("type", "")
            desc  = action.get("description", "Action sans description")
            print(f"\n  [{i}/{len(actions)}] {desc}")

            res = {"action": desc, "type": atype, "status": "pending", "detail": ""}

            try:
                if atype == "run_agent":
                    r = self._executer_commande(action.get("commande", ""))
                    res["status"] = "success" if r["returncode"] == 0 else "error"
                    res["detail"] = (r["stdout"] or r["stderr"])[:400]

                elif atype in ("fix_code", "update_html"):
                    r = self._modifier_fichier(
                        action.get("fichier", ""),
                        action.get("old_string", ""),
                        action.get("new_string", ""),
                    )
                    res["status"] = "success" if r["success"] else "error"
                    res["detail"] = r.get("message", "")

                elif atype == "note_action":
                    msg = action.get("message_antoine", desc)
                    res["status"] = "noted"
                    res["detail"] = msg
                    print(f"     📌 À faire manuellement : {msg}")

                else:
                    res["status"] = "skipped"
                    res["detail"] = f"Type inconnu : {atype}"

            except Exception as e:
                res["status"] = "error"
                res["detail"] = f"Exception : {e}"
                print(f"     ❌ Erreur inattendue : {e}")

            icons = {"success": "✅", "error": "❌", "noted": "📌", "skipped": "⏭️", "pending": "⏳"}
            print(f"     {icons.get(res['status'], '?')} {res['status'].upper()} — {res['detail'][:100]}")
            resultats.append(res)

        return resultats

    # ── Helpers exécution ────────────────────────────────────────────────────

    def _executer_commande(self, commande: str, timeout: int = 120) -> dict:
        """Exécute une commande shell depuis le répertoire du projet."""
        try:
            r = subprocess.run(
                commande, shell=True, capture_output=True,
                text=True, timeout=timeout,
                cwd=os.getcwd(),
            )
            return {"returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr}
        except subprocess.TimeoutExpired:
            return {"returncode": -1, "stdout": "", "stderr": "Timeout (120s)"}
        except Exception as e:
            return {"returncode": -1, "stdout": "", "stderr": str(e)}

    def _modifier_fichier(self, chemin: str, old_string: str, new_string: str) -> dict:
        """
        Remplace old_string par new_string dans un fichier.
        Effectue un backup automatique avant toute modification.
        Vérifie la syntaxe Python si applicable.
        """
        if not chemin:
            return {"success": False, "message": "Chemin de fichier manquant"}
        if not old_string:
            return {"success": False, "message": "old_string manquant (rien à remplacer)"}

        try:
            with open(chemin, "r", encoding="utf-8") as f:
                contenu = f.read()
        except FileNotFoundError:
            return {"success": False, "message": f"Fichier introuvable : {chemin}"}

        if old_string not in contenu:
            return {"success": False, "message": f"old_string introuvable dans {chemin}"}

        # Backup
        bak = os.path.join(BACKUP_DIR, f"{os.path.basename(chemin)}.{self.today}.bak")
        shutil.copy2(chemin, bak)

        nouveau = contenu.replace(old_string, new_string, 1)

        # Validation syntaxe Python
        if chemin.endswith(".py"):
            try:
                ast.parse(nouveau)
            except SyntaxError as e:
                return {"success": False,
                        "message": f"Syntaxe invalide après modification : {e}"}

        with open(chemin, "w", encoding="utf-8") as f:
            f.write(nouveau)

        return {"success": True, "message": f"✅ {chemin} modifié (backup : {bak})"}

    # ═══════════════════════════════════════════════════════════════════════════
    # 5. RAPPORT CEO (HTML + Email)
    # ═══════════════════════════════════════════════════════════════════════════

    def generer_rapport_ceo(self, etat: dict, plan: dict, actions: list) -> str:
        """Génère le rapport HTML quotidien du Directeur Adjoint."""
        print("\n  📊 Génération du rapport CEO...")

        donnees   = etat["donnees"]
        kpis      = plan.get("kpis_cibles", {})
        ok_list   = [a for a in actions if a["status"] == "success"]
        err_list  = [a for a in actions if a["status"] == "error"]
        note_list = [a for a in actions if a["status"] == "noted"]

        def pct(actuel, objectif):
            return min(round(actuel / max(objectif, 1) * 100), 100)

        pct_ab  = pct(donnees["nb_abonnes_actifs"],     kpis.get("abonnes_objectif", 1000))
        pct_ed  = pct(donnees["nb_editions_envoyees"],  kpis.get("editions_objectif", 50))
        pct_rev = pct(int(donnees["revenus_total"]),    kpis.get("revenus_objectif", 1000))

        # ── Blocs HTML ────────────────────────────────────────────────────────
        def action_row(a):
            icones  = {"success": "✅", "error": "❌", "noted": "📌", "skipped": "⏭️"}
            couleurs= {"success": "#22c55e", "error": "#ef4444", "noted": "#f59e0b", "skipped": "#64748b"}
            ic = icones.get(a["status"], "•")
            cl = couleurs.get(a["status"], "#94a3b8")
            detail = a.get("detail", "")[:150]
            return f"""
            <div style="display:flex;align-items:flex-start;gap:10px;padding:10px 14px;
                        background:rgba(255,255,255,.03);border-radius:8px;margin-bottom:6px;
                        border-left:3px solid {cl};">
              <span style="font-size:16px;flex-shrink:0;">{ic}</span>
              <div>
                <div style="color:#e2e8f0;font-size:13px;font-weight:600;">{a['action']}</div>
                {f'<div style="color:#64748b;font-size:11px;margin-top:2px;">{detail}</div>' if detail else ''}
              </div>
            </div>"""

        actions_html = "".join(action_row(a) for a in actions) if actions else \
            '<div style="color:#64748b;font-size:13px;text-align:center;padding:20px;">Aucune action cette session</div>'

        notes_html = ""
        if note_list:
            notes_html = '<div style="margin-top:20px;padding:16px;background:rgba(245,158,11,.06);border:1px solid rgba(245,158,11,.2);border-radius:10px;">'
            notes_html += '<div style="font-size:11px;letter-spacing:2px;color:#f59e0b;font-weight:700;margin-bottom:10px;">📌 ACTIONS MANUELLES POUR TOI, ANTOINE</div>'
            for n in note_list:
                notes_html += f'<div style="color:#fcd34d;font-size:13px;margin-bottom:6px;">→ {n["detail"]}</div>'
            notes_html += '</div>'

        prios_html = "".join(
            f'<div style="padding:8px 14px;background:rgba(59,130,246,.06);border:1px solid rgba(59,130,246,.18);'
            f'border-radius:8px;margin-bottom:6px;color:#93c5fd;font-size:13px;">→ {p}</div>'
            for p in plan.get("priorites_semaine", [])
        )

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AlphaBot — Rapport DA {self.today}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700;800&display=swap" rel="stylesheet">
</head>
<body style="margin:0;background:#04091a;font-family:'Inter',sans-serif;padding:24px 12px 60px;">
<div style="max-width:700px;margin:0 auto;">

  <!-- ── HEADER ─────────────────────────────────────────────────────── -->
  <div style="background:linear-gradient(135deg,rgba(168,85,247,.12),rgba(59,130,246,.08));
              border:1px solid rgba(168,85,247,.25);border-radius:16px;padding:28px 24px;
              margin-bottom:18px;text-align:center;">
    <div style="font-size:10px;letter-spacing:3px;color:#c084fc;font-weight:700;margin-bottom:8px;">
      RAPPORT QUOTIDIEN — DIRECTEUR ADJOINT IA
    </div>
    <div style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:900;
                background:linear-gradient(135deg,#fff,#c084fc,#22d3ee);
                -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;">
      🤝 AlphaBot Weekly
    </div>
    <div style="color:#94a3b8;font-size:13px;margin-top:4px;">{self.now_str}</div>
    <div style="margin-top:16px;display:flex;justify-content:center;gap:8px;flex-wrap:wrap;">
      <span style="background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.25);
                   color:#22c55e;font-size:11px;font-weight:700;padding:4px 12px;border-radius:20px;">
        ✅ {len(ok_list)} action(s) réussie(s)
      </span>
      <span style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.25);
                   color:#f87171;font-size:11px;font-weight:700;padding:4px 12px;border-radius:20px;">
        ❌ {len(err_list)} erreur(s)
      </span>
      <span style="background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.25);
                   color:#f59e0b;font-size:11px;font-weight:700;padding:4px 12px;border-radius:20px;">
        📌 {len(note_list)} action(s) pour toi
      </span>
    </div>
  </div>

  <!-- ── MESSAGE DA ──────────────────────────────────────────────────── -->
  <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
              border-radius:14px;padding:22px 24px;margin-bottom:14px;">
    <div style="font-size:10px;letter-spacing:2px;color:#64748b;font-weight:700;margin-bottom:12px;">
      💬 MESSAGE DE TON DIRECTEUR ADJOINT
    </div>
    <p style="color:#cbd5e1;font-size:14px;line-height:1.8;margin:0;">
      {plan.get('message_ceo', '—')}
    </p>
  </div>

  <!-- ── KPIs / PROGRESSION ──────────────────────────────────────────── -->
  <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
              border-radius:14px;padding:22px 24px;margin-bottom:14px;">
    <div style="font-size:10px;letter-spacing:2px;color:#64748b;font-weight:700;margin-bottom:16px;">
      📊 PROGRESSION VERS LES OBJECTIFS
    </div>

    <div style="margin-bottom:14px;">
      <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
        <span style="color:#e2e8f0;font-size:13px;">👥 Abonnés actifs</span>
        <span style="color:#22c55e;font-size:13px;font-weight:700;">{donnees['nb_abonnes_actifs']} / 1 000</span>
      </div>
      <div style="height:6px;background:rgba(255,255,255,.06);border-radius:3px;">
        <div style="width:{pct_ab}%;height:100%;background:#22c55e;border-radius:3px;"></div>
      </div>
    </div>

    <div style="margin-bottom:14px;">
      <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
        <span style="color:#e2e8f0;font-size:13px;">📧 Éditions envoyées</span>
        <span style="color:#3b82f6;font-size:13px;font-weight:700;">{donnees['nb_editions_envoyees']} / 50</span>
      </div>
      <div style="height:6px;background:rgba(255,255,255,.06);border-radius:3px;">
        <div style="width:{pct_ed}%;height:100%;background:#3b82f6;border-radius:3px;"></div>
      </div>
    </div>

    <div>
      <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
        <span style="color:#e2e8f0;font-size:13px;">💰 Revenus mensuels</span>
        <span style="color:#f5c842;font-size:13px;font-weight:700;">{int(donnees['revenus_total'])}€ / 1 000€</span>
      </div>
      <div style="height:6px;background:rgba(255,255,255,.06);border-radius:3px;">
        <div style="width:{pct_rev}%;height:100%;background:#f5c842;border-radius:3px;"></div>
      </div>
    </div>
  </div>

  <!-- ── ACTIONS EFFECTUÉES ──────────────────────────────────────────── -->
  <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
              border-radius:14px;padding:22px 24px;margin-bottom:14px;">
    <div style="font-size:10px;letter-spacing:2px;color:#64748b;font-weight:700;margin-bottom:14px;">
      ⚡ ACTIONS DE CETTE SESSION
    </div>
    {actions_html}
    {notes_html}
  </div>

  <!-- ── PRIORITÉS SEMAINE ────────────────────────────────────────────── -->
  <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
              border-radius:14px;padding:22px 24px;margin-bottom:14px;">
    <div style="font-size:10px;letter-spacing:2px;color:#64748b;font-weight:700;margin-bottom:14px;">
      🎯 PRIORITÉS DE LA SEMAINE
    </div>
    {prios_html if prios_html else '<div style="color:#64748b;font-size:13px;">Aucune priorité définie</div>'}
  </div>

  <!-- ── SUPERVISION ÉQUIPE ─────────────────────────────────────────── -->
  {self._html_supervision(etat.get('supervision', {}))}

  <!-- ── ANALYSE ─────────────────────────────────────────────────────── -->
  <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
              border-radius:14px;padding:22px 24px;margin-bottom:14px;">
    <div style="font-size:10px;letter-spacing:2px;color:#64748b;font-weight:700;margin-bottom:12px;">
      🔍 ANALYSE DE L'ÉTAT DU PROJET
    </div>
    <p style="color:#94a3b8;font-size:13px;line-height:1.8;margin:0;">
      {plan.get('analyse', '—')}
    </p>
  </div>

  <!-- ── FOOTER ──────────────────────────────────────────────────────── -->
  <div style="text-align:center;padding:20px 0 0;font-size:11px;color:#334155;line-height:1.8;">
    Rapport généré automatiquement par l'Agent Directeur Adjoint · AlphaBot Weekly<br>
    <strong style="color:#475569;">Pour donner tes instructions :</strong>
    édite le fichier <code style="color:#64748b;">directives.txt</code> dans le dossier Alphabot<br>
    Antoine Metout — CEO &amp; Fondateur
  </div>

</div>
</body>
</html>"""

        nom    = f"rapport_adjoint_{self.today}.html"
        chemin = os.path.join(OUTPUT_DIR, nom)
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  ✅ Rapport sauvegardé : {chemin}")
        return chemin

    def envoyer_rapport_email(self, chemin_rapport: str, plan: dict, actions: list) -> bool:
        """Envoie le rapport HTML par email à Antoine."""
        print("  📧 Envoi du rapport par email...")
        try:
            with open(chemin_rapport, "r", encoding="utf-8") as f:
                html_content = f.read()
        except Exception:
            html_content = "<p>Rapport non disponible.</p>"

        nb_ok    = len([a for a in actions if a["status"] == "success"])
        nb_notes = len([a for a in actions if a["status"] == "noted"])
        sujet    = (f"🤝 DA AlphaBot — {self.now_str} | "
                    f"{nb_ok} action(s) réussie(s) | {nb_notes} à faire")

        texte = (
            f"Rapport Directeur Adjoint AlphaBot Weekly — {self.now_str}\n\n"
            f"Actions réussies    : {nb_ok}\n"
            f"Actions pour toi   : {nb_notes}\n\n"
            f"Analyse : {plan.get('analyse', '—')}\n\n"
            f"Message : {plan.get('message_ceo', '—')}\n\n"
            "Pour donner des instructions : édite directives.txt dans le dossier Alphabot.\n"
            "— Ton Directeur Adjoint IA"
        )

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = sujet
            msg["From"]    = f"AlphaBot DA <{EMAIL_SENDER}>"
            msg["To"]      = EMAIL_CEO
            msg.attach(MIMEText(texte, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)

            print(f"  ✅ Email rapport envoyé à {EMAIL_CEO}")
            return True
        except Exception as e:
            print(f"  ❌ Erreur envoi email : {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # 5b. SUPERVISION DE L'ÉQUIPE (HIÉRARCHIE)
    # ═══════════════════════════════════════════════════════════════════════════

    # Définition des KPIs attendus de chaque agent
    AGENTS_KPI = {
        "agent_veille.py": {
            "nom":       "Agent Veille 📡",
            "mission":   "Collecter les données marché chaque matin (lun-ven)",
            "check":     "frequence_outputs",
            "pattern":   None,   # pas d'output fichier direct
            "max_jours_sans_run": 1,
        },
        "agent_analyste.py": {
            "nom":       "Agent Analyste 🧠",
            "mission":   "Produire des analyses IA (lun-ven)",
            "check":     "frequence_outputs",
            "pattern":   None,
            "max_jours_sans_run": 1,
        },
        "agent_redacteur.py": {
            "nom":       "Agent Rédacteur ✍️",
            "mission":   "Générer la newsletter HTML quotidienne (lun-ven)",
            "check":     "fichier_output",
            "pattern":   "alphabot_newsletter_*.html",
            "max_jours_sans_run": 1,
        },
        "agent_growth.py": {
            "nom":       "Agent Growth 📈",
            "mission":   "Envoyer la newsletter à tous les abonnés actifs (lun-ven)",
            "check":     "csv_data",
            "csv_path":  os.path.join("data", "send_log.csv"),
            "max_jours_sans_run": 1,
        },
        "agent_growth_booster.py": {
            "nom":       "Agent Growth Booster 🚀",
            "mission":   "Générer stratégies croissance + objectif +5 abonnés/semaine",
            "check":     "fichier_output",
            "pattern":   "growth_strategy_*.html",
            "max_jours_sans_run": 7,
        },
        "agent_commercial.py": {
            "nom":       "Agent Commercial 💼",
            "mission":   "Contacter 2 nouveaux prospects par semaine",
            "check":     "csv_data",
            "csv_path":  os.path.join("data", "prospects.csv"),
            "max_jours_sans_run": 7,
        },
        "agent_analytics.py": {
            "nom":       "Agent Analytics 📊",
            "mission":   "Générer le dashboard KPIs chaque semaine",
            "check":     "fichier_output",
            "pattern":   "alphabot_dashboard_*.html",
            "max_jours_sans_run": 7,
        },
        "agent_cfo.py": {
            "nom":       "Agent CFO 💰",
            "mission":   "Produire le rapport financier mensuel",
            "check":     "fichier_output",
            "pattern":   "cfo_rapport_*.html",
            "max_jours_sans_run": 30,
        },
        "agent_ceo_brief.py": {
            "nom":       "Agent CEO Brief 👔",
            "mission":   "Préparer le brief hebdomadaire du lundi",
            "check":     "fichier_output",
            "pattern":   "ceo_brief_*.html",
            "max_jours_sans_run": 7,
        },
    }

    def superviser_equipe(self) -> dict:
        """
        Vérifie la conformité de chaque agent par rapport à ses objectifs.
        Retourne un rapport de supervision avec les agents en retard et les actions correctives.
        """
        import glob
        print("  👔 Supervision de l'équipe...")
        rapport = {"agents_conformes": [], "agents_en_retard": [], "actions_correctives": []}

        for agent_file, kpi in self.AGENTS_KPI.items():
            statut = self._verifier_agent(agent_file, kpi)
            if statut["conforme"]:
                rapport["agents_conformes"].append({
                    "agent": kpi["nom"], "detail": statut.get("detail", "OK")
                })
            else:
                action_corr = self._generer_action_corrective(agent_file, kpi, statut)
                rapport["agents_en_retard"].append({
                    "agent":   kpi["nom"],
                    "mission": kpi["mission"],
                    "probleme": statut.get("probleme", "Inconnu"),
                    "action":  action_corr,
                })
                rapport["actions_correctives"].append(action_corr)

        nb_ok  = len(rapport["agents_conformes"])
        nb_ret = len(rapport["agents_en_retard"])
        print(f"  ✅ {nb_ok} agent(s) conforme(s) | ⚠️  {nb_ret} en retard")
        return rapport

    def _verifier_agent(self, agent_file: str, kpi: dict) -> dict:
        """Vérifie si un agent a rempli ses obligations récemment."""
        import glob
        check = kpi.get("check", "")
        max_j = kpi.get("max_jours_sans_run", 7)

        if check == "fichier_output":
            pattern = kpi.get("pattern", "")
            fichiers = sorted(glob.glob(os.path.join(OUTPUT_DIR, pattern)),
                              key=os.path.getmtime, reverse=True)
            if not fichiers:
                return {"conforme": False, "probleme": f"Aucun output trouvé ({pattern})"}
            dernier = fichiers[0]
            age_jours = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(dernier))).days
            if age_jours > max_j:
                return {"conforme": False, "probleme": f"Dernier output : il y a {age_jours} jour(s) (max {max_j}j)"}
            return {"conforme": True, "detail": f"Dernier output : il y a {age_jours}j"}

        elif check == "csv_data":
            csv_path = kpi.get("csv_path", "")
            try:
                with open(csv_path, "r", encoding="utf-8") as f:
                    rows = list(csv.DictReader(f))
                if not rows:
                    return {"conforme": False, "probleme": "CSV vide — aucune activité enregistrée"}
                # Chercher la dernière entrée avec une date
                dates = []
                for r in rows:
                    for col in ["date", "date_inscription", "date_dernier_contact"]:
                        if r.get(col):
                            try:
                                dates.append(datetime.strptime(r[col][:10], "%Y-%m-%d"))
                            except ValueError:
                                pass
                if dates:
                    age_j = (datetime.now() - max(dates)).days
                    if age_j > max_j:
                        return {"conforme": False, "probleme": f"Dernière activité : il y a {age_j}j (max {max_j}j)"}
                return {"conforme": True, "detail": f"{len(rows)} entrée(s) dans le CSV"}
            except FileNotFoundError:
                return {"conforme": False, "probleme": "Fichier CSV introuvable"}

        # Vérification de base : le fichier agent existe
        path = os.path.join(AGENTS_DIR, agent_file)
        if not os.path.exists(path):
            return {"conforme": False, "probleme": "Fichier agent introuvable"}
        return {"conforme": True, "detail": "Fichier présent (vérification légère)"}

    def _generer_action_corrective(self, agent_file: str, kpi: dict, statut: dict) -> dict:
        """Génère une action corrective pour un agent en retard."""
        # Mapper agent → commande main.py
        commandes = {
            "agent_veille.py":          "python main.py --veille",
            "agent_analyste.py":        "python main.py --demo",
            "agent_redacteur.py":       "python main.py --demo",
            "agent_growth.py":          "python main.py --growth",
            "agent_growth_booster.py":  "python main.py --booster",
            "agent_commercial.py":      "python main.py --commercial",
            "agent_analytics.py":       "python main.py --analytics",
            "agent_cfo.py":             "python main.py --cfo",
            "agent_ceo_brief.py":       "python main.py --ceo-brief",
        }
        commande = commandes.get(agent_file, f"python agents/{agent_file}")
        return {
            "type":        "run_agent",
            "description": f"[SUPERVISION] Relancer {kpi['nom']} — {statut.get('probleme','')}",
            "commande":    commande,
            "priorite":    "haute",
            "agent":       kpi["nom"],
        }

    def _html_supervision(self, supervision: dict) -> str:
        """Génère le bloc HTML de supervision pour le rapport CEO."""
        conformes = supervision.get("agents_conformes", [])
        retards   = supervision.get("agents_en_retard", [])

        lignes_ok = "".join(
            f'<div style="padding:6px 12px;background:rgba(34,197,94,.05);border-radius:6px;'
            f'margin-bottom:4px;color:#86efac;font-size:12px;">'
            f'✅ <strong>{a["agent"]}</strong> — {a["detail"]}</div>'
            for a in conformes
        )
        lignes_ret = "".join(
            f'<div style="padding:8px 12px;background:rgba(239,68,68,.05);border:1px solid rgba(239,68,68,.15);'
            f'border-radius:6px;margin-bottom:6px;">'
            f'<div style="color:#fca5a5;font-size:12px;font-weight:600;">⚠️  {a["agent"]}</div>'
            f'<div style="color:#64748b;font-size:11px;">{a["probleme"]}</div>'
            f'<div style="color:#f59e0b;font-size:11px;margin-top:2px;">→ Action : {a["action"].get("commande","?")}</div>'
            f'</div>'
            for a in retards
        )

        return f"""
    <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
                border-radius:14px;padding:22px 24px;margin-bottom:14px;">
      <div style="font-size:10px;letter-spacing:2px;color:#64748b;font-weight:700;margin-bottom:14px;">
        👔 SUPERVISION ÉQUIPE — HIÉRARCHIE DA
      </div>
      <div style="font-size:12px;color:#94a3b8;margin-bottom:12px;">
        CEO (Antoine) → Directeur Adjoint → {len(conformes)+len(retards)} agents
      </div>
      {lignes_ok}
      {lignes_ret if lignes_ret else ''}
    </div>"""

    # ═══════════════════════════════════════════════════════════════════════════
    # 6. ORCHESTRATEUR PRINCIPAL
    # ═══════════════════════════════════════════════════════════════════════════

    def run(self, envoyer_email: bool = True) -> dict:
        """
        Lance le cycle complet du Directeur Adjoint :
          1. Scan       → snapshot complet du projet
          2. Analyser   → plan d'action Claude (JSON)
          3. Exécuter   → appliquer les actions
          4. Rapporter  → HTML + email CEO
        """
        debut = datetime.now()
        print("\n╔══════════════════════════════════════════════════════╗")
        print("║  🤝  AlphaBot — Agent Directeur Adjoint              ║")
        print(f"║  Démarrage : {debut.strftime('%d/%m/%Y à %H:%M:%S'):<39}║")
        print("╚══════════════════════════════════════════════════════╝")
        _log(_AGENT, "start", f"Cycle quotidien démarré — {debut.strftime('%d/%m/%Y à %H:%M')}")

        # 1 — Scan
        print("\n[1/5] 🔍 Scan du projet...")
        _log(_AGENT, "progress", "Scan du projet en cours...")
        etat = self.scanner_projet()
        print(f"   Agents Python    : {len(etat['agents'])}")
        print(f"   Abonnés actifs   : {etat['donnees']['nb_abonnes_actifs']}")
        print(f"   Outputs récents  : {len(etat['outputs_recents'])}")
        _log(_AGENT, "info", f"Scan terminé — {len(etat['agents'])} agents | {etat['donnees']['nb_abonnes_actifs']} abonnés")

        # 2 — Supervision de l'équipe (hiérarchie)
        print("\n[2/5] 👔 Supervision de l'équipe...")
        _log(_AGENT, "progress", "Supervision de l'équipe en cours...")
        supervision = self.superviser_equipe()
        etat["supervision"] = supervision
        nb_ret = len(supervision.get("agents_en_retard", []))
        if nb_ret > 0:
            retards = [a["agent"] for a in supervision.get("agents_en_retard", [])]
            _log(_AGENT, "warning", f"{nb_ret} agent(s) en retard sur leurs objectifs", {"agents": retards})
        else:
            _log(_AGENT, "success", f"Tous les agents sont conformes à leurs objectifs")

        # 3 — Analyse & Plan
        print("\n[3/5] 🧠 Analyse & Planification Claude...")
        _log(_AGENT, "progress", "Analyse du projet avec Claude IA en cours...")
        plan = self.analyser_et_planifier(etat)
        actions_corr = supervision.get("actions_correctives", [])
        plan.setdefault("actions", [])
        plan["actions"] = actions_corr + plan["actions"]
        print(f"   Analyse : {plan.get('analyse','?')[:80]}...")
        print(f"   Actions planifiées : {len(plan.get('actions', []))} (dont {len(actions_corr)} correctives)")
        _log(_AGENT, "info", f"Plan d'action généré — {len(plan.get('actions',[]))} action(s)", {"nb_actions": len(plan.get("actions",[]))})

        # 4 — Exécution
        print("\n[4/5] ⚡ Exécution des actions...")
        _log(_AGENT, "progress", f"Exécution de {len(plan.get('actions',[]))} action(s) en cours...")
        actions = self.executer_actions(plan, etat)
        nb_ok  = len([a for a in actions if a["status"] == "success"])
        nb_err = len([a for a in actions if a["status"] == "error"])
        print(f"\n   Résultat : {nb_ok} succès | {nb_err} erreur(s)")
        _log(_AGENT, "success" if nb_err == 0 else "warning",
             f"Exécution terminée — {nb_ok} succès, {nb_err} erreur(s)", {"ok": nb_ok, "errors": nb_err})

        # 5 — Rapport
        print("\n[5/5] 📊 Rapport CEO...")
        _log(_AGENT, "progress", "Génération du rapport CEO...")
        chemin = self.generer_rapport_ceo(etat, plan, actions)
        if envoyer_email:
            self.envoyer_rapport_email(chemin, plan, actions)
            _log(_AGENT, "success", f"Rapport quotidien envoyé à {EMAIL_CEO}")

        # Log de session
        duree = (datetime.now() - debut).seconds
        self._sauvegarder_log({
            "date":              self.now_str,
            "duree_sec":         duree,
            "nb_actions":        len(actions),
            "actions_executees": [{"action": a["action"], "status": a["status"]} for a in actions],
            "resume":            plan.get("analyse", "?")[:200],
        })

        print(f"\n╔══════════════════════════════════════════════════════╗")
        print(f"║  ✅  Session terminée en {duree}s")
        print(f"║  Actions : {nb_ok} réussies | {nb_err} erreurs")
        print(f"║  Rapport : {chemin}")
        print(f"╚══════════════════════════════════════════════════════╝\n")

        return {"success": True, "rapport": chemin, "actions": actions, "plan": plan}


# ─── POINT D'ENTRÉE STANDALONE ────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Agent Directeur Adjoint AlphaBot")
    parser.add_argument("--no-email", action="store_true", help="Ne pas envoyer l'email rapport")
    args = parser.parse_args()

    agent = AgentAdjoint()
    agent.run(envoyer_email=not args.no_email)
