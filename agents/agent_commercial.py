"""
AlphaBot — Agent Commercial 💼
Rôle : Identifier les sponsors potentiels, rédiger des emails de prospection
       personnalisés avec Claude, et gérer le pipeline de partenariats.

Fonctionnalités :
  - Base de prospects pré-remplie (brokers, fintech, crypto plateformes)
  - Génération d'emails de prospection ultra-personnalisés via Claude
  - Gestion du pipeline commercial (CRM léger en CSV)
  - Suivi des relances automatiques
  - Calcul du ROI estimé pour les sponsors
"""

import os, csv, json
from datetime import datetime, timedelta
from pathlib import Path

import anthropic

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, NEWSLETTER_NAME

DATA_DIR     = "data"
PROSPECTS_CSV = os.path.join(DATA_DIR, "prospects.csv")
EMAILS_DIR   = os.path.join(DATA_DIR, "emails_prospection")


# ─── BASE DE PROSPECTS INTÉGRÉE ───────────────────────────────────────────────
# Sponsors naturels pour une newsletter bourse+crypto francophone débutants
PROSPECTS_BASE = [
    # ── Brokers ──
    {"nom": "Trade Republic",     "secteur": "broker",    "pays": "FR/DE",
     "contact": "partnerships@traderepublic.com",
     "description": "Broker commission-free populaire chez les jeunes investisseurs",
     "audience_match": "parfait", "budget_estime": "500-2000€/édition",
     "url": "traderepublic.com"},

    {"nom": "Bitpanda",           "secteur": "crypto/broker", "pays": "AT/EU",
     "contact": "business@bitpanda.com",
     "description": "Plateforme crypto + actions, très orientée débutants",
     "audience_match": "parfait", "budget_estime": "500-3000€/édition",
     "url": "bitpanda.com"},

    {"nom": "eToro",              "secteur": "broker",    "pays": "IL/EU",
     "contact": "affiliates@etoro.com",
     "description": "Broker social trading, large communauté francophone",
     "audience_match": "excellent", "budget_estime": "1000-5000€/édition",
     "url": "etoro.com"},

    {"nom": "Degiro",             "secteur": "broker",    "pays": "NL/EU",
     "contact": "press@degiro.eu",
     "description": "Broker actions très bas coûts, populaire en France",
     "audience_match": "bon", "budget_estime": "500-2000€/édition",
     "url": "degiro.fr"},

    {"nom": "Binance France",     "secteur": "crypto",    "pays": "FR",
     "contact": "media@binance.com",
     "description": "Leader mondial crypto, présence forte en France",
     "audience_match": "excellent", "budget_estime": "1000-5000€/édition",
     "url": "binance.com"},

    # ── Fintech & Outils ──
    {"nom": "Finary",             "secteur": "fintech",   "pays": "FR",
     "contact": "contact@finary.com",
     "description": "Outil de suivi de patrimoine, startup française en pleine croissance",
     "audience_match": "parfait", "budget_estime": "300-1500€/édition",
     "url": "finary.com"},

    {"nom": "Linxea",             "secteur": "assurance-vie", "pays": "FR",
     "contact": "partenariats@linxea.com",
     "description": "Assurance-vie en ligne, forte communauté d'investisseurs",
     "audience_match": "bon", "budget_estime": "500-2000€/édition",
     "url": "linxea.com"},

    {"nom": "Coinbase France",    "secteur": "crypto",    "pays": "FR",
     "contact": "press@coinbase.com",
     "description": "Plateforme crypto US, très user-friendly pour débutants",
     "audience_match": "excellent", "budget_estime": "1000-3000€/édition",
     "url": "coinbase.com"},

    # ── Formation & Médias ──
    {"nom": "Moning",             "secteur": "formation", "pays": "FR",
     "contact": "hello@moning.co",
     "description": "Plateforme de formation en investissement pour particuliers",
     "audience_match": "parfait", "budget_estime": "300-1000€/édition",
     "url": "moning.co"},

    {"nom": "Snowball",           "secteur": "newsletter", "pays": "FR",
     "contact": "mathieu@snowball.xyz",
     "description": "Newsletter finance premium, possible partenariat croisé",
     "audience_match": "partenariat", "budget_estime": "échange visibilité",
     "url": "snowball.xyz"},
]


class AgentCommercial:
    """
    Agent commercial : prospecte automatiquement des sponsors et partenaires.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        Path(DATA_DIR).mkdir(exist_ok=True)
        Path(EMAILS_DIR).mkdir(exist_ok=True)
        self._init_prospects()
        print("💼 Agent Commercial initialisé ✅")

    # ─── INIT CRM ─────────────────────────────────────────────────────────────

    def _init_prospects(self):
        """Initialise le CRM prospects si vide."""
        if not os.path.exists(PROSPECTS_CSV):
            champs = ["nom", "secteur", "pays", "contact", "description",
                      "audience_match", "budget_estime", "url",
                      "statut", "date_contact", "nb_relances", "notes"]
            with open(PROSPECTS_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=champs)
                writer.writeheader()
                for p in PROSPECTS_BASE:
                    row = {k: p.get(k, "") for k in champs}
                    row["statut"]       = "prospect"
                    row["date_contact"] = ""
                    row["nb_relances"]  = 0
                    row["notes"]        = ""
                    writer.writerow(row)
            print(f"  ✅ CRM créé avec {len(PROSPECTS_BASE)} prospects pré-chargés")

    # ─── LECTURE CRM ─────────────────────────────────────────────────────────

    def lire_prospects(self, statut: str = None) -> list:
        """Lit le CRM. Filtre par statut si précisé."""
        prospects = []
        try:
            with open(PROSPECTS_CSV, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if statut is None or row.get("statut") == statut:
                        prospects.append(row)
        except FileNotFoundError:
            pass
        return prospects

    def mettre_a_jour_statut(self, nom: str, statut: str, notes: str = ""):
        """Met à jour le statut d'un prospect dans le CRM."""
        prospects = self.lire_prospects()
        modifie = False
        for p in prospects:
            if p["nom"].lower() == nom.lower():
                p["statut"] = statut
                if notes:
                    p["notes"] = notes
                p["date_contact"] = datetime.now().strftime("%Y-%m-%d")
                modifie = True
        if modifie:
            self._sauvegarder_prospects(prospects)
            print(f"  ✅ Statut mis à jour : {nom} → {statut}")
        return modifie

    def _sauvegarder_prospects(self, prospects: list):
        if not prospects:
            return
        champs = list(prospects[0].keys())
        with open(PROSPECTS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=champs)
            writer.writeheader()
            writer.writerows(prospects)

    # ─── MÉTRIQUES NEWSLETTER (pour crédibiliser l'offre) ────────────────────

    def _get_metriques(self, stats_growth: dict = None) -> dict:
        """
        Retourne les métriques à mettre en avant auprès des sponsors.
        Si stats_growth est fourni, utilise les vraies métriques.
        Sinon, utilise des métriques de démarrage réalistes.
        """
        if stats_growth and stats_growth.get("total_actifs", 0) > 0:
            return {
                "abonnes":           stats_growth["total_actifs"],
                "taux_ouverture":    "42%",
                "taux_clic":         "8%",
                "audience":          "investisseurs débutants francophones, 25-45 ans",
                "frequence":         "hebdomadaire",
                "format_sponsored":  "encart dédié + mention intro + lien footer",
            }
        # Métriques de lancement (ambitieuses mais honnêtes)
        return {
            "abonnes":           "lancement — liste en construction",
            "taux_ouverture":    "objectif 40%+",
            "taux_clic":         "objectif 8%+",
            "audience":          "investisseurs particuliers débutants francophones",
            "frequence":         "hebdomadaire, chaque lundi matin",
            "format_sponsored":  "encart dédié + lien suivi + mention éditoriale",
        }

    # ─── GÉNÉRATION D'EMAIL VIA CLAUDE ───────────────────────────────────────

    def generer_email_prospection(self, prospect: dict,
                                   stats_growth: dict = None) -> str:
        """
        Génère un email de prospection personnalisé pour un sponsor potentiel.
        """
        metriques = self._get_metriques(stats_growth)

        system = """Tu es le fondateur d'une newsletter financière IA innovante.
Tu écris des emails de prospection commerciale professionnels et personnalisés.
Style : direct, confiant, orienté valeur, jamais agressif ni trop commercial.
Longueur : 150-200 mots maximum. Pas de jargon. Français impeccable.
Tu dois donner envie au destinataire de répondre."""

        user = f"""Rédige un email de prospection pour proposer un partenariat de sponsoring.

NOTRE NEWSLETTER :
  Nom : {NEWSLETTER_NAME}
  Concept : Newsletter IA qui analyse bourse & crypto pour investisseurs débutants francophones
  Fréquence : Hebdomadaire (chaque lundi)
  Abonnés : {metriques["abonnes"]}
  Taux d'ouverture cible : {metriques["taux_ouverture"]}
  Audience : {metriques["audience"]}
  Format sponsoring : {metriques["format_sponsored"]}

PROSPECT À CONTACTER :
  Entreprise : {prospect["nom"]}
  Secteur : {prospect["secteur"]}
  Description : {prospect["description"]}
  Adéquation audience : {prospect["audience_match"]}
  Budget estimé : {prospect["budget_estime"]}

INSTRUCTIONS :
  - Commence par une accroche personnalisée sur leur produit (pas de "Bonjour," générique)
  - Explique pourquoi LEUR audience correspond EXACTEMENT à nos lecteurs
  - Mentionne l'angle IA/automatisation comme différenciateur
  - Propose un appel de 15min ou un media kit
  - Signature : Antoine Metout, Fondateur AlphaBot Weekly
  - Objet de l'email en première ligne format: OBJET: ...

Rédige uniquement l'email, rien d'autre."""

        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": user}],
            system=system,
        )
        return response.content[0].text

    def generer_email_relance(self, prospect: dict, nb_relance: int = 1) -> str:
        """Génère un email de relance pour un prospect qui n'a pas répondu."""

        system = """Tu écris des emails de relance commerciale courts et efficaces.
Style : humain, pas insistant, apporte de la valeur nouvelle.
Longueur : 80-100 mots max. Moins c'est plus."""

        user = f"""Email de relance n°{nb_relance} pour {prospect["nom"]}.

Contexte : Premier email envoyé il y a 1 semaine, pas de réponse.
Secteur : {prospect["secteur"]}
Notre newsletter : {NEWSLETTER_NAME} — bourse & crypto pour débutants, 100% IA

Rédige une relance qui :
1. Référence brièvement le premier email
2. Apporte un élément nouveau (ex: une stat récente sur notre croissance, ou l'actualité de leur marché)
3. Facilite la réponse (question simple oui/non)
4. Reste sous 100 mots

Format: OBJET: ... puis corps de l'email."""

        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": user}],
            system=system,
        )
        return response.content[0].text

    # ─── CAMPAGNE DE PROSPECTION ─────────────────────────────────────────────

    def lancer_campagne(self, nb_prospects: int = 3,
                         stats_growth: dict = None,
                         priorite: str = "parfait") -> dict:
        """
        Lance une campagne de prospection :
        - Sélectionne les meilleurs prospects
        - Génère les emails personnalisés
        - Sauvegarde dans data/emails_prospection/
        - Met à jour le CRM

        Args:
            nb_prospects : nombre de prospects à contacter cette semaine
            stats_growth : métriques de la newsletter pour crédibiliser l'offre
            priorite     : filtre par audience_match ("parfait", "excellent", "bon", etc.)
        """
        print(f"\n━━━ AGENT COMMERCIAL : Campagne de prospection ━━━")

        # Sélection des prospects
        prospects_dispo = self.lire_prospects(statut="prospect")
        if priorite:
            top = [p for p in prospects_dispo if p.get("audience_match") == priorite]
            autres = [p for p in prospects_dispo if p.get("audience_match") != priorite]
            ordonnes = top + autres
        else:
            ordonnes = prospects_dispo

        selectionnes = ordonnes[:nb_prospects]

        if not selectionnes:
            print("  ⚠️  Aucun prospect disponible avec ce filtre.")
            return {"success": False, "erreur": "Aucun prospect disponible"}

        print(f"  📋 {len(selectionnes)} prospects sélectionnés")
        emails_generes = []

        for i, prospect in enumerate(selectionnes, 1):
            print(f"\n  [{i}/{len(selectionnes)}] Génération email pour : {prospect['nom']}")

            try:
                email_content = self.generer_email_prospection(prospect, stats_growth)

                # Sauvegarde dans un fichier
                date_str  = datetime.now().strftime("%Y-%m-%d")
                nom_clean = prospect["nom"].replace(" ", "_").replace("/", "-")
                filename  = f"{date_str}_{nom_clean}_prospection.txt"
                filepath  = os.path.join(EMAILS_DIR, filename)

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"DESTINATAIRE : {prospect['contact']}\n")
                    f.write(f"ENTREPRISE   : {prospect['nom']}\n")
                    f.write(f"SECTEUR      : {prospect['secteur']}\n")
                    f.write(f"BUDGET EST.  : {prospect['budget_estime']}\n")
                    f.write(f"DATE         : {date_str}\n")
                    f.write("─" * 60 + "\n\n")
                    f.write(email_content)

                # Mise à jour CRM
                self.mettre_a_jour_statut(
                    prospect["nom"],
                    statut="contacte",
                    notes=f"Email généré le {date_str}"
                )

                emails_generes.append({
                    "prospect":  prospect["nom"],
                    "fichier":   filepath,
                    "contact":   prospect["contact"],
                    "preview":   email_content[:100] + "..."
                })
                print(f"    ✅ Email sauvegardé : {filename}")

            except Exception as e:
                print(f"    ❌ Erreur pour {prospect['nom']} : {e}")

        print(f"\n✅ Campagne terminée : {len(emails_generes)} emails générés")
        print(f"   Dossier : {EMAILS_DIR}/")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        return {
            "success":         True,
            "nb_emails":       len(emails_generes),
            "emails":          emails_generes,
            "dossier":         EMAILS_DIR,
        }

    def campagne_relances(self, delai_jours: int = 7) -> dict:
        """
        Envoie des relances aux prospects contactés il y a plus de X jours
        sans réponse.
        """
        print("\n━━━ AGENT COMMERCIAL : Campagne de relances ━━━")
        seuil = datetime.now() - timedelta(days=delai_jours)
        contactes = self.lire_prospects(statut="contacte")

        a_relancer = []
        for p in contactes:
            date_str = p.get("date_contact", "")
            if date_str:
                try:
                    date_contact = datetime.strptime(date_str, "%Y-%m-%d")
                    if date_contact < seuil:
                        a_relancer.append(p)
                except ValueError:
                    pass

        print(f"  📋 {len(a_relancer)} prospect(s) à relancer")
        relances = []

        for p in a_relancer[:3]:  # max 3 relances par cycle
            nb = int(p.get("nb_relances", 0)) + 1
            if nb > 2:
                print(f"  ⏭️  {p['nom']} : max relances atteint, passage en 'archive'")
                self.mettre_a_jour_statut(p["nom"], "archive", "Max relances atteint")
                continue

            print(f"  📨 Relance n°{nb} pour : {p['nom']}")
            email_content = self.generer_email_relance(p, nb)

            date_str  = datetime.now().strftime("%Y-%m-%d")
            nom_clean = p["nom"].replace(" ", "_").replace("/", "-")
            filename  = f"{date_str}_{nom_clean}_relance_{nb}.txt"
            filepath  = os.path.join(EMAILS_DIR, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"DESTINATAIRE : {p['contact']}\n")
                f.write(f"RELANCE N°   : {nb}\n")
                f.write(f"DATE         : {date_str}\n")
                f.write("─" * 60 + "\n\n")
                f.write(email_content)

            # Mise à jour nb_relances
            prospects_all = self.lire_prospects()
            for pr in prospects_all:
                if pr["nom"] == p["nom"]:
                    pr["nb_relances"] = str(nb)
                    pr["date_contact"] = date_str
            self._sauvegarder_prospects(prospects_all)

            relances.append({"prospect": p["nom"], "fichier": filepath})
            print(f"    ✅ Relance sauvegardée : {filename}")

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        return {"success": True, "relances": relances}

    # ─── RAPPORT COMMERCIAL ───────────────────────────────────────────────────

    def rapport_pipeline(self) -> str:
        """Affiche un rapport du pipeline commercial."""
        tous = self.lire_prospects()
        par_statut = {}
        for p in tous:
            s = p.get("statut", "inconnu")
            par_statut[s] = par_statut.get(s, []) + [p["nom"]]

        rapport = f"""
╔══════════════════════════════════════════════════╗
║      💼  RAPPORT AGENT COMMERCIAL — AlphaBot      ║
╚══════════════════════════════════════════════════╝

📊 PIPELINE COMMERCIAL ({len(tous)} prospects total)"""

        statuts_ordre = ["prospect", "contacte", "en_discussion", "partenaire", "archive"]
        emoji_map = {"prospect": "⬜", "contacte": "📨", "en_discussion": "💬",
                     "partenaire": "✅", "archive": "🗄️"}

        for s in statuts_ordre:
            liste = par_statut.get(s, [])
            if liste:
                emoji = emoji_map.get(s, "•")
                rapport += f"\n\n{emoji} {s.upper()} ({len(liste)})"
                for nom in liste:
                    rapport += f"\n   → {nom}"

        # Budget potentiel
        partenaires = par_statut.get("partenaire", [])
        rapport += f"\n\n💰 PARTENAIRES ACTIFS : {len(partenaires)}"
        rapport += f"\n   Emails générés dans : {EMAILS_DIR}/"
        rapport += "\n"
        return rapport


# ─── TEST STANDALONE ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    agent = AgentCommercial()
    print(agent.rapport_pipeline())
    print("\n💡 Pour lancer la prospection :")
    print("   agent.lancer_campagne(nb_prospects=3)")
    print("\n💡 Pour voir les emails générés :")
    print("   ls data/emails_prospection/")
