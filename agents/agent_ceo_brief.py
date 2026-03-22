"""
AlphaBot — Agent CEO Brief 👔
Rôle : Organiser la réunion hebdomadaire entre Antoine (CEO) et tous les agents.
       Chaque agent présente son bilan de la semaine, ses résultats et ses recommandations.
       Le brief est envoyé par email au CEO chaque lundi matin à 8h00.

Format : Compte-rendu de réunion de direction — style moderne startup.
"""

import os, csv, json
from datetime import datetime, timedelta
from pathlib import Path

import anthropic

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, NEWSLETTER_NAME, OUTPUT_DIR

DATA_DIR = "data"


class AgentCEOBrief:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        Path(OUTPUT_DIR).mkdir(exist_ok=True)
        print("👔 Agent CEO Brief initialisé ✅")

    # ─── COLLECTE DONNÉES TOUS AGENTS ────────────────────────────────────────

    def _lire_csv(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        except:
            return []

    def _collecter_etat_entreprise(self) -> dict:
        """Agrège l'état de santé de tous les agents."""
        abonnes   = self._lire_csv(os.path.join(DATA_DIR, "subscribers.csv"))
        send_log  = self._lire_csv(os.path.join(DATA_DIR, "send_log.csv"))
        prospects = self._lire_csv(os.path.join(DATA_DIR, "prospects.csv"))
        revenues  = self._lire_csv(os.path.join(DATA_DIR, "revenues.csv"))

        actifs = [a for a in abonnes if a.get("actif") == "oui"]

        def jours(d):
            try: return (datetime.now() - datetime.strptime(d[:10], "%Y-%m-%d")).days
            except: return 9999

        nouveaux_7j = [a for a in actifs if jours(a.get("date_inscription","")) <= 7]
        rev_30j     = sum(float(r.get("montant",0)) for r in revenues if jours(r.get("date","")) <= 30)
        nb_editions = len(send_log)
        envoyes_7j  = sum(int(r.get("nb_envoyes",0)) for r in send_log if jours(r.get("date","")) <= 7)

        par_statut_comm = {}
        for p in prospects:
            s = p.get("statut","?")
            par_statut_comm[s] = par_statut_comm.get(s,0)+1

        return {
            "semaine":          datetime.now().strftime("Semaine %W — %d %B %Y"),
            "nb_abonnes":       len(actifs),
            "nouveaux_7j":      len(nouveaux_7j),
            "nb_editions":      nb_editions,
            "envoyes_7j":       envoyes_7j,
            "rev_30j":          round(rev_30j,2),
            "prospects_total":  len(prospects),
            "partenaires":      par_statut_comm.get("partenaire",0),
            "contactes":        par_statut_comm.get("contacte",0),
            "en_discussion":    par_statut_comm.get("en_discussion",0),
        }

    # ─── GÉNÉRATION DU BRIEF PAR CLAUDE ──────────────────────────────────────

    def generer_brief(self) -> str:
        """
        Génère le compte-rendu de la réunion hebdomadaire.
        Claude joue le rôle de chaque agent qui s'adresse au CEO Antoine.
        """
        print("  🧠 Génération du CEO Brief par Claude...")
        etat = self._collecter_etat_entreprise()

        system = """Tu es le coordinateur d'AlphaBot Weekly, une newsletter financière IA.
Tu rédiges le compte-rendu de la réunion hebdomadaire de direction pour Antoine Metout, CEO et fondateur.
Chaque agent de l'entreprise prend la parole tour à tour pour faire son point.
Style : professionnel mais humain, direct, avec des données réelles, des émojis discrets.
Tu parles à Antoine comme ses agents lui parleraient : avec respect, franchise et ambition partagée."""

        user = f"""Génère le compte-rendu de la réunion hebdomadaire d'AlphaBot Weekly pour Antoine Metout, CEO.

DONNÉES RÉELLES DE L'ENTREPRISE cette semaine ({etat['semaine']}) :
- Abonnés actifs : {etat['nb_abonnes']}
- Nouveaux abonnés (7j) : +{etat['nouveaux_7j']}
- Éditions publiées au total : {etat['nb_editions']}
- Emails envoyés cette semaine : {etat['envoyes_7j']}
- Revenus (30 derniers jours) : {etat['rev_30j']}€
- Pipeline commercial : {etat['prospects_total']} prospects | {etat['contactes']} contactés | {etat['en_discussion']} en discussion | {etat['partenaires']} partenaires

FORMAT DU BRIEF (respecte ce format exactement) :

---
🤖 ALPHABOT WEEKLY — RÉUNION HEBDOMADAIRE
Antoine Metout — CEO & Fondateur
{etat['semaine']}
---

ORDRE DU JOUR
1. Tour de table des agents
2. KPIs de la semaine
3. Priorités de la semaine prochaine
4. Message du CEO

---

TOUR DE TABLE

[Chaque agent (Veille, Analyste, Rédacteur, Growth, Commercial, Analytics, CFO) prend la parole
en 3-4 lignes : ce qu'il a fait cette semaine, son résultat clé, et sa priorité pour la semaine prochaine.
Utilise des données réelles quand disponibles. Sois concret et honnête — si les chiffres sont encore petits,
les agents le disent avec confiance et vision long terme.]

KPIs DE LA SEMAINE
[Tableau synthétique des métriques clés avec indicateur tendance]

PRIORITÉS COLLECTIVES — SEMAINE PROCHAINE
[3 actions concrètes et prioritaires pour toute l'équipe]

MESSAGE DU CEO
[2 paragraphes qu'Antoine pourrait dire à son équipe d'agents : reconnaître le travail,
rappeler la vision, donner l'élan pour la semaine. Ton inspirant, ambitieux, humain.
Termine par la signature : Antoine Metout — CEO, AlphaBot Weekly]

---
Bonne semaine à tous. On vise les sommets. 🚀
---"""

        response = self.client.messages.create(
            model=CLAUDE_MODEL, max_tokens=1800,
            messages=[{"role": "user", "content": user}],
            system=system,
        )
        return response.content[0].text

    # ─── GÉNÉRATION DU BRIEF HTML ─────────────────────────────────────────────

    def generer_brief_html(self, contenu_texte: str, etat: dict) -> str:
        """Génère une version HTML premium du brief CEO."""

        # Convertir le texte en HTML simple
        lignes = contenu_texte.split('\n')
        html_body = ""
        for ligne in lignes:
            ligne = ligne.strip()
            if not ligne:
                html_body += '<div style="height:10px;"></div>'
            elif ligne.startswith('---'):
                html_body += '<hr style="border:none;border-top:1px solid rgba(255,255,255,.08);margin:16px 0;">'
            elif ligne.startswith('🤖') or ligne.startswith('ALPHABOT'):
                html_body += f'<h1 style="font-family:Space Grotesk,sans-serif;font-size:22px;font-weight:800;color:white;margin:8px 0 4px;">{ligne}</h1>'
            elif ligne.isupper() and len(ligne) > 3:
                html_body += f'<h2 style="font-size:11px;font-weight:700;letter-spacing:2px;color:#64748b;text-transform:uppercase;margin:22px 0 10px;">{ligne}</h2>'
            elif ligne.startswith('[') and ligne.endswith(']'):
                pass  # instructions de format, ignorer
            else:
                import re
                ligne = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', ligne)
                html_body += f'<p style="color:#cbd5e1;font-size:14px;line-height:1.8;margin:4px 0;">{ligne}</p>'

        now = datetime.now()
        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AlphaBot — CEO Brief {now.strftime('%d/%m/%Y')}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700;800&display=swap" rel="stylesheet">
</head>
<body style="margin:0;background:#04091a;font-family:Inter,sans-serif;padding:24px 12px 60px;">
  <div style="max-width:680px;margin:0 auto;">

    <!-- Bandeau CEO -->
    <div style="background:linear-gradient(135deg,rgba(59,130,246,.12),rgba(245,200,66,.07));
                border:1px solid rgba(59,130,246,.25);border-radius:16px;
                padding:28px;margin-bottom:20px;text-align:center;">
      <div style="font-size:10px;letter-spacing:3px;text-transform:uppercase;
                  color:#f5c842;margin-bottom:8px;">CONFIDENTIEL — RÉSERVÉ AU CEO</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:26px;font-weight:900;
                  background:linear-gradient(135deg,#fff,#22d3ee,#f5c842);
                  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;">
        🤖 AlphaBot Weekly
      </div>
      <div style="color:#94a3b8;font-size:13px;margin-top:4px;">
        Réunion hebdomadaire · {etat['semaine']}
      </div>
      <div style="margin-top:16px;display:flex;justify-content:center;gap:8px;flex-wrap:wrap;">
        <span style="background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.25);
                     color:#22c55e;font-size:11px;font-weight:700;padding:4px 12px;border-radius:20px;">
          👥 {etat['nb_abonnes']} abonnés
        </span>
        <span style="background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.25);
                     color:#3b82f6;font-size:11px;font-weight:700;padding:4px 12px;border-radius:20px;">
          +{etat['nouveaux_7j']} nouveaux
        </span>
        <span style="background:rgba(245,200,66,.1);border:1px solid rgba(245,200,66,.25);
                     color:#f5c842;font-size:11px;font-weight:700;padding:4px 12px;border-radius:20px;">
          {etat['rev_30j']}€ revenus/mois
        </span>
      </div>
    </div>

    <!-- Contenu -->
    <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);
                border-radius:14px;padding:28px;">
      {html_body}
    </div>

    <!-- Footer -->
    <div style="text-align:center;padding:24px 0 0;font-size:11px;color:#334155;">
      Généré automatiquement par l'Agent CEO Brief · AlphaBot Weekly<br>
      Antoine Metout — CEO & Fondateur
    </div>
  </div>
</body>
</html>"""

    # ─── POINT D'ENTRÉE ──────────────────────────────────────────────────────

    def lancer_reunion(self, sauvegarder_html: bool = True) -> dict:
        """Lance la réunion hebdomadaire et génère le brief complet."""
        print("\n━━━ AGENT CEO BRIEF : Réunion hebdomadaire ━━━")
        etat = self._collecter_etat_entreprise()

        print(f"  📋 Semaine : {etat['semaine']}")
        print(f"  👥 Abonnés : {etat['nb_abonnes']} | Revenus : {etat['rev_30j']}€")

        brief_texte = self.generer_brief()

        chemins = {"texte": None, "html": None}

        # Sauvegarde texte
        nom_txt = f"ceo_brief_{datetime.now().strftime('%Y-%m-%d')}.txt"
        chemin_txt = os.path.join(OUTPUT_DIR, nom_txt)
        with open(chemin_txt, "w", encoding="utf-8") as f:
            f.write(brief_texte)
        chemins["texte"] = chemin_txt

        # Sauvegarde HTML
        if sauvegarder_html:
            html = self.generer_brief_html(brief_texte, etat)
            nom_html = f"ceo_brief_{datetime.now().strftime('%Y-%m-%d')}.html"
            chemin_html = os.path.join(OUTPUT_DIR, nom_html)
            with open(chemin_html, "w", encoding="utf-8") as f:
                f.write(html)
            chemins["html"] = chemin_html

        print(f"\n✅ Brief CEO généré")
        print(f"   HTML  : {chemins['html']}")
        print(f"   Texte : {chemins['texte']}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        return {"success": True, "brief": brief_texte, **chemins}


if __name__ == "__main__":
    agent = AgentCEOBrief()
    result = agent.lancer_reunion()
    print(result["brief"])
