# 🤖 AlphaBot Weekly — Brief Complet pour Claude Projects

> **Ce document est le contexte de démarrage à coller dans Claude Projects.**
> Il remplace l'intégralité des conversations passées. Tu as ici TOUTES les informations nécessaires pour continuer le travail sur le projet AlphaBot Weekly.

---

## 👤 Qui est Antoine ?

- **Nom** : Antoine Metout — `antoine.metout@gmail.com`
- **Rôle** : CEO fondateur du projet AlphaBot Weekly
- **Profil** : Non-développeur. Il ne code pas, ne lit pas Python. Il donne des directives en français et attend que Claude exécute tout de manière autonome.
- **Exigences** : Antoine veut un projet qui tourne **sans lui**, avec des agents IA autonomes qui travaillent chaque jour de 8h à 18h. Il veut **voir** le travail de ses agents (dashboard, emails, newsletters).
- **Style de communication** : Direct, en français, parfois impatient. Il n'aime pas les explications trop longues — il veut des résultats concrets.

---

## 📌 C'est quoi AlphaBot Weekly ?

Une **newsletter financière IA** qui décrypte la bourse et la géopolitique pour des investisseurs débutants francophones.

- **Site public** : hébergé sur Netlify (déploiement manuel par glisser-déposer)
- **Modèle** : newsletter gratuite → croissance abonnés → monétisation pub/sponsors
- **Philosophie éditoriale** : inspirée d'**aktionnaire.com** — chaque section commence par un FAIT concret avec un chiffre, titres accrocheurs, jamais de phrases génériques
- **Cible** : investisseurs débutants francophones, 25-45 ans
- **Abonnés actuels** : 6 (dont 1 réel — Antoine — et 5 simulés pour les tests)
- **Modèle Claude utilisé** : `claude-sonnet-4-6`

---

## 📁 Structure du projet

```
Alphabot/                          ← Dossier racine (sur le PC d'Antoine)
├── agents/                        ← Les 13 agents IA Python
│   ├── agent_veille.py            ← Collecte données marchés (yfinance, CoinGecko)
│   ├── agent_analyste.py          ← Analyse macro, géopolitique, crypto, bourse
│   ├── agent_redacteur.py         ← Rédige la newsletter HTML complète
│   ├── agent_growth.py            ← Gestion abonnés, envoi emails SMTP, notifications
│   ├── agent_da_site.py           ← Design/Aesthetic : améliore le site entier autonomement
│   ├── agent_adjoint.py           ← Directeur Adjoint : supervise tout, envoie rapport CEO
│   ├── agent_investissement.py    ← Gère le portefeuille IA (10k€ fictif → objectif 100k)
│   ├── agent_twitter.py           ← Poste sur @AlphaBot_Weekly (3 tweets/jour)
│   ├── agent_analytics.py         ← Dashboard métriques KPIs
│   ├── agent_commercial.py        ← Prospection sponsors, relances
│   ├── agent_cfo.py               ← Rapport financier mensuel
│   ├── agent_ceo_brief.py         ← Brief stratégique CEO
│   └── agent_growth_booster.py   ← Contenu viral, simulations croissance
├── utils/
│   ├── activity_logger.py         ← Log partagé de tous les agents → data/activity_log.jsonl
│   └── __init__.py
├── data/
│   ├── activity_log.jsonl         ← Journal de toute l'activité des agents (append-only)
│   ├── activity_feed.json         ← Export JSON public lu par dashboard-agents.html
│   ├── subscribers.csv            ← Liste abonnés (email, prénom, source, actif)
│   ├── newsletters.json           ← Index des éditions publiées (utilisé par newsletter.html)
│   ├── portfolio.json             ← Portefeuille IA (10k€ initial, 0 position ouverte)
│   ├── contenu_da.json            ← Insights géopolitiques générés par agent_da_site
│   ├── dernier_rapport_veille.json← Dernières données marchés collectées
│   ├── agent_memory.json          ← Mémoire persistante de l'orchestrateur
│   ├── prospects.csv              ← Prospects sponsors
│   ├── send_log.csv               ← Log des emails envoyés
│   └── booster_score.json         ← Score de croissance
├── outputs/                       ← Fichiers générés (newsletters HTML, rapports)
│   ├── alphabot_newsletter_YYYY-MM-DD.html  ← Newsletter du jour
│   ├── rapport_adjoint_YYYY-MM-DD.html      ← Rapport CEO quotidien
│   └── ...
├── orchestrateur.py               ← Cerveau central — gère le planning 8h-18h
├── rattrapage.py                  ← Script de rattrapage matin (si PC était éteint)
├── config.py                      ← Config centrale (actifs suivis, modèle Claude)
├── monitor.py                     ← Moniteur terminal temps réel de l'activité
├── sync_netlify.py                ← Sync abonnés depuis Netlify Forms
├── main.py                        ← Point d'entrée alternatif
├── directives.txt                 ← Canal CEO → Agents (Antoine écrit ses instructions ici)
│
├── index.html                     ← Page d'accueil du site public
├── newsletter.html                ← Page newsletter (dropdown éditions)
├── newsletters.html               ← Archive de toutes les éditions
├── investissement.html            ← Page portefeuille IA
├── dashboard-agents.html          ← Dashboard activité agents (NOUVEAU - créé le 21/03)
├── espace-pilotage.html           ← Dashboard CEO privé
├── dashboard-ceo.html             ← Dashboard CEO alternatif
├── landing_page.html              ← Landing page alternative
│
├── RATTRAPAGE_MATIN.bat           ← Double-clic → lance rattrapage.py (Windows)
├── lancer_orchestrateur.bat       ← Lance orchestrateur.py
├── lancer_monitor.bat             ← Lance monitor.py
├── installer_demarrage_auto.bat   ← Configure le démarrage auto Windows
├── .env                           ← Secrets (ne jamais commit)
├── config.py                      ← Configuration publique
└── requirements.txt               ← Dépendances Python
```

---

## ⚙️ Configuration technique

### Variables d'environnement (`.env`)
```
ANTHROPIC_API_KEY=sk-ant-...         # Clé API Anthropic
ALPHABOT_EMAIL=antoine.metout@gmail.com
ALPHABOT_PASSWORD=pjzypoqtjkicznem   # App password Gmail
TWITTER_API_KEY=...
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

CLAUDE_MODEL = "claude-sonnet-4-6"
OUTPUT_DIR = "outputs"
```

---

## 🗓️ Planning orchestrateur (8h-18h, tous les jours)

| Heure | Tâche | Agent | ID |
|-------|-------|-------|-----|
| 07:30 | Newsletter hebdo | Pipeline complet | `newsletter_lundi` (lundi only) |
| 07:45 | Sync abonnés Netlify | sync_netlify | `sync_netlify` |
| 08:00 | Directeur Adjoint matin | agent_adjoint | `adjoint_matin` |
| 08:30 | Veille marchés ouverture | agent_veille | `veille_matin` |
| 08:35 | Tweet matin | agent_twitter | `twitter_matin` |
| 08:50 | Email quotidien CEO | agent_growth | `email_ceo_matin` |
| 09:30 | DA Site (insights géo + amélio visuelle) | agent_da_site | `da_site` |
| 09:45 | Investissement IA | agent_investissement | `investissement` |
| 10:00 | Growth Booster session 1 | agent_growth_booster | `booster_1` |
| 11:00 | Commercial prospection | agent_commercial | `commercial_matin` |
| 12:00 | Veille marchés midi | agent_veille | `veille_midi` |
| 12:30 | Tweet midi | agent_twitter | `twitter_midi` |
| 13:30 | Growth Booster session 2 | agent_growth_booster | `booster_2` |
| 14:30 | Veille marchés après-midi | agent_veille | `veille_apm` |
| 15:30 | Growth Booster session 3 | agent_growth_booster | `booster_3` |
| 16:00 | Commercial relances | agent_commercial | `commercial_relances` |
| 16:30 | Analytics | agent_analytics | `analytics` |
| 16:45 | CFO rapport | agent_cfo | `cfo` |
| 17:30 | Directeur Adjoint soir + email CEO | agent_adjoint | `adjoint_soir` |
| 17:45 | Tweet soir | agent_twitter | `twitter_soir` |

---

## 🤖 Les 13 agents — Rôles détaillés

### 1. `agent_veille.py` — Collecte données
- Récupère Bitcoin (CoinGecko), indices boursiers, matières premières, devises via yfinance
- Retourne un dict `rapport` utilisé par tous les autres agents
- Appel : `AgentVeille().collecter()`

### 2. `agent_analyste.py` — Analyse IA
- Génère des analyses textuelles sur crypto, macro, géopolitique, bourse, synthèse
- **Style éditorial OBLIGATOIRE** : inspiré aktionnaire.com
  - Chaque section commence par un FAIT concret avec un chiffre
  - Titres `##` sont des accroches journalistiques (ex: "Bitcoin résiste, les mineurs capitulent")
  - 4 sections structurées avec `##` : Vue d'ensemble, Mouvements notables, Ce que ça signifie, Point clé
  - Jamais de phrases génériques
- Appel : `AgentAnalyste().analyser(rapport)`

### 3. `agent_redacteur.py` — Rédaction newsletter
- Génère la newsletter HTML complète dans `outputs/alphabot_newsletter_YYYY-MM-DD.html`
- Copie aussi dans le dossier racine pour Netlify
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

### 6. `agent_adjoint.py` — Directeur Adjoint (chef d'orchestre humain)
- Scan complet du projet (agents, abonnés, KPIs)
- Supervise l'équipe → détecte retards et problèmes
- Analyse avec Claude → génère plan d'action
- Envoie rapport HTML par email à Antoine (17h30)
- Canal de directives : `directives.txt`
- Appel : `AgentAdjoint().run(envoyer_email=True/False)`

### 7. `agent_investissement.py` — Portefeuille IA
- Gère `data/portfolio.json` (10 000€ initial, objectif 100 000€)
- 3 thèses actives : Bitcoin/DXY, Réarmement européen (LMT), Or géopolitique
- Évalue opportunités sur base données macro/géopolitiques
- Appel : `AgentInvestissement().run(donnees_veille=donnees)`

### 8. `agent_twitter.py` — @AlphaBot_Weekly
- 3 tweets par jour (matin, midi, soir)
- **Problème connu** : erreur 401 Unauthorized → credentials Twitter possiblement expirés
- À résoudre : régénérer les tokens sur developer.twitter.com

### 9. `agent_analytics.py` — Métriques
- Génère dashboard HTML des KPIs dans `outputs/`

### 10. `agent_commercial.py` — Prospection
- Génère emails de prospection sponsors
- Campagne de relances à J+7

### 11. `agent_cfo.py` — Finances
- Rapport mensuel financier (coûts API, revenus)

### 12. `agent_ceo_brief.py` — Brief stratégique CEO

### 13. `agent_growth_booster.py` — Croissance virale
- Simule profils d'abonnés, génère contenu LinkedIn/Twitter

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
<a href="dashboard-agents.html">Agents</a>
<a href="newsletter.html" class="nav-cta">S'abonner gratuitement</a>
```

---

## 📊 État des agents au 21 mars 2026

| Agent | Statut | Dernière action |
|-------|--------|----------------|
| Orchestrateur | ✅ Actif | Veille marchés après-midi |
| Agent DA Site | ✅ Actif | 3 pages améliorées (index, investissement, newsletter) |
| Directeur Adjoint | ✅ Actif | Rapport CEO envoyé à 11h45 |
| Agent Veille | ✅ Actif | Données collectées 3x dans la journée |
| Agent Growth | ✅ Actif | Newsletter envoyée + notification abonnés |
| Agent Rédacteur | ✅ Actif | Newsletter 21/03 générée |
| Agent Twitter | ❌ Erreur 401 | Credentials expirés — à régénérer |
| Agent Growth Booster | ✅ Actif | Session du matin effectuée |

---

## 🌐 Site Web — Pages existantes

| Fichier | URL publique | Rôle |
|---------|-------------|------|
| `index.html` | / | Page d'accueil publique |
| `newsletter.html` | /newsletter.html | Lecteur newsletter avec dropdown éditions |
| `newsletters.html` | /newsletters.html | Archive toutes les éditions |
| `investissement.html` | /investissement.html | Portefeuille IA public |
| `dashboard-agents.html` | /dashboard-agents.html | Dashboard activité agents (NOUVEAU 21/03) |
| `espace-pilotage.html` | /espace-pilotage.html | Dashboard CEO privé |
| `landing_page.html` | /landing_page.html | Landing alternative |

---

## 📡 Dashboard Agents (créé le 21/03/2026)

**Fichier** : `dashboard-agents.html`

**Fonctionnement** :
1. L'orchestrateur/rattrapage.py génère `data/activity_feed.json` après chaque tâche
2. La page HTML lit ce JSON via `fetch()` toutes les 30 secondes
3. Affiche : KPIs du jour, statut de chaque agent, journal d'activité avec filtres

**`data/activity_feed.json`** — structure :
```json
{
  "generated_at": "2026-03-21T14:42:35",
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
# Orchestrateur principal (8h-18h, planning automatique)
python orchestrateur.py

# Rattrapage matin (si PC était éteint)
python rattrapage.py
# Ou double-clic sur RATTRAPAGE_MATIN.bat

# Voir le planning
python orchestrateur.py --status

# Lancer un agent individuellement
python -c "from agents.agent_veille import AgentVeille; print(AgentVeille().collecter())"

# Générer le feed du dashboard
python -c "from utils.activity_logger import exporter_activity_feed; exporter_activity_feed(100)"

# Surveiller l'activité en temps réel
python monitor.py
```

---

## 📋 Fichier de log — Format

`data/activity_log.jsonl` — une ligne JSON par événement :
```json
{"ts": "2026-03-21T11:43:55.199", "agent": "Agent DA Site", "type": "success", "message": "Mission DA terminée (3 pages améliorées)", "data": {...}}
```

Types d'événements : `start`, `progress`, `success`, `error`, `warning`, `info`, `milestone`

---

## 🔧 Déploiement Netlify

Le site est **statique** (HTML pur). Pour mettre à jour le site en ligne :
1. Aller sur [app.netlify.com](https://app.netlify.com)
2. Cliquer sur le site AlphaBot
3. Onglet **Deploys**
4. **Glisser-déposer** le dossier `Alphabot` entier dans la zone prévue
5. Attendre ~30s → "Published" ✅

**IMPORTANT** : `data/activity_feed.json` doit être dans le dossier au moment du déploiement pour que le dashboard soit fonctionnel.

---

## ⚠️ Problèmes connus à résoudre

1. **Twitter 401 Unauthorized** : les credentials Twitter sont expirés. À régénérer sur [developer.twitter.com](https://developer.twitter.com), récupérer de nouveaux Access Tokens et les mettre dans `.env`.

2. **DA Site — CSS injection** : si l'agent DA injecte du CSS avec des backticks markdown `\`\`\`css`, le site devient blanc. La regex de nettoyage existe dans `agent_da_site.py` mais surveiller. Si le site redevient blanc, chercher dans les fichiers HTML la présence de `\`\`\`` et supprimer.

3. **`newsletters.json`** non mis à jour automatiquement : après chaque génération de newsletter, l'agent_redacteur doit mettre à jour `data/newsletters.json` pour que le dropdown de `newsletter.html` affiche la nouvelle édition. Vérifier que c'est bien le cas.

4. **PC en veille** : l'orchestrateur ne peut pas démarrer si le PC est en veille. Solution déjà configurée dans le Planificateur de tâches Windows avec "Sortir l'ordinateur du mode veille".

---

## 🎯 Objectifs stratégiques du projet

| Horizon | Objectif |
|---------|---------|
| Court terme | 50 abonnés réels, newsletter chaque semaine |
| Moyen terme | 500 abonnés, 1er sponsor |
| Long terme | 5 000 abonnés, monétisation ads + sponsors |
| Portefeuille | 10 000€ → 100 000€ via thèses géopolitiques IA |

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

*Document généré le 21 mars 2026 — à coller comme message initial dans Claude Projects*
