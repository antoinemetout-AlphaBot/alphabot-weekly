# 🤖 AlphaBot Weekly — Brief Complet pour Claude Projects

> **Ce document est le contexte de démarrage à coller dans Claude Projects.**
> Il remplace l'intégralité des conversations passées. Tu as ici TOUTES les informations nécessaires pour continuer le travail sur le projet AlphaBot Weekly.

---

## 👤 Qui est Antoine ?

- **Nom** : Antoine Metout — `antoine.metout@gmail.com`
- **Rôle** : CEO fondateur du projet AlphaBot Weekly
- **Profil** : Non-développeur. Il ne code pas, ne lit pas Python. Il donne des directives en français et attend que Claude exécute tout de manière autonome.
- **Exigences** : Antoine veut un projet qui tourne **sans lui**, avec des agents IA autonomes qui travaillent chaque jour de 7h30 à 22h30. Il veut **voir** le travail de ses agents (dashboard, emails, newsletters).
- **Style de communication** : Direct, en français, parfois impatient. Il n'aime pas les explications trop longues — il veut des résultats concrets.

---

## 📌 C'est quoi AlphaBot Weekly ?

Une **newsletter financière IA** qui décrypte la bourse et la géopolitique pour des investisseurs débutants francophones.

- **Site public** : hébergé sur **GitHub Pages** — déploiement automatique via `auto_push.py` + GitHub Actions
- **URL** : `https://antoinemetout-alphabot.github.io/alphabot-weekly`
- **Modèle** : newsletter gratuite → croissance abonnés → monétisation pub/sponsors
- **Philosophie éditoriale** : inspirée d'**aktionnaire.com** — chaque section commence par un FAIT concret avec un chiffre, titres accrocheurs, jamais de phrases génériques
- **Cible** : investisseurs débutants francophones, 25-45 ans
- **Abonnés actuels** : 2 (Antoine + 1 vrai abonné Emma)
- **Newsletters publiées** : 5 éditions (du 20 au 24 mars 2026), quotidiennes
- **Modèle Claude utilisé** : `claude-sonnet-4-6`

---

## 📁 Structure du projet

```
Alphabot/                          ← Dossier racine (sur le PC d'Antoine)
├── agents/                        ← Les agents IA Python
│   ├── agent_veille.py            ← Collecte données marchés (yfinance, CoinGecko)
│   ├── agent_analyste.py          ← Analyse macro, géopolitique, crypto, bourse
│   ├── agent_redacteur.py         ← Rédige la newsletter HTML complète
│   ├── agent_growth.py            ← Gestion abonnés, envoi emails SMTP, notifications
│   ├── agent_da_site.py           ← Design/Aesthetic : améliore le site entier autonomement
│   ├── agent_adjoint.py           ← Directeur Adjoint : supervise tout, envoie rapport CEO
│   ├── agent_investissement.py    ← Gère le portefeuille IA (3 profils : prudent, modéré, agressif)
│   ├── agent_trader.py            ← 🆕 Robot Trader actif — trading intraday/swing
│   ├── agent_linkedin.py          ← 🆕 Génère 7 posts LinkedIn/semaine (données fraîches)
│   ├── agent_twitter.py           ← Poste sur @AlphaBot_Weekly (DÉSACTIVÉ)
│   ├── agent_analytics.py         ← Dashboard métriques KPIs
│   ├── agent_commercial.py        ← Prospection sponsors (DÉSACTIVÉ — trop tôt)
│   ├── agent_cfo.py               ← Rapport financier mensuel (DÉSACTIVÉ — 0€ revenu)
│   ├── agent_ceo_brief.py         ← Brief stratégique CEO
│   └── agent_growth_booster.py    ← Contenu viral (DÉSACTIVÉ — pas d'intégration réelle)
├── utils/
│   ├── activity_logger.py         ← Log partagé de tous les agents → data/activity_log.jsonl
│   ├── alert_detector.py          ← 🆕 Détection alertes marchés (mouvements significatifs)
│   ├── api_retry.py               ← 🆕 Retry automatique sur les appels API
│   ├── data_validator.py          ← 🆕 Validation des données veille/analyses
│   ├── file_lock.py               ← 🆕 Verrou fichier anti-corruption
│   └── __init__.py
├── data/
│   ├── activity_log.jsonl         ← Journal de toute l'activité des agents (append-only)
│   ├── activity_feed.json         ← Export JSON public lu par dashboard-agents.html
│   ├── subscribers.csv            ← Liste abonnés (email, prénom, source, actif)
│   ├── newsletters.json           ← Index des 5 éditions publiées
│   ├── portfolio.json             ← Portefeuille IA (3 profils, positions actives)
│   ├── portfolio_public.json      ← 🆕 Version publique du portfolio (pour le site)
│   ├── contenu_da.json            ← Insights géopolitiques générés par agent_da_site
│   ├── dernier_rapport_veille.json← Dernières données marchés collectées
│   ├── agent_memory.json          ← Mémoire persistante de l'orchestrateur
│   ├── analyste_memory.json       ← 🆕 Mémoire de l'analyste
│   ├── adjoint_log.json           ← 🆕 Log structuré du directeur adjoint
│   ├── alerts.json                ← 🆕 Alertes marchés en cours
│   ├── orchestrateur_schedule.json← 🆕 État du planning (tâches complétées aujourd'hui)
│   ├── orchestrateur.lock         ← 🆕 Lock anti-doublon orchestrateur
│   ├── previous_prices.json       ← 🆕 Prix précédents (pour calcul variations)
│   ├── prospects.csv              ← Prospects sponsors
│   ├── send_log.csv               ← Log des emails envoyés
│   ├── booster_score.json         ← Score de croissance
│   ├── costs.csv                  ← Coûts API
│   └── revenues.csv               ← Revenus
├── outputs/                       ← Fichiers générés quotidiennement
│   ├── alphabot_newsletter_YYYY-MM-DD.html  ← Newsletter du jour
│   ├── alphabot_dashboard_YYYY-MM-DD.html   ← Dashboard analytics du jour
│   ├── rapport_adjoint_YYYY-MM-DD.html      ← Rapport CEO quotidien
│   ├── section_da_YYYY-MM-DD.html           ← Section géopolitique du jour
│   ├── growth_strategy_YYYY-MM-DD.html      ← Stratégie de croissance
│   ├── ceo_brief_YYYY-MM-DD.html            ← Brief CEO
│   └── twitter_plan_YYYY-MM-DD.html         ← Plan Twitter (archivé)
├── scripts/                       ← 🆕 Scripts utilitaires (déplacés ici)
│   ├── RATTRAPAGE_MATIN.bat       ← Double-clic → lance rattrapage.py (Windows)
│   ├── lancer_orchestrateur.bat   ← Lance orchestrateur.py
│   ├── lancer_monitor.bat         ← Lance monitor.py
│   ├── lancer_agents.bat          ← Lance tous les agents
│   ├── installer_demarrage_auto.bat ← Configure démarrage auto Windows
│   ├── auto_push.py               ← Push auto vers GitHub
│   ├── sync_netlify.py            ← Sync abonnés (historique)
│   ├── update_prices.py           ← 🆕 MAJ prix live pour le site
│   ├── test_twitter.py            ← Test connexion Twitter
│   └── example_trader_usage.py    ← Exemple d'utilisation du robot trader
├── templates/                     ← 🆕 Templates email
│   ├── preview_email_bienvenue.html
│   └── template_emailjs_bienvenue.html
├── docs/                          ← 🆕 Documentation
│   ├── ALPHABOT_BRIEF_CLAUDE_PROJECTS.md  ← CE FICHIER
│   ├── ANALYSE_PROJET_AZ.md
│   ├── ROBOT_TRADER_README.md
│   ├── TRADER_INTEGRATION_GUIDE.md
│   ├── TWITTER_PLAYBOOK.md
│   └── contenu_acquisition.md
├── assets/                        ← 🆕 Assets statiques
│   ├── alphabot_twitter_pp.png
│   ├── alphabot_twitter_pp.svg
│   └── gate_subscriber.js        ← Script gate abonnés
├── .github/workflows/static.yml   ← 🆕 GitHub Actions — déploiement auto Pages
│
├── orchestrateur.py               ← Cerveau central — gère le planning 7h30-22h30
├── rattrapage.py                  ← Script de rattrapage matin (si PC était éteint)
├── auto_push.py                   ← Push auto GitHub après chaque tâche
├── config.py                      ← Config centrale (actifs suivis, modèle Claude)
├── monitor.py                     ← Moniteur terminal temps réel de l'activité
├── main.py                        ← Point d'entrée alternatif
├── directives.txt                 ← Canal CEO → Agents
├── gate_subscriber.js             ← Gate abonnés (copie racine pour le site)
├── favicon.svg                    ← 🆕 Favicon du site
│
├── index.html                     ← Page d'accueil du site public
├── newsletter.html                ← Page newsletter (dropdown éditions)
├── newsletters.html               ← Archive de toutes les éditions
├── investissement.html            ← Page portefeuille IA (3 profils)
├── arena.html                     ← 🆕 Arena — comparaison 3 robots traders en live
├── dashboard-agents.html          ← Dashboard activité agents
├── dashboard-ceo.html             ← Dashboard CEO
├── espace-pilotage.html           ← Dashboard CEO privé
├── 404.html                       ← 🆕 Page 404 personnalisée
├── communaute.html                ← 🆕 Page communauté (placeholder)
├── landing_page.html              ← Landing page alternative
│
├── .env                           ← Secrets (ne jamais commit)
├── .gitignore                     ← Exclut agents/, utils/, *.py, .env du repo Git
├── .nojekyll                      ← 🆕 Désactive Jekyll sur GitHub Pages
├── requirements.txt               ← Dépendances Python
└── RAPPORT_AUDIT_2026-03-24.md    ← 🆕 Dernier rapport d'audit
```

---

## ⚙️ Configuration technique

### Variables d'environnement (`.env`)
```
ANTHROPIC_API_KEY=sk-ant-...         # Clé API Anthropic
ALPHABOT_EMAIL=antoine.metout@gmail.com
ALPHABOT_PASSWORD=pjzypoqtjkicznem   # App password Gmail
TWITTER_API_KEY=...                   # (désactivé)
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_SECRET=...
TWITTER_BEARER_TOKEN=...
```

### `config.py` — Actifs suivis
```python
CRYPTO_IDS = ["bitcoin"]             # 1 seule crypto suivie

STOCK_INDICES = {
    "CAC 40": "^FCHI", "S&P 500": "^GSPC",
    "Nasdaq 100": "^NDX", "DAX": "^GDAXI", "Dow Jones": "^DJI"
}

COMMODITIES = {
    "Dollar Index (DXY)": "DX-Y.NYB", "Pétrole WTI": "CL=F",
    "Or (XAU/USD)": "GC=F", "EUR/USD": "EURUSD=X"
}

WATCHLIST_STOCKS = {
    "Apple": "AAPL", "NVIDIA": "NVDA", "Tesla": "TSLA",
    "LVMH": "MC.PA", "TotalEnergies": "TTE.PA",
    "ExxonMobil": "XOM", "Lockheed Martin": "LMT"
}

# URL du site — GitHub Pages (ancien Netlify abandonné)
SITE_URL = "https://antoinemetout-alphabot.github.io/alphabot-weekly"

CLAUDE_MODEL = "claude-sonnet-4-6"
OUTPUT_DIR = "outputs"
```

### Déploiement — GitHub Pages (remplace Netlify)
- **Repo** : `antoinemetout-alphabot/alphabot-weekly`
- **Branch** : `main`
- **GitHub Actions** : `.github/workflows/static.yml` déploie automatiquement sur push
- **`auto_push.py`** : pousse les fichiers HTML/JSON/CSV vers GitHub après chaque tâche
- **`.gitignore`** : exclut les agents Python, utils, .env — seuls les fichiers du site sont sur GitHub
- **`.nojekyll`** : désactive le traitement Jekyll

---

## 🗓️ Planning orchestrateur (7h30-22h30, tous les jours)

### Tâches principales (tous les jours)

| Heure | Tâche | Agent | ID |
|-------|-------|-------|-----|
| 07:30 | Newsletter quotidienne (pipeline complet) | Pipeline | `newsletter_lundi` |
| 07:45 | Sync abonnés | sync_netlify | `sync_netlify` |
| 08:00 | Directeur Adjoint matin | agent_adjoint | `adjoint_matin` |
| 08:30 | Veille marchés ouverture | agent_veille | `veille_matin` |
| 08:50 | Email quotidien CEO | agent_growth | `email_ceo_matin` |
| 09:30 | DA Site (insights géo) | agent_da_site | `da_site` |
| 09:45 | Investissement IA | agent_investissement | `investissement` |
| 12:00 | Veille marchés midi | agent_veille | `veille_midi` |
| 14:30 | Veille marchés après-midi | agent_veille | `veille_apm` |
| 16:30 | Analytics | agent_analytics | `analytics` |
| 22:15 | Directeur Adjoint soir + rapport CEO | agent_adjoint | `adjoint_soir` |

### 🤖 Robot Trader (lundi-vendredi uniquement)

| Heure | Session | ID |
|-------|---------|-----|
| 09:00 | Ouverture Europe | `trader_09h` |
| 10:30 | Matinée EU | `trader_10h30` |
| 12:00 | Midi EU | `trader_12h` |
| 14:00 | Pré-ouverture US | `trader_14h` |
| 15:45 | Ouverture US (moment clé) | `trader_15h45` |
| 16:30 | Overlap EU/US (liquidité max) | `trader_16h30` |
| 17:30 | Clôture Europe | `trader_17h30` |
| 19:00 | Soirée US | `trader_19h` |
| 20:30 | Pré-clôture US | `trader_20h30` |
| 22:00 | Clôture US | `trader_22h` |

### 📊 Prix Live (lundi-vendredi, ~toutes les 30 min de 9h15 à 21h45)

16 points de MAJ prix par jour pour alimenter le site en données temps réel.

### 🔍 Veille Continue (toutes les 15 min de 8h45 à 22h)

Scan alertes permanent — détecte mouvements significatifs + news breaking. Résultats sur le dashboard, pas de notification email. Couvre aussi le weekend (scan crypto).

### ❌ Agents DÉSACTIVÉS (depuis audit J3 — 22/03/2026)

| Agent | Raison | Condition de réactivation |
|-------|--------|--------------------------|
| Growth Booster (×3/jour) | Crashe, pas d'intégration réelle | API LinkedIn/Twitter fonctionnelles |
| Commercial (×2/jour) | Inutile avec 2 abonnés | 100+ abonnés |
| CFO | 0€ de revenu | Revenu ≥ 100€/mois |
| Twitter (×3/jour) | Antoine n'utilise plus Twitter | Décision CEO |

---

## 🤖 Les agents — Rôles détaillés

### 1. `agent_veille.py` — Collecte données
- Récupère Bitcoin (CoinGecko), indices boursiers, matières premières, devises via yfinance
- Retourne un dict `rapport` utilisé par tous les autres agents
- Appel : `AgentVeille().collecter()`

### 2. `agent_analyste.py` — Analyse IA
- Génère des analyses textuelles sur crypto, macro, géopolitique, bourse, synthèse
- Dispose d'une **mémoire persistante** (`data/analyste_memory.json`)
- **Style éditorial OBLIGATOIRE** : inspiré aktionnaire.com
  - Chaque section commence par un FAIT concret avec un chiffre
  - Titres `##` sont des accroches journalistiques (ex: "Bitcoin résiste, les mineurs capitulent")
  - 4 sections structurées avec `##` : Vue d'ensemble, Mouvements notables, Ce que ça signifie, Point clé
  - Jamais de phrases génériques
- Appel : `AgentAnalyste().analyser(rapport)`

### 3. `agent_redacteur.py` — Rédaction newsletter
- Génère la newsletter HTML complète dans `outputs/alphabot_newsletter_YYYY-MM-DD.html`
- Copie aussi dans le dossier racine pour le site
- **Structure newsletter** (dans cet ordre) :
  1. Header AlphaBot + date
  2. KPI Bar (Bitcoin, DXY, Or, S&P, Pétrole)
  3. Fear & Greed Index
  4. Section Macro (analyse macro)
  5. Insights Géopolitiques (depuis `data/contenu_da.json`)
  6. Section Bourse (stocks avec logos Clearbit)
  7. Synthèse IA
  8. Section News
  9. Concept de la semaine
  10. **Section Crypto en avant-dernière position**
  11. Footer
- **Logos stocks** : Clearbit API `https://logo.clearbit.com/{domain}`
- **Logos crypto** : `https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@latest/svg/color/{sym}.svg`
- **CSS** : `.wrap` max-width 1400px (full-width), `.nl-h2` avec soulignement cyan, `.section:hover` avec glow cyan
- **`_md()` function** : convertit markdown en HTML — rend les `## Titre` en `<h2 class="nl-h2">` ← CRITIQUE
- Met à jour `data/newsletters.json` après chaque génération
- Appel : `AgentRedacteur().rediger_newsletter(analyses)`

### 4. `agent_growth.py` — Gestion abonnés & emails
- Gère `data/subscribers.csv`
- Envoi newsletter complète SMTP Gmail
- **`envoyer_notification_quotidienne(chemin_newsletter)`** : envoie email avec titres + lien vers le site
- Appel : `AgentGrowth().envoyer_newsletter(chemin)`, `.envoyer_notification_quotidienne(chemin)`

### 5. `agent_da_site.py` — Design Aesthetic (DA)
- **Mission : améliorer l'ENSEMBLE du site** (pas seulement géopolitique)
- Méthodes principales :
  - `auditer_esthetique_site()` → score/100 sur tous les HTML
  - `harmoniser_navigation()` → ajoute liens manquants dans toutes les pages
  - `generer_ameliorations_visuelles_claude()` → demande à Claude du CSS amélioré
  - `ameliorer_esthetique_page(html_file)` → injecte le CSS avant `</head>` avec marqueur daté
  - `injecter_insights_dans_index()` → place les cartes géopolitiques dans index.html
  - `run_mission_da_complete()` → pipeline complet en 5 étapes
- **ATTENTION bugs connus** :
  - Claude retourne parfois le CSS avec des backticks markdown → regex de nettoyage dans la méthode
  - Le CSS doit toujours avoir `<style>` ET `</style>` correctement fermés sinon le site devient blanc
  - Marqueur d'injection : `<!-- DA-AMELIORATIONS-YYYY-MM-DD -->` pour éviter les doublons

### 6. `agent_adjoint.py` — Directeur Adjoint
- Scan complet du projet (agents, abonnés, KPIs)
- Supervise l'équipe → détecte retards et problèmes
- Analyse avec Claude → génère plan d'action
- Envoie rapport HTML par email à Antoine (22h15)
- Canal de directives : `directives.txt`
- Log structuré dans `data/adjoint_log.json`
- Appel : `AgentAdjoint().run(envoyer_email=True/False)`

### 7. `agent_investissement.py` — Portefeuille IA
- Gère `data/portfolio.json` — **3 profils de robots** :
  - **Robot Prudent** : obligations, ETF défensifs (capital initial 10 000€, performance +0.14%)
  - **Robot Modéré** : mix actions/ETF
  - **Robot Agressif** : positions plus risquées
- Publie `data/portfolio_public.json` pour le site
- Appel : `AgentInvestissement().run(donnees_veille=donnees)`

### 8. `agent_trader.py` — 🆕 Robot Trader
- Trading actif intraday/swing sur marchés EU et US
- 10 sessions par jour (lun-ven), calées sur les horaires réels des marchés :
  - Ouverture Europe (9h) → Clôture US (22h)
- Analyse positions, calcule P&L, évalue nouvelles opportunités
- Documentation : `docs/ROBOT_TRADER_README.md`

### 9. `agent_linkedin.py` — 🆕 Agent LinkedIn
- Génère automatiquement 7 posts LinkedIn chaque lundi matin (7h00)
- Utilise les données fraîches : veille marchés, portfolio, stats agents
- 7 types de posts en rotation : lancement, extrait newsletter, infographie portfolio, behind the scenes, quiz éducatif, storytelling, récap semaine
- Sauvegarde dans `docs/LINKEDIN_POSTS_SEMAINE.md` (copier-coller) + `data/linkedin_posts.json`
- Antoine doit publier manuellement sur LinkedIn (pas d'API gratuite)
- Appel : `AgentLinkedIn().run()`

### 10. `agent_twitter.py` — @AlphaBot_Weekly (DÉSACTIVÉ)
- 3 tweets par jour (matin, midi, soir) — actuellement désactivé par décision CEO
- Credentials Twitter possiblement expirés

### 10. `agent_analytics.py` — Métriques
- Génère dashboard HTML des KPIs dans `outputs/`

### 11-13. Agents DÉSACTIVÉS
- **agent_commercial.py** : prospection sponsors — réactivation à 100+ abonnés
- **agent_cfo.py** : rapport financier — réactivation quand revenu ≥ 100€/mois
- **agent_growth_booster.py** : contenu viral — réactivation quand API intégrées

---

## 🎨 Design System du site

### CSS Variables
```css
--bg:#04091a; --bg2:#060d1f;          /* Fond dark navy */
--gold:#f5c842;                        /* Or/jaune */
--blue:#3b82f6;                        /* Bleu */
--cyan:#22d3ee;                        /* Cyan (couleur principale accent) */
--green:#22c55e; --red:#ef4444;
--text:#e2e8f0; --muted:#64748b;
```

### Fonts
- `Space Grotesk` : titres et nav-brand
- `Inter` : corps de texte
- `JetBrains Mono` : données, timestamps (sur dashboard-agents.html)

### Éléments récurrents
- `.orb` : cercles floutés animés en arrière-plan
- `.scan` : ligne de scan animée qui traverse la page de haut en bas
- `.bg-grid` : grille en points bleus très subtile
- `.nav-cta` : bouton gradient bleu→cyan dans la nav

### Navigation actuelle (toutes les pages publiques)
```html
<a href="index.html">Accueil</a>
<a href="newsletter.html">Newsletter</a>
<a href="investissement.html">Investissement</a>
<a href="arena.html">Arena</a>
<a href="dashboard-agents.html">Agents</a>
<a href="newsletter.html" class="nav-cta">S'abonner gratuitement</a>
```

---

## 📊 État des agents au 24 mars 2026

| Agent | Statut | Détails |
|-------|--------|---------|
| Orchestrateur | ✅ Actif 7h30-22h30 | ~60 tâches/jour (veille + trader + scans + prix) |
| Agent Veille | ✅ Actif | 3 collectes/jour (matin, midi, après-midi) |
| Agent Analyste | ✅ Actif | Analyse quotidienne avec mémoire persistante |
| Agent Rédacteur | ✅ Actif | 5 newsletters générées (20-24 mars) |
| Agent Growth | ✅ Actif | Newsletter envoyée + notification CEO |
| Agent DA Site | ✅ Actif | Insights géo quotidiens, amélioration continue |
| Directeur Adjoint | ✅ Actif | Rapport CEO à 22h15 |
| Agent Investissement | ✅ Actif | 3 profils, positions ouvertes |
| Robot Trader | ✅ Actif | 10 sessions/jour lun-ven |
| Prix Live | ✅ Actif | 16 MAJ/jour |
| Veille Continue | ✅ Actif | Scan alertes toutes les 15 min |
| Agent Analytics | ✅ Actif | Dashboard quotidien |
| Agent LinkedIn | ✅ Actif | 7 posts/semaine générés le lundi à 7h00 |
| Agent Twitter | ❌ Désactivé | Décision CEO |
| Growth Booster | ❌ Désactivé | Pas d'intégration réelle |
| Commercial | ❌ Désactivé | Trop tôt (2 abonnés) |
| CFO | ❌ Désactivé | 0€ revenu |

---

## 🌐 Site Web — Pages existantes

| Fichier | URL publique | Rôle |
|---------|-------------|------|
| `index.html` | / | Page d'accueil publique |
| `newsletter.html` | /newsletter.html | Lecteur newsletter avec dropdown 5 éditions |
| `newsletters.html` | /newsletters.html | Archive toutes les éditions |
| `investissement.html` | /investissement.html | Portefeuille IA public (3 profils) |
| `arena.html` | /arena.html | 🆕 Arena — comparaison 3 robots traders en live |
| `dashboard-agents.html` | /dashboard-agents.html | Dashboard activité agents |
| `dashboard-ceo.html` | /dashboard-ceo.html | Dashboard CEO |
| `espace-pilotage.html` | /espace-pilotage.html | Dashboard CEO privé |
| `communaute.html` | /communaute.html | 🆕 Page communauté (placeholder) |
| `404.html` | (auto) | 🆕 Page 404 personnalisée |
| `landing_page.html` | /landing_page.html | Landing alternative |

### Gate Abonnés
- **`gate_subscriber.js`** : script qui vérifie si l'utilisateur est abonné avant d'afficher le contenu premium
- Utilise `sessionStorage` pour partager la session entre les pages
- Peut être inclus sur n'importe quelle page avec `<div id="ab-gate">` + `<div id="ab-content" style="display:none">`

---

## 📡 Dashboard Agents

**Fichier** : `dashboard-agents.html`

**Fonctionnement** :
1. L'orchestrateur génère `data/activity_feed.json` après chaque tâche
2. La page HTML lit ce JSON via `fetch()` toutes les 30 secondes
3. Affiche : KPIs du jour, statut de chaque agent, journal d'activité avec filtres

**`data/activity_feed.json`** — structure :
```json
{
  "generated_at": "2026-03-24T19:01:06",
  "total_events": 58,
  "events": [{"ts":"...","agent":"...","type":"success","message":"...","data":{}}],
  "agents": [{"agent":"Orchestrateur","last_ts":"...","last_type":"success","total_today":12,"errors_today":0,"successes_today":8}]
}
```

**Fonction Python** dans `utils/activity_logger.py` :
```python
from utils.activity_logger import exporter_activity_feed
exporter_activity_feed(100)  # génère data/activity_feed.json
```

---

## 🚦 Commandes importantes (à lancer depuis le dossier Alphabot)

```bash
# Orchestrateur principal (7h30-22h30, planning automatique)
python orchestrateur.py

# Rattrapage matin (si PC était éteint)
python rattrapage.py

# Voir le planning
python orchestrateur.py --status

# Reset complet (relance tout)
python orchestrateur.py --reset

# Lancer un agent individuellement
python -c "from agents.agent_veille import AgentVeille; print(AgentVeille().collecter())"

# Générer le feed du dashboard
python -c "from utils.activity_logger import exporter_activity_feed; exporter_activity_feed(100)"

# Push manuel vers GitHub
python auto_push.py

# Surveiller l'activité en temps réel
python monitor.py
```

---

## 📋 Fichier de log — Format

`data/activity_log.jsonl` — une ligne JSON par événement :
```json
{"ts": "2026-03-24T11:43:55.199", "agent": "Agent DA Site", "type": "success", "message": "Mission DA terminée (3 pages améliorées)", "data": {...}}
```

Types d'événements : `start`, `progress`, `success`, `error`, `warning`, `info`, `milestone`

---

## 🔧 Déploiement — GitHub Pages (remplace Netlify)

Le site est **statique** (HTML pur), hébergé sur **GitHub Pages**.

### Déploiement automatique
1. `auto_push.py` est appelé par l'orchestrateur après chaque tâche
2. Il copie les fichiers HTML, JSON, CSV, assets dans un clone shallow du repo
3. Commit + push automatique vers `main`
4. GitHub Actions (`.github/workflows/static.yml`) déploie automatiquement

### Déploiement manuel
```bash
python auto_push.py
```

**IMPORTANT** : `data/activity_feed.json` et `data/portfolio_public.json` doivent être poussés pour que le dashboard et la page investissement soient fonctionnels.

---

## ⚠️ Problèmes connus à résoudre

1. **Twitter désactivé** : les credentials Twitter sont expirés et Antoine n'utilise plus Twitter pour l'instant. À régénérer si décision de réactiver.

2. **DA Site — CSS injection** : si l'agent DA injecte du CSS avec des backticks markdown `` ```css ``, le site devient blanc. La regex de nettoyage existe dans `agent_da_site.py` mais surveiller. Si le site redevient blanc, chercher dans les fichiers HTML la présence de `` ``` `` et supprimer.

3. **Proxy système** : certains VPN/antivirus configurent des proxys locaux qui bloquent les requêtes des agents. `config.py` nettoie automatiquement `HTTP_PROXY`/`HTTPS_PROXY` au démarrage.

4. **PC en veille** : l'orchestrateur ne peut pas démarrer si le PC est en veille. Solution configurée dans le Planificateur de tâches Windows avec "Sortir l'ordinateur du mode veille".

5. **Fichiers "- Copie"** : plusieurs agents ont des copies de sauvegarde dans `agents/` (ex: `agent_redacteur - Copie.py`). Ces fichiers sont des snapshots de sécurité, pas des versions actives.

---

## 🎯 Objectifs stratégiques du projet

| Horizon | Objectif |
|---------|---------|
| Court terme | 50 abonnés réels, newsletter quotidienne |
| Moyen terme | 500 abonnés, 1er sponsor |
| Long terme | 5 000 abonnés, monétisation ads + sponsors |
| Portefeuille | 10 000€ → 100 000€ via 3 profils robots IA |

---

## 💬 Instructions pour Claude Projects

Tu es l'assistant technique et stratégique d'**Antoine Metout**, CEO fondateur d'AlphaBot Weekly.

**Tes responsabilités** :
- Modifier, créer et améliorer les fichiers Python et HTML du projet
- Tout expliquer en **français simple**, sans jargon technique inutile
- Toujours préférer l'action à l'explication — Antoine veut des résultats, pas des cours
- Quand tu modifies un fichier, **montrer le résultat final** et confirmer que c'est sauvegardé
- Ne jamais casser le site (toujours vérifier que les balises `<style>` sont bien fermées avant `</head>`)
- Si Antoine dit "fais-le" → le faire sans redemander confirmation
- Suggérer proactivement des améliorations quand tu vois quelque chose à optimiser

**Règle d'or** : Antoine ne développe pas. Tu es ses mains + son cerveau technique. Chaque réponse doit aboutir à quelque chose de concret et directement utilisable.

---

*Document mis à jour le 24 mars 2026*