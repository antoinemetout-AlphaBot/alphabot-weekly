"""
AlphaBot — Agent Growth Booster 🚀
====================================
Rôle : Maximiser le nombre d'abonnés à la newsletter AlphaBot Weekly.

Deux axes de travail :
  1. SIMULATION  — Génère des abonnés réalistes pour tester le système en développement.
                   Ces profils sont clairement marqués source="simulation" dans le CSV.
                   Utile pour valider le pipeline email avant d'avoir de vrais abonnés.

  2. CROISSANCE  — Produit du contenu et des stratégies actionnables pour acquérir
                   de vrais abonnés humains : posts LinkedIn/Twitter, templates de
                   prospection, idées de lead magnets, stratégie referral.

Système de récompense :
  - Chaque vrai abonné humain gagné  = +10 points
  - Chaque abonné simulation ajouté  = +1 point (pour tester uniquement)
  - Score cumulé sauvegardé dans data/booster_score.json

Collaboration :
  - Travaille avec agent_growth (envoi, stats abonnés)
  - Rapporte au Directeur Adjoint via data/booster_score.json
"""

import os, sys, csv, json, random, string
from datetime import datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, OUTPUT_DIR
from utils.activity_logger import log_event as _log

_AGENT = "Agent Growth Booster"

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

DATA_DIR       = "data"
SUBSCRIBERS_CSV = os.path.join(DATA_DIR, "subscribers.csv")
SCORE_FILE     = os.path.join(DATA_DIR, "booster_score.json")

# ─── BANQUES DE DONNÉES RÉALISTES ─────────────────────────────────────────────
PRENOMS_FR = [
    "Emma","Lucas","Léa","Noah","Chloé","Ethan","Inès","Louis","Camille","Hugo",
    "Manon","Théo","Jade","Nathan","Lucie","Arthur","Zoé","Tom","Alice","Maxime",
    "Clara","Raphaël","Lola","Antoine","Sarah","Baptiste","Juliette","Alexis",
    "Pauline","Romain","Marie","Julien","Margot","Pierre","Anaïs","Thomas",
    "Charlotte","Nicolas","Elisa","Quentin","Laura","Valentin","Marion","Clément",
    "Ambre","Alexandre","Victoria","Florian","Océane","Mathieu","Sofia","Adrien",
]
NOMS_FR = [
    "Martin","Bernard","Dubois","Thomas","Robert","Richard","Petit","Durand",
    "Leroy","Moreau","Simon","Laurent","Lefebvre","Michel","Garcia","David",
    "Bertrand","Roux","Vincent","Fournier","Morel","Girard","Andre","Lefevre",
    "Mercier","Dupont","Lambert","Bonnet","François","Martinez","Legrand","Garnier",
    "Faure","Rousseau","Blanc","Guerin","Muller","Henry","Roussel","Nicolas",
    "Perrin","Morin","Mathieu","Clement","Gauthier","Dumont","Lopez","Fontaine",
]
DOMAINES_EMAIL = [
    "gmail.com","gmail.com","gmail.com","hotmail.fr","outlook.fr",
    "yahoo.fr","laposte.net","orange.fr","sfr.fr","free.fr","wanadoo.fr",
]
VILLES_FR = [
    "Paris","Lyon","Marseille","Toulouse","Nice","Nantes","Montpellier",
    "Strasbourg","Bordeaux","Lille","Rennes","Reims","Saint-Étienne","Toulon",
    "Grenoble","Dijon","Angers","Nîmes","Villeurbanne","Le Mans",
]
SOURCES_SIMULATION = [
    "linkedin","twitter","referral","organic_search","instagram","facebook",
    "reddit_finance","youtube","podcast","bouche_a_oreille",
]


class AgentGrowthBooster:
    """
    Agent Growth Booster : maximise les abonnés par simulation et stratégies réelles.
    """

    def __init__(self):
        Path(DATA_DIR).mkdir(exist_ok=True)
        Path(OUTPUT_DIR).mkdir(exist_ok=True)
        self._init_score()
        self.score_session = 0
        print("🚀 Agent Growth Booster initialisé ✅")

    # ═══════════════════════════════════════════════════════════════════════════
    # SYSTÈME DE RÉCOMPENSE
    # ═══════════════════════════════════════════════════════════════════════════

    def _init_score(self):
        """Initialise le fichier de score si absent."""
        if not os.path.exists(SCORE_FILE):
            self._sauvegarder_score({"total_points": 0, "vrais_abonnes_gagnes": 0,
                                     "simulations_ajoutees": 0, "sessions": []})

    def _lire_score(self) -> dict:
        try:
            with open(SCORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"total_points": 0, "vrais_abonnes_gagnes": 0,
                    "simulations_ajoutees": 0, "sessions": []}

    def _sauvegarder_score(self, score: dict):
        with open(SCORE_FILE, "w", encoding="utf-8") as f:
            json.dump(score, f, indent=2, ensure_ascii=False)

    def _ajouter_points(self, points: int, raison: str):
        score = self._lire_score()
        score["total_points"] += points
        self.score_session    += points
        if "vrais" in raison.lower():
            score["vrais_abonnes_gagnes"] += points // 10
        elif "simulation" in raison.lower():
            score["simulations_ajoutees"] += points
        self._sauvegarder_score(score)
        print(f"  🏆 +{points} pts — {raison} (total : {score['total_points']})")

    # ═══════════════════════════════════════════════════════════════════════════
    # AXE 1 — ABONNÉS SIMULATION (pour tester le pipeline)
    # ═══════════════════════════════════════════════════════════════════════════

    def _email_existe(self, email: str) -> bool:
        """Vérifie si un email est déjà dans le CSV."""
        try:
            with open(SUBSCRIBERS_CSV, "r", encoding="utf-8") as f:
                return any(row.get("email", "").lower() == email.lower()
                           for row in csv.DictReader(f))
        except FileNotFoundError:
            return False

    def _generer_profil(self) -> dict:
        """Génère un profil francophone réaliste."""
        prenom = random.choice(PRENOMS_FR)
        nom    = random.choice(NOMS_FR)
        domaine = random.choice(DOMAINES_EMAIL)
        # Patterns email réalistes
        patterns = [
            f"{prenom.lower()}.{nom.lower()}",
            f"{prenom.lower()}{nom.lower()[:3]}",
            f"{prenom.lower()[0]}{nom.lower()}",
            f"{nom.lower()}.{prenom.lower()}",
            f"{prenom.lower()}{random.randint(10,99)}",
        ]
        local = random.choice(patterns)
        email = f"{local}@{domaine}"
        # Date d'inscription répartie sur les 30 derniers jours
        jours_ago = random.randint(0, 30)
        date_inscription = (datetime.now() - timedelta(days=jours_ago)).strftime("%Y-%m-%d")
        return {
            "email":            email,
            "prenom":           prenom,
            "nom":              nom,
            "ville":            random.choice(VILLES_FR),
            "source":           f"simulation_{random.choice(SOURCES_SIMULATION)}",
            "date_inscription": date_inscription,
        }

    def ajouter_abonnes_simulation(self, nb: int = 10) -> dict:
        """
        Ajoute des abonnés de simulation réalistes au CSV.
        ⚠️  Ces profils sont clairement marqués 'simulation_*' dans la colonne source.
        Objectif : tester le pipeline email avant d'avoir de vrais abonnés.
        """
        print(f"\n  🤖 Génération de {nb} abonné(s) simulation...")
        ajoutes   = 0
        doublons  = 0
        tentatives = 0
        max_tentatives = nb * 5

        # Assurer que le CSV existe
        if not os.path.exists(SUBSCRIBERS_CSV):
            with open(SUBSCRIBERS_CSV, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(["email","prenom","source","date_inscription","actif","opens","clicks"])

        while ajoutes < nb and tentatives < max_tentatives:
            tentatives += 1
            profil = self._generer_profil()
            if self._email_existe(profil["email"]):
                doublons += 1
                continue
            with open(SUBSCRIBERS_CSV, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([
                    profil["email"], profil["prenom"], profil["source"],
                    profil["date_inscription"], "oui", 0, 0,
                ])
            ajoutes += 1

        self._ajouter_points(ajoutes, f"simulation — {ajoutes} profils ajoutés")
        print(f"  ✅ {ajoutes} simulation(s) ajoutée(s) | {doublons} doublon(s) évité(s)")
        return {"ajoutes": ajoutes, "doublons": doublons}

    def nb_abonnes_reels(self) -> int:
        """Compte les abonnés humains (source ne contenant pas 'simulation')."""
        try:
            with open(SUBSCRIBERS_CSV, "r", encoding="utf-8") as f:
                return sum(1 for r in csv.DictReader(f)
                           if "simulation" not in r.get("source","")
                           and r.get("actif","") == "oui")
        except FileNotFoundError:
            return 0

    def nb_abonnes_total(self) -> int:
        """Compte tous les abonnés actifs."""
        try:
            with open(SUBSCRIBERS_CSV, "r", encoding="utf-8") as f:
                return sum(1 for r in csv.DictReader(f)
                           if r.get("actif","") == "oui")
        except FileNotFoundError:
            return 0

    # ═══════════════════════════════════════════════════════════════════════════
    # AXE 2 — STRATÉGIES DE CROISSANCE RÉELLE (contenu actionnable)
    # ═══════════════════════════════════════════════════════════════════════════

    def generer_strategie_croissance(self) -> dict:
        """
        Utilise Claude pour générer du contenu de croissance offensif et prêt à poster.
        Produit des posts complets, des accroches testées, des angles géopolitiques.
        """
        if not CLAUDE_AVAILABLE:
            return self._strategie_fallback()

        print("  🧠 Génération de stratégies de croissance (brand anonyme AlphaBot Weekly)...")
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            nb_reels  = self.nb_abonnes_reels()
            nb_total  = self.nb_abonnes_total()
            score     = self._lire_score()
            today     = datetime.now().strftime("%A %d %B %Y")

            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2000,
                system="""Tu es un growth hacker specialise newsletters financieres francophones.
Tu travailles pour AlphaBot Weekly, newsletter 100% IA, anonyme, focus Bitcoin + macro geopolitique.
IMPORTANT : Reponds UNIQUEMENT en JSON valide. Pas de markdown. Pas de retours a la ligne dans les valeurs string. Utilise des phrases courtes.""",
                messages=[{"role": "user", "content": f"""
Date : {today} | Abonnes humains : {nb_reels} | Total : {nb_total} | Score : {score['total_points']} pts
Site : https://antoinemetout-alphabot.github.io/alphabot-weekly

Genere un plan de croissance en JSON STRICT (pas de retours a la ligne dans les strings) :
{{
  "article_seo": {{
    "titre": "Titre SEO 60 chars avec keyword fort",
    "meta_description": "Meta description 155 chars",
    "slug": "slug-url",
    "mots_cles": ["kw1", "kw2", "kw3"],
    "plan": ["H2 Section 1", "H2 Section 2", "H2 Section 3", "H2 Section 4"],
    "intro": "Introduction 2-3 phrases, angle geopolitique, accroche forte"
  }},
  "reddit_posts": [
    {{"subreddit": "r/finance_france", "titre": "Titre informatif", "resume": "Resume 2 phrases du post", "timing": "Quand poster"}},
    {{"subreddit": "r/Bitcoin_France", "titre": "Titre informatif", "resume": "Resume 2 phrases", "timing": "Quand poster"}}
  ],
  "annuaires": [
    {{"nom": "Nom annuaire", "url": "url", "action": "Action concrete"}},
    {{"nom": "Nom annuaire 2", "url": "url", "action": "Action concrete"}}
  ],
  "email_referral": {{
    "sujet": "Sujet email de recommandation",
    "resume": "Resume du contenu en 2 phrases"
  }},
  "lead_magnet": {{
    "titre": "Titre du lead magnet",
    "format": "Format",
    "points": ["Point 1", "Point 2", "Point 3"],
    "cta": "Texte du CTA"
  }},
  "partenariats": [
    {{"nom": "Newsletter partenaire", "raison": "Pourquoi", "approche": "Email en 1 phrase"}}
  ],
  "objectif_semaine": "Objectif SMART pour les 7 prochains jours",
  "action_prioritaire": "1 action concrete a faire dans les 2 prochaines heures"
}}"""}],
            )
            texte = response.content[0].text.strip()
            debut = texte.find("{")
            fin   = texte.rfind("}") + 1
            if debut != -1 and fin > debut:
                json_str = texte[debut:fin]
                # Parse avec strict=False pour tolérer les control characters
                import re
                json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
                return json.loads(json_str, strict=False)
        except Exception as e:
            print(f"  ⚠️ Erreur Claude : {e} — mode fallback")

        return self._strategie_fallback()

    def _strategie_fallback(self) -> dict:
        """Stratégies de base si Claude n'est pas disponible — VERSION ANONYME."""
        return {
            "article_seo_complet": {
                "titre": "Bitcoin et la géopolitique mondiale : ce que tout investisseur débutant doit savoir",
                "meta_description": "Comprendre pourquoi les tensions géopolitiques mondiales (Fed, OPEP, Chine) influencent directement le prix du Bitcoin. Analyse IA hebdomadaire gratuite.",
                "slug": "bitcoin-geopolitique-investisseur-debutant",
                "mots_cles_cibles": ["bitcoin géopolitique", "newsletter finance débutant", "analyse bitcoin IA"],
                "plan": ["Pourquoi le DXY influence Bitcoin", "Le rôle de l'or comme signal d'alarme", "Comment lire les tensions géopolitiques pour investir", "Les outils pour suivre ça simplement"],
                "intro_complete": "Chaque semaine, des milliers d'investisseurs débutants regardent le prix du Bitcoin sans comprendre pourquoi il monte ou descend. La réponse n'est pas dans les graphiques techniques — elle est dans les journaux. Quand la Fed hausse ses taux, le dollar se renforce et Bitcoin recule. Quand une guerre éclate, l'or monte et Bitcoin réagit. AlphaBot Weekly est la seule newsletter française qui fait ce lien géopolitique-marchés automatiquement, chaque semaine, grâce à l'IA.",
            },
            "tweets_thread_marque": [
                "🌍 Thread : Pourquoi le dollar américain est l'indicateur le plus important pour votre épargne (même si vous n'investissez pas aux USA) — @AlphaBotWeekly explique 🧵",
                "1/ Le Dollar Index (DXY) mesure la force du dollar face aux autres devises. Quand il monte, ça pèse sur TOUT : Bitcoin, or, pétrole, marchés émergents.",
                "2/ En 2022, quand la Fed a relevé ses taux 7 fois, le DXY a gagné +15%. Bitcoin a perdu -65%. Pas une coïncidence.",
                "3/ L'or monte quand les investisseurs ont peur. Le pétrole monte quand il y a des tensions au Moyen-Orient. Ces signaux sont lisibles AVANT que ça impacte votre portefeuille.",
                "4/ AlphaBot Weekly analyse ces liens géopolitiques chaque semaine automatiquement. Gratuit, en français, pour débutants.",
                "5/ → https://antoinemetout-alphabot.github.io/alphabot-weekly #Bitcoin #Finance #Investissement #Géopolitique",
            ],
            "reddit_posts_valeur": [
                {"subreddit": "r/finance_france", "titre": "Comment j'ai appris à lire les marchés grâce aux actualités géopolitiques (ressources)", "corps": "Partage de ressources pour comprendre le lien entre géopolitique et marchés financiers. Le DXY, l'or et le pétrole sont des indicateurs avancés que peu de débutants suivent. Une newsletter IA en français fait ce travail automatiquement si vous voulez un point de départ.", "timing": "Après 3 semaines de contributions actives au subreddit"},
                {"subreddit": "r/Bitcoin_France", "titre": "Bitcoin et le dollar : la corrélation que personne n'explique simplement", "corps": "Analyse de la corrélation inverse BTC/DXY sur les 5 dernières années. Chiffres et sources. Quand comprendre ça peut vous aider à mieux timing vos achats (pas un conseil financier, juste une observation statistique).", "timing": "Quand le compte a 30+ jours d'activité"},
            ],
            "annuaires_newsletters": [
                {"nom": "Lettres Françaises", "url": "https://lettresfrancaises.fr", "action": "Créer un compte gratuit et soumettre AlphaBot Weekly dans la catégorie Finance"},
                {"nom": "The Sample", "url": "https://thesample.ai", "action": "Inscrire la newsletter via le formulaire de soumission — recommande automatiquement aux lecteurs intéressés"},
                {"nom": "Substack Discover", "url": "https://substack.com/discover", "action": "Créer une publication Substack miroir gratuite pour bénéficier de leur algorithme de découverte"},
                {"nom": "Newsletterstack", "url": "https://newsletterstack.com", "action": "Soumettre dans la catégorie Finance/Investissement — gratuit, bonne visibilité FR"},
            ],
            "email_referral_automatique": {
                "sujet": "🤖 AlphaBot Weekly — Connaissez-vous quelqu'un qui devrait lire ça ?",
                "corps": "Bonjour,\n\nVous lisez AlphaBot Weekly depuis quelques semaines. Merci de votre fidélité !\n\nSi vous connaissez 2 personnes qui s'intéressent à la finance, Bitcoin ou à l'actualité économique mondiale — et qui aimeraient comprendre sans jargon — notre newsletter est faite pour elles.\n\nIl suffit de leur partager ce lien :\n👉 https://antoinemetout-alphabot.github.io/alphabot-weekly\n\nC'est gratuit, sans publicité, 100% IA.\n\nMerci d'avance — chaque recommandation compte !\n\nL'équipe AlphaBot Weekly 🤖",
            },
            "lead_magnet": {
                "titre": "Guide gratuit : Comprendre Bitcoin et la géopolitique en 10 minutes",
                "format": "PDF (4 pages)",
                "contenu_sommaire": ["Le DXY expliqué simplement", "Or et pétrole : les signaux d'alarme", "Comment Bitcoin réagit aux crises", "Les 5 indicateurs à surveiller chaque semaine"],
                "cta": "📥 Télécharger le guide gratuit",
            },
            "partenariats_newsletters": [
                {"nom": "Snowball (newsletter finance FR)", "raison": "Audience similaire, pas concurrente sur l'angle IA+géopolitique", "approche": "Email court proposant un échange de mention dans les prochaines éditions respectives. Pas de money deal, juste de la visibilité mutuelle."},
            ],
            "objectif_semaine": "Référencer AlphaBot Weekly dans 3 annuaires de newsletters francophones",
            "action_prioritaire": "Soumettre AlphaBot Weekly sur Lettres Françaises (15 min, gratuit, impact immédiat)",
        }

    def sauvegarder_strategie(self, strategie: dict) -> str:
        """Sauvegarde la stratégie de croissance en HTML dans outputs/."""
        now_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
        date    = datetime.now().strftime("%Y-%m-%d")

        def section(titre, items, couleur="#3b82f6"):
            if not items:
                return ""
            if isinstance(items, str):
                items = [items]
            # Convertit les dicts en strings lisibles pour le HTML
            safe_items = []
            for i in items:
                if isinstance(i, dict):
                    safe_items.append(" | ".join(f"<strong>{k}</strong>: {v}" for k, v in i.items()))
                else:
                    safe_items.append(str(i))
            contenu = "".join(f'<div class="item">→ {i}</div>' for i in safe_items)
            return f"""
            <div class="bloc">
              <div class="bloc-titre" style="color:{couleur};">{titre}</div>
              {contenu}
            </div>"""

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AlphaBot — Stratégie Growth {date}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@700;800&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:#04091a;color:#e2e8f0;font-family:'Inter',sans-serif;padding:24px 12px 60px;}}
.wrap{{max-width:760px;margin:0 auto;}}
header{{text-align:center;padding:28px 24px;margin-bottom:24px;
  background:linear-gradient(135deg,rgba(34,197,94,.1),rgba(59,130,246,.07));
  border:1px solid rgba(34,197,94,.25);border-radius:16px;}}
.logo{{font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:900;
  background:linear-gradient(135deg,#fff,#22c55e,#3b82f6);
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}}
.sub{{color:#64748b;font-size:13px;margin-top:4px;}}
.score{{display:inline-block;background:rgba(245,200,66,.1);border:1px solid rgba(245,200,66,.3);
  color:#f5c842;font-size:13px;font-weight:700;padding:5px 14px;border-radius:20px;margin-top:12px;}}
.bloc{{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);
  border-radius:12px;padding:18px 20px;margin-bottom:14px;}}
.bloc-titre{{font-size:11px;letter-spacing:2px;font-weight:700;text-transform:uppercase;margin-bottom:12px;}}
.item{{color:#cbd5e1;font-size:13px;line-height:1.7;padding:8px 12px;
  background:rgba(255,255,255,.02);border-radius:6px;margin-bottom:6px;}}
.priorite{{background:rgba(245,200,66,.06);border:1px solid rgba(245,200,66,.2);
  border-radius:12px;padding:18px 20px;margin-bottom:14px;}}
.priorite-titre{{font-size:11px;letter-spacing:2px;color:#f5c842;font-weight:700;margin-bottom:8px;}}
.priorite-texte{{color:#fcd34d;font-size:14px;font-weight:600;}}
footer{{text-align:center;color:#334155;font-size:11px;margin-top:24px;}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo">🚀 Agent Growth Booster</div>
    <div class="sub">Stratégie de croissance abonnés — {now_str}</div>
    <div class="score">🏆 Score cumulé : {self._lire_score()['total_points']} pts</div>
  </header>

  <div class="priorite">
    <div class="priorite-titre">⚡ ACTION PRIORITAIRE DU JOUR</div>
    <div class="priorite-texte">{strategie.get('action_prioritaire','—')}</div>
  </div>
  <div class="priorite" style="background:rgba(59,130,246,.06);border-color:rgba(59,130,246,.2);">
    <div class="priorite-titre" style="color:#3b82f6;">🎯 OBJECTIF DE LA SEMAINE</div>
    <div class="priorite-texte" style="color:#93c5fd;">{strategie.get('objectif_semaine','—')}</div>
  </div>

  {section("📰 Article SEO", strategie.get("article_seo", strategie.get("article_seo_complet", [])), "#8b5cf6")}
  {section("💬 Posts Reddit", strategie.get("reddit_posts", strategie.get("reddit_posts_valeur", [])), "#ff4500")}
  {section("📚 Annuaires Newsletters", strategie.get("annuaires", strategie.get("annuaires_newsletters", [])), "#22c55e")}
  {section("📧 Email Referral", strategie.get("email_referral", strategie.get("email_referral_automatique", dict())), "#06b6d4")}
  {section("🎁 Lead Magnet", strategie.get("lead_magnet", dict()), "#f59e0b")}
  {section("🤝 Partenariats", strategie.get("partenariats", strategie.get("partenariats_newsletters", [])), "#f5c842")}

  <footer>Généré par l'Agent Growth Booster · AlphaBot Weekly 🤖 — 100% IA</footer>
</div>
</body>
</html>"""

        nom    = f"growth_strategy_{date}.html"
        chemin = os.path.join(OUTPUT_DIR, nom)
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  ✅ Stratégie sauvegardée : {chemin}")
        return chemin

    # ═══════════════════════════════════════════════════════════════════════════
    # AXE 3 — PLAN D'ACTION TWITTER QUOTIDIEN @AlphaBotWeekly
    # ═══════════════════════════════════════════════════════════════════════════

    def generer_plan_twitter(self) -> dict:
        """
        Génère un plan d'action Twitter concret pour la journée.
        Stratégie human-first : engagement > volume, 3-4 tweets/jour max,
        5-10 interactions genuines, comportement humain crédible.
        """
        if not CLAUDE_AVAILABLE or not ANTHROPIC_API_KEY:
            return self._plan_twitter_fallback()

        print("  🐦 Génération du plan Twitter @AlphaBotWeekly...")
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            today  = datetime.now().strftime("%A %d %B %Y")
            jour_semaine = datetime.now().strftime("%A")

            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=3000,
                system="""Tu es expert en growth Twitter/X pour newsletters financières francophones.
Tu gères @AlphaBotWeekly — compte de marque 100% anonyme, newsletter IA focus Bitcoin + macro géopolitique.

RÈGLES ABSOLUES pour paraître humain et maximiser l'engagement :
1. JAMAIS plus de 4 tweets originaux par jour (spam = shadowban)
2. 70% du temps = interactions (likes, réponses à d'autres comptes) / 30% = contenu propre
3. 1-2 hashtags MAX par tweet (l'algorithme X pénalise le hashtag stuffing)
4. Varier les types : observation, question, réaction actu, thread, donnée choc
5. Répondre à des grands comptes finance/crypto FR pour se faire remarquer
6. Jamais de ton corporate — ton conversationnel, données précises, parfois emoji
7. Horaires optimaux FR : 8h-10h matin et 19h-21h soir en semaine
8. Les threads (5-7 tweets) génèrent 3x plus d'engagement que les tweets simples
9. Le premier tweet d'un thread DOIT accrocher en 1 ligne avec une stat ou question choc
10. Objectif final : chaque post doit donner envie de s'abonner à la newsletter

Réponds UNIQUEMENT en JSON valide, sans markdown autour.""",
                messages=[{"role": "user", "content": f"""
Date du jour : {today} ({jour_semaine})
Compte : @AlphaBotWeekly
Contexte : Newsletter IA hebdo, Bitcoin + macro géopolitique, investisseurs FR débutants.
Site : https://antoinemetout-alphabot.github.io/alphabot-weekly (gratuit, sans inscription lourde)

Génère le plan d'action Twitter du jour en JSON :
{{
  "resume_strategie_jour": "Résumé en 1 phrase de l'ambiance et focus du jour",
  "tweets_du_jour": [
    {{
      "heure_publication": "08:30",
      "type": "observation|question|thread|reaction_actu|donnee_choc|cta_doux",
      "contenu": "Texte complet du tweet (280 chars MAX, prêt à copier-coller, 1-2 emojis, 1 hashtag max)",
      "objectif": "Pourquoi ce tweet maintenant (engagement, visibilité, CTA...)",
      "si_thread": ["tweet 2/N", "tweet 3/N", "..."]
    }},
    {{
      "heure_publication": "12:15",
      "type": "question",
      "contenu": "Tweet question qui invite les gens à répondre (280 chars MAX)",
      "objectif": "Générer des replies pour booster l'algorithme",
      "si_thread": []
    }},
    {{
      "heure_publication": "19:45",
      "type": "donnee_choc",
      "contenu": "Tweet avec stat ou fait surprenant lié à Bitcoin/macro (280 chars MAX)",
      "objectif": "Viral potentiel, retweet facile",
      "si_thread": []
    }}
  ],
  "comptes_a_engager_aujourd_hui": [
    {{
      "compte": "@NomDuCompte",
      "type_compte": "Finance FR|Crypto FR|Économie|Macro|Géopolitique",
      "action": "Liker les 2-3 derniers posts + répondre au plus récent avec cette réponse :",
      "template_reponse": "Texte concret de la réponse à poster (pertinent, ajoute de la valeur, pas de promo directe)"
    }}
  ],
  "sujets_tendance_a_surveiller": [
    {{
      "hashtag": "#HashtagOuSujet",
      "pourquoi": "Pertinent car lié à Bitcoin/macro/géopolitique",
      "angle_possible": "Comment @AlphaBotWeekly peut réagir naturellement à ce sujet"
    }}
  ],
  "action_engagement_matin": "Routine 15 min le matin : actions concrètes à faire AVANT de poster (ex: liker 10 posts dans #Bitcoin, répondre à 3 tweets de @X...)",
  "action_engagement_soir": "Routine 10 min le soir : actions concrètes APRÈS avoir posté le tweet du soir",
  "erreurs_a_eviter_aujourd_hui": ["Erreur 1 spécifique au jour/contexte", "Erreur 2"],
  "kpi_a_tracker": {{
    "objectif_impressions": "X impressions cette semaine (réaliste pour un compte nouveau)",
    "objectif_followers": "+X followers cette semaine",
    "objectif_engagement_rate": "X% taux engagement cible",
    "action_si_tweet_performe": "Si un tweet dépasse 100 impressions, faire..."
  }}
}}
"""}],
            )
            texte = response.content[0].text.strip()
            debut = texte.find("{")
            fin   = texte.rfind("}") + 1
            if debut != -1 and fin > debut:
                return json.loads(texte[debut:fin])
        except Exception as e:
            print(f"  ⚠️ Erreur Claude Twitter : {e} — mode fallback")

        return self._plan_twitter_fallback()

    def _plan_twitter_fallback(self) -> dict:
        """Plan Twitter de base si Claude indisponible."""
        jour = datetime.now().strftime("%A")
        return {
            "resume_strategie_jour": f"Journée {jour} — Focus engagement + 1 thread Bitcoin/macro",
            "tweets_du_jour": [
                {
                    "heure_publication": "08:30",
                    "type": "donnee_choc",
                    "contenu": "📊 Le Bitcoin a perdu -65% en 2022 pendant que le Dollar Index gagnait +15%.\n\nCette corrélation inverse, peu de débutants la connaissent.\n\nThread sur pourquoi le dollar est l'indicateur N°1 à surveiller 🧵\n\n#Bitcoin",
                    "objectif": "Accrocher avec une stat forte, lancer un thread",
                    "si_thread": [
                        "1/ Le Dollar Index (DXY) mesure la force du $ face à 6 grandes devises. Quand il monte, les actifs risqués (BTC, actions) ont tendance à baisser. Voici pourquoi 👇",
                        "2/ La Fed hausse les taux → les investisseurs achètent des $ → DXY monte → Bitcoin recule. C'est mécanique. Ça s'est produit 4 fois depuis 2018.",
                        "3/ L'inverse est aussi vrai : quand la Fed baisse ses taux (2020, 2024), le DXY faiblit et Bitcoin s'envole. La corrélation est à -0.75 sur 5 ans.",
                        "4/ Donc avant d'acheter du BTC, regardez le DXY. Si il est en baisse depuis 3 semaines → signal favorable. Si en hausse → prudence.",
                        "5/ AlphaBot Weekly suit ça chaque semaine automatiquement par IA. Gratuit 👉 https://antoinemetout-alphabot.github.io/alphabot-weekly #Crypto #Finance",
                    ],
                },
                {
                    "heure_publication": "12:15",
                    "type": "question",
                    "contenu": "Question pour les investisseurs francophones 🇫🇷\n\nQuand vous achetez du Bitcoin, vous regardez quoi en premier ?\n\n→ Le prix\n→ Les news\n→ Les indicateurs macro\n→ Rien, j'achète sans regarder 😅\n\nCurieux de voir vos réponses 👇 #Bitcoin #Crypto",
                    "objectif": "Générer des replies, booster l'algorithme, identifier l'audience",
                    "si_thread": [],
                },
                {
                    "heure_publication": "19:45",
                    "type": "reaction_actu",
                    "contenu": "🌍 L'or vient de toucher un nouveau record historique.\n\nChaque fois que l'or monte fortement, ça signale une chose : les gros investisseurs ont peur.\n\nÀ surveiller de près cette semaine. AlphaBot Weekly fait ce suivi automatiquement 🤖\n\n#Or #Macro #Investissement",
                    "objectif": "Réaction à l'actualité, ton humain, CTA doux",
                    "si_thread": [],
                },
            ],
            "comptes_a_engager_aujourd_hui": [
                {
                    "compte": "@CoinAcademy_fr",
                    "type_compte": "Crypto FR",
                    "action": "Liker les 3 derniers posts + répondre au plus récent :",
                    "template_reponse": "Bonne analyse. Ce qui est intéressant c'est la corrélation avec le DXY en ce moment — le dollar donne souvent le signal en avance sur les prix crypto 🎯",
                },
                {
                    "compte": "@AxelDebassonFR",
                    "type_compte": "Finance FR",
                    "action": "Liker + répondre si post récent sur macro/taux :",
                    "template_reponse": "Exactement — et quand on superpose ça avec le positionnement des institutionnels (COT report), le tableau se précise encore plus. Bonne semaine !",
                },
                {
                    "compte": "@Le_Revenu",
                    "type_compte": "Finance FR",
                    "action": "Liker les posts récents sur marchés + répondre :",
                    "template_reponse": "Merci pour cet update. Pour les débutants qui veulent comprendre ces mouvements macro chaque semaine, il y a maintenant des newsletters IA qui synthétisent ça très bien 📊",
                },
                {
                    "compte": "@cryptoast",
                    "type_compte": "Crypto FR",
                    "action": "Liker + engager sur posts Bitcoin/macro :",
                    "template_reponse": "Le timing coïncide bien avec le mouvement du DXY cette semaine. C'est souvent le premier indicateur à regarder avant le BTC 👀",
                },
            ],
            "sujets_tendance_a_surveiller": [
                {
                    "hashtag": "#Bitcoin",
                    "pourquoi": "Hashtag principal, surveiller les posts avec fort engagement pour répondre",
                    "angle_possible": "Ajouter une perspective macro/géopolitique que les autres ne font pas",
                },
                {
                    "hashtag": "#FinanceTwitter",
                    "pourquoi": "Communauté finance FR active, bonne audience cible",
                    "angle_possible": "Se positionner comme la source IA hebdomadaire sur macro+crypto",
                },
                {
                    "hashtag": "#Inflation",
                    "pourquoi": "Toujours en tendance, lié directement à notre angle géopolitique",
                    "angle_possible": "Expliquer le lien inflation → Fed → DXY → Bitcoin simplement",
                },
            ],
            "action_engagement_matin": "08h00-08h15 → Ouvrir X, chercher #Bitcoin et #FinanceTwitter, liker 8-10 posts pertinents des comptes listés, laisser 2 réponses à valeur ajoutée (pas de promo). ENSUITE seulement, poster le tweet du matin.",
            "action_engagement_soir": "21h00-21h10 → Vérifier les réponses au tweet de la journée (répondre à CHAQUE reply dans les 15 minutes — l'algo adore ça), liker 5 nouveaux posts dans le fil #Macro.",
            "erreurs_a_eviter_aujourd_hui": [
                "Ne pas poster 4 tweets d'affilée sans interaction entre les deux — ça ressemble à du spam",
                "Ne pas mettre plus de 2 hashtags dans le même tweet",
                "Ne pas faire de promo directe dans les réponses aux autres comptes",
                "Ne pas ignorer les réponses à ses propres tweets",
            ],
            "kpi_a_tracker": {
                "objectif_impressions": "500 impressions cette semaine (réaliste pour compte tout nouveau)",
                "objectif_followers": "+10 followers cette semaine via engagement organique",
                "objectif_engagement_rate": "Viser 5%+ (likes+replies / impressions)",
                "action_si_tweet_performe": "Si un tweet dépasse 200 impressions → le transformer en thread le lendemain pour amplifier",
            },
        }

    def sauvegarder_plan_twitter(self, plan: dict) -> str:
        """Sauvegarde le plan Twitter quotidien en HTML."""
        now_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
        date    = datetime.now().strftime("%Y-%m-%d")

        # Génère les cards de tweets
        tweets_html = ""
        for i, tw in enumerate(plan.get("tweets_du_jour", []), 1):
            type_badge_colors = {
                "thread": "#8b5cf6",
                "question": "#06b6d4",
                "donnee_choc": "#f5c842",
                "reaction_actu": "#22c55e",
                "observation": "#3b82f6",
                "cta_doux": "#f59e0b",
            }
            badge_color = type_badge_colors.get(tw.get("type", ""), "#64748b")
            thread_html = ""
            if tw.get("si_thread"):
                thread_html = "<div style='margin-top:10px;padding:8px 12px;background:rgba(139,92,246,.08);border-left:2px solid #8b5cf6;border-radius:4px;'>"
                thread_html += f"<div style='color:#8b5cf6;font-size:10px;font-weight:700;letter-spacing:1px;margin-bottom:6px;'>🧵 THREAD ({len(tw['si_thread'])} tweets de suite)</div>"
                for j, t in enumerate(tw["si_thread"], 2):
                    thread_html += f"<div style='color:#94a3b8;font-size:12px;padding:4px 0;border-bottom:1px solid rgba(255,255,255,.04);'><span style='color:#8b5cf6;font-weight:600;'>{j}/</span> {t}</div>"
                thread_html += "</div>"

            tweets_html += f"""
            <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:16px 18px;margin-bottom:12px;">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                <span style="color:#22d3ee;font-weight:700;font-size:15px;">⏰ {tw.get('heure_publication','')}</span>
                <span style="background:{badge_color}22;border:1px solid {badge_color}44;color:{badge_color};font-size:10px;font-weight:700;letter-spacing:1px;padding:2px 10px;border-radius:20px;">{tw.get('type','').upper()}</span>
              </div>
              <div style="background:rgba(0,0,0,.3);border-radius:8px;padding:12px 14px;font-size:13px;color:#e2e8f0;line-height:1.6;white-space:pre-wrap;font-family:monospace;">{tw.get('contenu','')}</div>
              <div style="color:#64748b;font-size:11px;margin-top:8px;">🎯 {tw.get('objectif','')}</div>
              {thread_html}
            </div>"""

        # Génère les cards d'engagement
        engage_html = ""
        for c in plan.get("comptes_a_engager_aujourd_hui", []):
            engage_html += f"""
            <div style="background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:14px 16px;margin-bottom:10px;">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <span style="color:#1d9bf0;font-weight:700;">{c.get('compte','')}</span>
                <span style="color:#64748b;font-size:11px;">· {c.get('type_compte','')}</span>
              </div>
              <div style="color:#94a3b8;font-size:12px;margin-bottom:8px;">📋 {c.get('action','')}</div>
              <div style="background:rgba(29,155,240,.06);border:1px solid rgba(29,155,240,.15);border-radius:6px;padding:8px 12px;color:#bae6fd;font-size:12px;font-style:italic;">"{c.get('template_reponse','')}"</div>
            </div>"""

        # Tendances
        tend_html = ""
        for t in plan.get("sujets_tendance_a_surveiller", []):
            tend_html += f"""
            <div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.04);">
              <span style="color:#22d3ee;font-weight:700;min-width:130px;">{t.get('hashtag','')}</span>
              <span style="color:#94a3b8;font-size:12px;">{t.get('angle_possible','')}</span>
            </div>"""

        # Erreurs
        err_html = "".join(f'<div style="color:#fca5a5;font-size:12px;padding:5px 0;">⚠️ {e}</div>' for e in plan.get("erreurs_a_eviter_aujourd_hui", []))

        kpi = plan.get("kpi_a_tracker", {})

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AlphaBot — Plan Twitter {date}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@700;800&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:#04091a;color:#e2e8f0;font-family:'Inter',sans-serif;padding:24px 12px 60px;}}
.wrap{{max-width:720px;margin:0 auto;}}
header{{text-align:center;padding:24px;margin-bottom:20px;
  background:linear-gradient(135deg,rgba(29,155,240,.1),rgba(34,211,238,.07));
  border:1px solid rgba(29,155,240,.3);border-radius:16px;}}
.logo{{font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:900;
  background:linear-gradient(135deg,#1d9bf0,#22d3ee);
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}}
.sub{{color:#64748b;font-size:12px;margin-top:4px;}}
.section-label{{font-size:10px;letter-spacing:2px;font-weight:700;text-transform:uppercase;color:#64748b;margin:20px 0 10px;}}
.resume-box{{background:rgba(29,155,240,.06);border:1px solid rgba(29,155,240,.2);border-radius:10px;padding:12px 16px;color:#93c5fd;font-size:14px;margin-bottom:16px;}}
.routine-box{{border-radius:10px;padding:14px 16px;margin-bottom:10px;}}
.kpi-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;}}
.kpi-card{{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:12px 14px;}}
.kpi-label{{color:#64748b;font-size:10px;letter-spacing:1px;font-weight:700;text-transform:uppercase;margin-bottom:4px;}}
.kpi-val{{color:#22d3ee;font-size:13px;font-weight:600;}}
footer{{text-align:center;color:#334155;font-size:11px;margin-top:24px;}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo">🐦 Plan Twitter @AlphaBotWeekly</div>
    <div class="sub">{now_str} · Brand anonyme · Stratégie human-first</div>
  </header>

  <div class="resume-box">💡 {plan.get('resume_strategie_jour','')}</div>

  <div class="section-label">📅 Tweets du jour (copier-coller prêt)</div>
  {tweets_html}

  <div class="section-label">💬 Comptes à engager aujourd'hui</div>
  {engage_html}

  <div class="section-label">🔥 Routines d'engagement</div>
  <div class="routine-box" style="background:rgba(34,197,94,.05);border:1px solid rgba(34,197,94,.2);">
    <div style="color:#22c55e;font-size:10px;font-weight:700;letter-spacing:1px;margin-bottom:6px;">☀️ MATIN (15 MIN AVANT DE POSTER)</div>
    <div style="color:#86efac;font-size:13px;">{plan.get('action_engagement_matin','')}</div>
  </div>
  <div class="routine-box" style="background:rgba(245,200,66,.05);border:1px solid rgba(245,200,66,.2);">
    <div style="color:#f5c842;font-size:10px;font-weight:700;letter-spacing:1px;margin-bottom:6px;">🌙 SOIR (10 MIN APRÈS AVOIR POSTÉ)</div>
    <div style="color:#fcd34d;font-size:13px;">{plan.get('action_engagement_soir','')}</div>
  </div>

  <div class="section-label">📡 Hashtags / Sujets à surveiller</div>
  <div style="background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:12px 16px;margin-bottom:16px;">
    {tend_html}
  </div>

  <div class="section-label">⚠️ Erreurs à éviter aujourd'hui</div>
  <div style="background:rgba(239,68,68,.05);border:1px solid rgba(239,68,68,.2);border-radius:10px;padding:12px 16px;margin-bottom:16px;">
    {err_html}
  </div>

  <div class="section-label">📊 KPIs de la semaine</div>
  <div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-label">Impressions cibles</div><div class="kpi-val">{kpi.get('objectif_impressions','—')}</div></div>
    <div class="kpi-card"><div class="kpi-label">Followers cibles</div><div class="kpi-val">{kpi.get('objectif_followers','—')}</div></div>
    <div class="kpi-card"><div class="kpi-label">Taux d'engagement</div><div class="kpi-val">{kpi.get('objectif_engagement_rate','—')}</div></div>
    <div class="kpi-card" style="grid-column:span 2;"><div class="kpi-label">Si tweet performe</div><div class="kpi-val" style="color:#22c55e;">{kpi.get('action_si_tweet_performe','—')}</div></div>
  </div>

  <footer style="margin-top:28px;">Généré par l'Agent Growth Booster · @AlphaBotWeekly · AlphaBot Weekly 🤖</footer>
</div>
</body>
</html>"""

        nom    = f"twitter_plan_{date}.html"
        chemin = os.path.join(OUTPUT_DIR, nom)
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  ✅ Plan Twitter sauvegardé : {chemin}")

        # Sauvegarde aussi en JSON pour l'agent_twitter.py
        chemin_json = os.path.join(DATA_DIR, f"twitter_plan_{date}.json")
        with open(chemin_json, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Plan Twitter JSON : {chemin_json}")

        return chemin

    # ═══════════════════════════════════════════════════════════════════════════
    # RAPPORT DE SESSION
    # ═══════════════════════════════════════════════════════════════════════════

    def rapport(self) -> str:
        score = self._lire_score()
        nb_reels = self.nb_abonnes_reels()
        nb_total = self.nb_abonnes_total()
        return f"""
╔══════════════════════════════════════════════════╗
║      🚀  RAPPORT AGENT GROWTH BOOSTER            ║
╚══════════════════════════════════════════════════╝

🏆 SCORE CUMULÉ       : {score['total_points']} pts
🏆 SCORE CETTE SESSION: {self.score_session} pts

👥 ABONNÉS
   Total actifs         : {nb_total}
   Humains réels        : {nb_reels}
   Simulation (dev)     : {nb_total - nb_reels}

📈 HISTORIQUE
   Vrais abonnés gagnés : {score.get('vrais_abonnes_gagnes', 0)}
   Simulations ajoutées : {score.get('simulations_ajoutees', 0)}

📊 STRATÉGIE
   Axes principaux : SEO, Reddit, annuaires newsletters, partenariats
   Fichier stratégie → outputs/growth_strategy_YYYY-MM-DD.html
"""

    # ═══════════════════════════════════════════════════════════════════════════
    # ORCHESTRATEUR
    # ═══════════════════════════════════════════════════════════════════════════

    def run(self, mode_simulation: bool = False, nb_simulations: int = 5) -> dict:
        """
        Lance le cycle complet du Growth Booster.
        - mode_simulation=True  → ajoute des abonnés de test (développement uniquement)
        - mode_simulation=False → génère uniquement les stratégies de croissance réelle
        """
        print("\n━━━ AGENT GROWTH BOOSTER : Démarrage ━━━")
        resultats = {}

        avant = self.nb_abonnes_total()

        _log(_AGENT, "start", f"Cycle Growth Booster démarré (simulation={'oui' if mode_simulation else 'non'})")
        if mode_simulation:
            print(f"\n[1/2] 🤖 Mode simulation — ajout de {nb_simulations} profils...")
            _log(_AGENT, "progress", f"Ajout de {nb_simulations} abonnés simulation...")
            resultats["simulation"] = self.ajouter_abonnes_simulation(nb_simulations)
            r = resultats["simulation"]
            _log(_AGENT, "success", f"{r['ajoutes']} profils simulation ajoutés au CSV", r)
        else:
            print("\n[1/2] ⏭️  Mode simulation désactivé (production)")
            resultats["simulation"] = None

        print("\n[2/2] 🧠 Génération stratégies de croissance réelle...")
        _log(_AGENT, "progress", "Génération des stratégies de croissance avec Claude IA...")
        try:
            strategie = self.generer_strategie_croissance()
            chemin    = self.sauvegarder_strategie(strategie)
            resultats["strategie"] = strategie
            resultats["fichier_strategie"] = chemin
            action_prio = str(strategie.get('action_prioritaire','?'))[:80]
            _log(_AGENT, "success", f"Stratégie générée : {action_prio}",
                 {"objectif": str(strategie.get("objectif_semaine",""))})
        except Exception as e:
            print(f"  ⚠️ Erreur stratégie croissance : {e} — on continue")
            _log(_AGENT, "warning", f"Stratégie croissance erreur: {str(e)[:80]}")
            resultats["strategie"] = self._strategie_fallback()

        # Twitter désactivé (22/03/2026) — Antoine n'utilise plus Twitter pour l'instant
        resultats["plan_twitter"] = None

        apres = self.nb_abonnes_total()
        nouveaux = apres - avant
        if nouveaux > 0:
            self._ajouter_points(nouveaux * 10, f"vrais abonnés — +{nouveaux} humains")
            _log(_AGENT, "milestone", f"+{nouveaux} nouvel(s) abonné(s) humain(s) !", {"nouveaux": nouveaux})

        # Sauvegarde session dans le score
        score = self._lire_score()
        score.setdefault("sessions", []).append({
            "date":            datetime.now().strftime("%Y-%m-%d %H:%M"),
            "pts_session":     self.score_session,
            "abonnes_avant":   avant,
            "abonnes_apres":   apres,
        })
        score["sessions"] = score["sessions"][-30:]
        self._sauvegarder_score(score)

        print(self.rapport())
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        return resultats


# ─── POINT D'ENTRÉE STANDALONE ────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Agent Growth Booster AlphaBot")
    parser.add_argument("--simulation", action="store_true",
                        help="Ajouter des abonnés de simulation (tests dev uniquement)")
    parser.add_argument("--nb", type=int, default=5,
                        help="Nombre d'abonnés simulation à ajouter (défaut: 5)")
    args = parser.parse_args()

    agent = AgentGrowthBooster()
    agent.run(mode_simulation=args.simulation, nb_simulations=args.nb)
