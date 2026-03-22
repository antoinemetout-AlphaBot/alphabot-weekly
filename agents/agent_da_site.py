"""
AlphaBot — Agent Directeur Artistique Site 🎨
Rôle : Générer des insights géopolitiques-marchés au format visuel "insight cards"
       pour le site web. Style : aktionnaire.com mais plus accessible aux débutants.

Structure : Données brutes → Claude (génération insights percutants) → HTML visuel
Format de sortie : Cards avec emoji catégorie, titre, contexte, impact marché, action cible, sévérité
"""

import os
import json
from datetime import datetime
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("⚠️  anthropic non disponible")
    anthropic = None

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, OUTPUT_DIR
try:
    from utils.activity_logger import log_event as _log
    _HAS_LOGGER = True
except Exception:
    def _log(*a, **k): pass
    _HAS_LOGGER = False

DATA_DIR = "data"


class AgentDASite:
    """Directeur Artistique qui génère des insights géopolitiques-marchés visuels."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if anthropic else None
        Path(OUTPUT_DIR).mkdir(exist_ok=True)
        Path(DATA_DIR).mkdir(exist_ok=True)
        print("🎨 Agent Directeur Artistique Site initialisé")

    # ═══════════════════════════════════════════════════════════════════════════
    # FALLBACK INSIGHTS (hardcoded)
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _get_fallback_insights() -> list:
        """Insights hardcodés si Claude n'est pas disponible."""
        return [
            {
                "id": "insight_btc_fed_001",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "categorie": "Crypto",
                "titre": "Bitcoin et la Fed : pourquoi les taux directeurs font trembler le BTC",
                "contexte": "La Réserve fédérale américaine maintient les taux d'intérêt élevés pour combattre l'inflation. Les investisseurs déplacent leurs capitaux vers des actifs sans rendement comme Bitcoin.",
                "impact_marche": "Impact majeur sur les cryptomonnaies. Indices tech (Nasdaq) également affectés par les craintes de taux stables.",
                "action_cible": {
                    "ticker": "BTC",
                    "nom": "Bitcoin",
                    "variation_pct": 2.3,
                    "prix_actuel": 67450.00,
                    "pourquoi": "Bitcoin agit comme valeur refuge quand la Fed maintient les taux élevés — or numérique d'inflation."
                },
                "severite": "MEDIUM",
                "emoji_categorie": "₿",
                "angle_alphabot": "Chaque hausse de taux Fed = achat Bitcoin. Comment cette relation géopolitique crée des opportunités pour les traders?"
            },
            {
                "id": "insight_defense_001",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "categorie": "Défense",
                "titre": "Réarmement européen : qui profite de la hausse des budgets défense ?",
                "contexte": "L'Europe augmente ses budgets militaires suite aux tensions géopolitiques. L'OTAN se réarme. Les contrats d'armements explosent.",
                "impact_marche": "Secteur de la défense en hausse. Actions de contractors militaires : LMT, RTX, BA en forte demande.",
                "action_cible": {
                    "ticker": "LMT",
                    "nom": "Lockheed Martin",
                    "variation_pct": 3.7,
                    "prix_actuel": 456.78,
                    "pourquoi": "Principal fournisseur de systèmes d'armes à l'OTAN. Réarmement européen = croissance organique guaranteed."
                },
                "severite": "HIGH",
                "emoji_categorie": "🛡️",
                "angle_alphabot": "Géopolitique 101 : tensions = contrats défense = résultats boursiers. Pourquoi les investisseurs ignorent encore ce levier?"
            },
            {
                "id": "insight_or_001",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "categorie": "Énergie",
                "titre": "Or au plus haut historique : signal d'alarme ou opportunité ?",
                "contexte": "L'or dépasse 2 400 USD/oz. Les banques centrales accumulent. C'est un signal classique de craintes géopolitiques et inflation.",
                "impact_marche": "Indices de risque (VIX) en hausse. USD faiblit. Secteur des matières premières survolte.",
                "action_cible": {
                    "ticker": "GLD",
                    "nom": "SPDR Gold Shares (ETF)",
                    "variation_pct": 5.2,
                    "prix_actuel": 189.45,
                    "pourquoi": "Meilleur proxy pour jouer l'or sans physique. Quand l'or monte, GLD monte. Diversification simple."
                },
                "severite": "CRITICAL",
                "emoji_categorie": "⚡",
                "angle_alphabot": "L'or à 2 400 USD = ce que dit le marché des 5 prochaines années. Suis-tu cet indicateur?"
            }
        ]

    # ═══════════════════════════════════════════════════════════════════════════
    # GENERATION INSIGHTS AVEC CLAUDE
    # ═══════════════════════════════════════════════════════════════════════════

    def generer_insights_geopolitiques(self, donnees_veille: dict = None) -> list:
        """
        Génère 3-5 insight cards percutants à partir de données de marché/géopolitique.
        Retourne une liste de dicts avec la structure complète des insights.
        """
        if not self.client:
            print("⚠️  Claude non disponible, utilisation insights fallback")
            return self._get_fallback_insights()

        # Si pas de données, utilise fallback
        if not donnees_veille:
            print("⚠️  Pas de données veille, utilisation fallback")
            return self._get_fallback_insights()

        # Forge le prompt pour Claude
        systeme = """Tu es le Directeur Artistique éditorial d'AlphaBot Weekly.
Ta mission : transformer des données de marché brutes en insights visuels percutants qui expliquent
le lien géopolitique → marché → action concrète pour des investisseurs débutants français.

Style : percutant, visuel, pédagogique. PAS de jargon financier.
Ton : journaliste d'investigation qui vulgarise.
Format : JSON valide uniquement.

Chaque insight DOIT avoir cette structure EXACTE:
{
  "id": "unique_id",
  "date": "2026-03-21",
  "categorie": "Géopolitique|Macro|Crypto|Énergie|Défense",
  "titre": "Titre accrocheur 8-10 mots",
  "contexte": "2 phrases de contexte simple pour débutants",
  "impact_marche": "Quel indice/secteur est impacté et dans quel sens",
  "action_cible": {
    "ticker": "TICKER",
    "nom": "Nom complet",
    "variation_pct": 2.3,
    "prix_actuel": 456.78,
    "pourquoi": "1 phrase expliquant le lien direct géopolitique→action"
  },
  "severite": "LOW|MEDIUM|HIGH|CRITICAL",
  "emoji_categorie": "🌍|💰|₿|⚡|🛡️",
  "angle_alphabot": "Ce que AlphaBot Weekly analyse en détail cette semaine sur ce sujet"
}

Retourne un ARRAY JSON valide [] avec 3-5 insights maximum.
"""

        user_prompt = f"""Données de veille actuelles:
{json.dumps(donnees_veille, ensure_ascii=False, indent=2)}

Génère 3-5 insight cards percutants basés sur ces données.
Chaque card doit avoir un lien CLAIR géopolitique → impact marché → ticker concret.
Sois direct, visuel, pédagogique. Pas de disclaimers financiers."""

        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=3000,
                system=systeme,
                messages=[{"role": "user", "content": user_prompt}]
            )

            # Parse la réponse JSON
            json_str = response.content[0].text.strip()
            # Nettoie les markdown backticks si présentes
            import re as _re
            json_str = _re.sub(r'```(?:json)?\s*', '', json_str).strip()
            if json_str.endswith("```"):
                json_str = json_str[:-3].strip()

            # Tente le parsing, si échoue tronque au dernier ] ou } valide
            try:
                insights = json.loads(json_str)
            except json.JSONDecodeError:
                # Cherche le dernier crochet fermant pour un array JSON valide
                last_bracket = json_str.rfind(']')
                if last_bracket > 0:
                    json_str = json_str[:last_bracket + 1]
                    # Ferme les objets/strings ouverts
                    try:
                        insights = json.loads(json_str)
                    except json.JSONDecodeError:
                        # Tente de réparer en fermant le dernier objet
                        json_str_fixed = json_str.rstrip().rstrip(',') + '}]'
                        try:
                            insights = json.loads(json_str_fixed)
                        except json.JSONDecodeError:
                            raise
                else:
                    raise

            # Valide la structure
            if not isinstance(insights, list):
                insights = [insights]

            for insight in insights:
                if "id" not in insight:
                    insight["id"] = f"insight_{insight.get('categorie', 'autre').lower()}_{datetime.now().timestamp():.0f}"

            if _HAS_LOGGER:
                _log("Agent DA Site", "success", f"Générés {len(insights)} insights géopolitiques", {"count": len(insights)})

            return insights

        except Exception as e:
            print(f"❌ Erreur Claude: {e}")
            if _HAS_LOGGER:
                _log("Agent DA Site", "error", f"Erreur génération insights: {str(e)}", {})
            return self._get_fallback_insights()

    # ═══════════════════════════════════════════════════════════════════════════
    # GENERATION HTML VISUEL
    # ═══════════════════════════════════════════════════════════════════════════

    def generer_section_editoriale_html(self, insights: list) -> str:
        """
        Génère une section HTML (pas full page) avec les insight cards.
        Design: dark navy glassmorphism, cards avec badges catégorie/sévérité.
        """
        if not insights:
            insights = self._get_fallback_insights()

        cards_html = ""

        for idx, insight in enumerate(insights):
            cat = insight.get("categorie", "Autre")
            titre = insight.get("titre", "Sans titre")
            contexte = insight.get("contexte", "")
            impact = insight.get("impact_marche", "")
            action = insight.get("action_cible", {})
            severite = insight.get("severite", "MEDIUM")
            emoji = insight.get("emoji_categorie", "🌍")
            angle = insight.get("angle_alphabot", "")

            # Couleurs sévérité
            sev_color = {
                "LOW": "#22c55e",
                "MEDIUM": "#eab308",
                "HIGH": "#f97316",
                "CRITICAL": "#ef4444"
            }.get(severite, "#64748b")

            ticker = action.get("ticker", "—")
            ticker_nom = action.get("nom", "")
            ticker_var = action.get("variation_pct", 0)
            ticker_prix = action.get("prix_actuel", 0)
            ticker_pourquoi = action.get("pourquoi", "")

            var_color = "#22c55e" if ticker_var >= 0 else "#ef4444"
            var_text = f"+{ticker_var:.1f}%" if ticker_var >= 0 else f"{ticker_var:.1f}%"

            cards_html += f"""
            <div class="insight-card">
              <div class="insight-header">
                <div class="insight-top">
                  <span class="insight-emoji">{emoji}</span>
                  <div class="insight-badges">
                    <span class="badge badge-cat">{cat}</span>
                    <span class="badge badge-sev" style="background:rgba({self._hex_to_rgb(sev_color)},.2);color:{sev_color};">{severite}</span>
                  </div>
                </div>
              </div>

              <h3 class="insight-titre">{titre}</h3>

              <p class="insight-contexte">{contexte}</p>

              <div class="insight-impact">
                <strong>→ Impact marché:</strong> {impact}
              </div>

              <div class="insight-stock">
                <div class="stock-ticker">
                  <div class="ticker-symbol">{ticker}</div>
                  <div class="ticker-name">{ticker_nom}</div>
                </div>
                <div class="ticker-price">
                  <div class="price-val">${ticker_prix:,.2f}</div>
                  <div class="price-var" style="color:{var_color};">{var_text}</div>
                </div>
              </div>

              <p class="insight-pourquoi">
                <strong>Pourquoi?</strong> {ticker_pourquoi}
              </p>

              <p class="insight-angle">
                <em>{angle}</em>
              </p>

              <a href="#" class="cta-lire">Lire dans la newsletter →</a>
            </div>
            """

        # Wrapper HTML complet avec styles
        html = f"""<!-- ─── SECTION INSIGHTS GÉOPOLITIQUES ─── -->
<section class="insights-section">
  <div class="insights-header">
    <h2>🌍 Insights Géopolitiques</h2>
    <p>Comment les grands événements mondiaux façonnent les marchés — et tes opportunités d'investissement.</p>
  </div>

  <div class="insights-grid">
    {cards_html}
  </div>
</section>

<!-- ─── STYLES INSIGHTS ─── -->
<style>
/* INSIGHTS SECTION */
.insights-section {{
  padding: 80px 5%;
  position: relative;
  z-index: 1;
}}

.insights-header {{
  text-align: center;
  max-width: 700px;
  margin: 0 auto 60px;
}}

.insights-header h2 {{
  font-family: 'Space Grotesk', sans-serif;
  font-size: clamp(28px, 4vw, 44px);
  font-weight: 800;
  line-height: 1.15;
  margin-bottom: 16px;
  color: white;
}}

.insights-header p {{
  font-size: 16px;
  color: #64748b;
  line-height: 1.7;
}}

/* INSIGHT CARDS */
.insights-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}}

.insight-card {{
  background: linear-gradient(135deg, rgba(255, 255, 255, .04), rgba(255, 255, 255, .02));
  border: 1px solid rgba(255, 255, 255, .08);
  border-radius: 16px;
  padding: 28px;
  transition: .3s;
  display: flex;
  flex-direction: column;
  gap: 16px;
}}

.insight-card:hover {{
  border-color: rgba(34, 211, 238, .3);
  transform: translateY(-4px);
  background: linear-gradient(135deg, rgba(255, 255, 255, .06), rgba(255, 255, 255, .03));
}}

/* HEADER */
.insight-header {{
  margin-bottom: 8px;
}}

.insight-top {{
  display: flex;
  align-items: center;
  gap: 12px;
}}

.insight-emoji {{
  font-size: 28px;
}}

.insight-badges {{
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}}

.badge {{
  font-size: 10px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 50px;
  text-transform: uppercase;
  letter-spacing: .5px;
}}

.badge-cat {{
  background: rgba(59, 130, 246, .2);
  color: #3b82f6;
}}

.badge-sev {{
  /* dynamique color */
}}

/* TITRE */
.insight-titre {{
  font-family: 'Space Grotesk', sans-serif;
  font-size: 16px;
  font-weight: 700;
  color: white;
  line-height: 1.4;
  margin: 0;
}}

/* CONTEXTE */
.insight-contexte {{
  font-size: 13px;
  color: #e2e8f0;
  line-height: 1.6;
  margin: 0;
}}

/* IMPACT */
.insight-impact {{
  font-size: 13px;
  color: #e2e8f0;
  padding: 12px;
  background: rgba(59, 130, 246, .08);
  border-left: 3px solid #3b82f6;
  border-radius: 4px;
}}

/* STOCK WIDGET */
.insight-stock {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: rgba(255, 255, 255, .04);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, .06);
}}

.stock-ticker {{
  display: flex;
  flex-direction: column;
  gap: 4px;
}}

.ticker-symbol {{
  font-family: 'Space Grotesk', sans-serif;
  font-size: 14px;
  font-weight: 700;
  color: white;
}}

.ticker-name {{
  font-size: 12px;
  color: #64748b;
}}

.ticker-price {{
  text-align: right;
}}

.price-val {{
  font-family: 'Space Grotesk', sans-serif;
  font-size: 16px;
  font-weight: 700;
  color: white;
}}

.price-var {{
  font-size: 12px;
  font-weight: 600;
  margin-top: 2px;
}}

/* POURQUOI */
.insight-pourquoi {{
  font-size: 13px;
  color: #e2e8f0;
  line-height: 1.6;
  margin: 0;
}}

/* ANGLE ALPHABOT */
.insight-angle {{
  font-size: 12px;
  color: #64748b;
  font-style: italic;
  margin: 0;
  padding: 12px;
  background: rgba(245, 200, 66, .05);
  border-radius: 4px;
}}

/* CTA */
.cta-lire {{
  align-self: flex-start;
  font-size: 12px;
  font-weight: 600;
  color: #22d3ee;
  text-decoration: none;
  transition: .2s;
  margin-top: auto;
}}

.cta-lire:hover {{
  color: #f5c842;
  text-decoration: underline;
}}

/* RESPONSIVE */
@media (max-width: 768px) {{
  .insights-section {{
    padding: 60px 5%;
  }}

  .insights-grid {{
    grid-template-columns: 1fr;
  }}

  .insight-card {{
    padding: 20px;
  }}

  .insight-titre {{
    font-size: 15px;
  }}

  .insight-contexte {{
    font-size: 12px;
  }}
}}
</style>
"""

        return html

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> str:
        """Convertit #RRGGBB en R,G,B."""
        hex_color = hex_color.lstrip("#")
        return ",".join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))

    # ═══════════════════════════════════════════════════════════════════════════
    # SAUVEGARDE CONTENU
    # ═══════════════════════════════════════════════════════════════════════════

    def sauvegarder_contenu(self, insights: list, section_html: str) -> str:
        """
        Sauvegarde les insights en JSON et la section HTML.
        Retourne le chemin du fichier HTML généré.
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # JSON insights
        insights_path = os.path.join(DATA_DIR, "contenu_da.json")
        with open(insights_path, "w", encoding="utf-8") as f:
            json.dump({"date": today, "insights": insights}, f, ensure_ascii=False, indent=2)

        # HTML section
        html_path = os.path.join(OUTPUT_DIR, f"section_da_{today}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(section_html)

        if _HAS_LOGGER:
            _log("Agent DA Site", "success", f"Contenu sauvegardé", {
                "insights_file": insights_path,
                "html_file": html_path
            })

        return html_path

    # ═══════════════════════════════════════════════════════════════════════════
    # RUN COMPLET
    # ═══════════════════════════════════════════════════════════════════════════

    def run(self, donnees_veille: dict = None) -> dict:
        """
        Cycle complet :
        1. Génère insights
        2. Génère HTML section
        3. Sauvegarde les deux
        4. Log l'activité
        5. Retourne un dict avec résultats

        Args:
            donnees_veille: dict optionnel avec données brutes de veille
                           Si None, utilise des données fallback

        Returns:
            {
                "success": bool,
                "insights_count": int,
                "html_path": str,
                "insights": list
            }
        """
        if _HAS_LOGGER:
            _log("Agent DA Site", "start", "Démarrage génération contenu éditorial")

        try:
            # Données fallback si rien fourni
            if not donnees_veille:
                donnees_veille = {
                    "marches": {
                        "indices": ["CAC 40", "S&P 500", "Nasdaq"],
                        "cryptos": ["Bitcoin", "Ethereum"],
                        "commodities": ["Or", "Pétrole"]
                    },
                    "geopolitique": ["Tensions Ukraine", "Politique monétaire Fed", "Réarmement OTAN"],
                    "date": datetime.now().strftime("%Y-%m-%d")
                }

            # 1. Génère insights
            insights = self.generer_insights_geopolitiques(donnees_veille)

            # 2. Génère HTML
            html = self.generer_section_editoriale_html(insights)

            # 3. Sauvegarde
            html_path = self.sauvegarder_contenu(insights, html)

            if _HAS_LOGGER:
                _log("Agent DA Site", "success", f"Contenu éditorial généré ({len(insights)} insights)",
                     {"count": len(insights), "html_path": html_path})

            return {
                "success": True,
                "insights_count": len(insights),
                "html_path": html_path,
                "insights": insights
            }

        except Exception as e:
            print(f"❌ Erreur Agent DA Site: {e}")
            if _HAS_LOGGER:
                _log("Agent DA Site", "error", f"Erreur: {str(e)}", {})
            return {
                "success": False,
                "insights_count": 0,
                "html_path": "",
                "insights": []
            }

    # ═══════════════════════════════════════════════════════════════════════════
    # DIRECTEUR ARTISTIQUE — MISSION ESTHÉTIQUE GLOBALE DU SITE
    # ═══════════════════════════════════════════════════════════════════════════

    SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    HTML_PAGES = [
        "index.html",
        "investissement.html",
        "newsletter.html",
        "newsletters.html",
        "espace-pilotage.html",
    ]

    def auditer_esthetique_site(self) -> dict:
        """
        Lit tous les fichiers HTML du site et produit un audit esthétique complet.
        Détecte : incohérences nav, pages sans liens, sections manquantes, etc.
        """
        import re
        audit = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "pages": {},
            "problemes": [],
            "score_global": 0,
        }

        for page in self.HTML_PAGES:
            filepath = os.path.join(self.SITE_DIR, page)
            if not os.path.exists(filepath):
                audit["pages"][page] = {"existe": False}
                audit["problemes"].append(f"Page manquante: {page}")
                continue

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Extraire les liens de nav
            nav_links = re.findall(r'href="([^"#]+\.html)"', content)
            nav_links = list(set(nav_links))

            info = {
                "existe": True,
                "taille_ko": round(len(content) / 1024, 1),
                "has_nav": "<nav" in content,
                "has_footer": "<footer" in content,
                "has_insights_section": "insights-section" in content,
                "has_investissement_link": "investissement.html" in content,
                "has_newsletter_link": "newsletter.html" in content,
                "liens_nav": nav_links,
                "has_mobile_menu": "toggleMenu" in content or "nav-hamburger" in content,
                "has_animations": "@keyframes" in content,
                "has_glassmorphism": "backdrop-filter" in content,
            }

            # Détecter les problèmes spécifiques
            if not info["has_investissement_link"] and page != "investissement.html":
                audit["problemes"].append(f"{page}: lien 'Investissement' manquant dans nav")
            if not info["has_nav"]:
                audit["problemes"].append(f"{page}: pas de balise <nav>")
            if not info["has_footer"]:
                audit["problemes"].append(f"{page}: pas de footer")
            if not info["has_mobile_menu"] and info["has_nav"]:
                audit["problemes"].append(f"{page}: menu mobile absent")

            audit["pages"][page] = info

        # Score: 100 - (10 points par problème)
        audit["score_global"] = max(0, 100 - len(audit["problemes"]) * 10)

        print(f"🔍 Audit terminé — Score: {audit['score_global']}/100 — {len(audit['problemes'])} problème(s)")
        for pb in audit["problemes"]:
            print(f"   ⚠️  {pb}")

        return audit

    def harmoniser_navigation(self) -> dict:
        """
        Synchronise la navigation sur toutes les pages HTML :
        - Ajoute le lien 'Investissement' si absent
        - Assure la cohérence logo / liens / CTA
        Retourne un dict page → "updated" | "already_ok" | "skipped"
        """
        resultats = {}

        for page in self.HTML_PAGES:
            if page == "dashboard-ceo.html":
                resultats[page] = "skipped"
                continue

            filepath = os.path.join(self.SITE_DIR, page)
            if not os.path.exists(filepath):
                resultats[page] = "missing"
                continue

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            modif = False

            # Ajouter lien Investissement dans la nav s'il est absent
            if "investissement.html" not in content and "<nav" in content:
                # On l'insère après le lien Newsletter
                if 'href="newsletter.html">Newsletter</a>' in content:
                    content = content.replace(
                        'href="newsletter.html">Newsletter</a>',
                        'href="newsletter.html">Newsletter</a>\n    <a href="investissement.html">Investissement</a>'
                    )
                    modif = True

            # Marquer le lien actif correctement selon la page
            active_href = page
            if modif or f'href="{active_href}" class="active"' not in content:
                # Enlève tous les "active" existants puis remet sur la bonne page
                import re
                content = re.sub(r' class="active"', '', content)
                content = content.replace(
                    f'href="{active_href}"',
                    f'href="{active_href}" class="active"',
                    1
                )
                modif = True

            if modif:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                resultats[page] = "updated"
                print(f"   ✅ Navigation mise à jour: {page}")
            else:
                resultats[page] = "already_ok"

        return resultats

    def injecter_insights_dans_index(self, insights: list) -> bool:
        """
        Injecte / met à jour la section insights géopolitiques dans index.html.
        Remplace la section si elle existe déjà, ou l'ajoute avant le footer.
        """
        import re
        index_path = os.path.join(self.SITE_DIR, "index.html")
        if not os.path.exists(index_path):
            print("❌ index.html introuvable")
            return False

        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()

        section_html = self.generer_section_editoriale_html(insights)

        MARKER_START = "<!-- ─── SECTION INSIGHTS GÉOPOLITIQUES ─── -->"
        MARKER_END = "<!-- ─── FIN INSIGHTS GÉOPOLITIQUES ─── -->"

        if MARKER_START in content:
            # Remplace la section existante
            pattern = re.compile(
                re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
                re.DOTALL
            )
            new_content = pattern.sub(
                MARKER_START + "\n" + section_html + "\n" + MARKER_END,
                content
            )
        else:
            # Insère avant le footer
            if "<footer" in content:
                new_content = content.replace(
                    "<footer",
                    MARKER_START + "\n" + section_html + "\n" + MARKER_END + "\n\n<footer",
                    1
                )
            else:
                new_content = content + "\n" + MARKER_START + "\n" + section_html + "\n" + MARKER_END

        with open(index_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print("✅ Insights injectés dans index.html")
        return True

    def generer_ameliorations_visuelles_claude(self, page: str, html_extrait: str) -> str:
        """
        Demande à Claude d'analyser l'extrait HTML d'une page et de retourner
        un bloc <style> avec des améliorations CSS concrètes et priorisées.
        Retourne une chaîne CSS prête à injecter.
        """
        if not self.client:
            return ""

        systeme = """Tu es le Directeur Artistique senior d'AlphaBot Weekly.
Ton rôle : améliorer l'esthétique des pages HTML du site pour qu'il soit
plus beau, plus moderne et plus impressionnant visuellement.

Design system actuel : dark navy (#04091a), glassmorphism, Inter + Space Grotesk,
or (#f5c842), bleu (#3b82f6), cyan (#22d3ee), vert (#22c55e).

Tu dois retourner UNIQUEMENT un bloc CSS valide (pas de HTML, pas d'explication)
avec des améliorations concrètes :
- Meilleures animations (hover, entrée, transitions)
- Meilleure typographie (line-height, letter-spacing, weight contrasts)
- Meilleur espacement (padding, gap, margin)
- Effets visuels (box-shadow, gradient borders, glow effects)
- Micro-interactions (transform on hover, scale, opacity)
- Amélioration des cartes et conteneurs
- Amélioration des boutons et CTAs
Règle absolue : les améliorations doivent être NON-DESTRUCTIVES (complètes ou s'ajoutent
aux styles existants). Retourne seulement le CSS, entre balises <style> et </style>."""

        user_prompt = f"""Analyse cette page ({page}) et génère des améliorations CSS
pour la rendre plus belle et plus professionnelle.

Extrait HTML de la page (300 premières lignes) :
{html_extrait[:8000]}

Génère un bloc <style> compact avec tes meilleures améliorations visuelles.
Maximum 60 règles CSS. Focus sur l'impact visuel maximal."""

        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2000,
                system=systeme,
                messages=[{"role": "user", "content": user_prompt}]
            )
            css_block = response.content[0].text.strip()

            # Nettoie les markdown backticks si Claude les a ajoutés (```css, ```html, etc.)
            import re as _re
            css_block = _re.sub(r'^```\w*\n?', '', css_block)
            css_block = _re.sub(r'\n?```$', '', css_block)
            css_block = css_block.strip()

            # S'assure que c'est bien du CSS entre <style> tags
            if "<style>" not in css_block:
                css_block = f"<style>\n{css_block}\n</style>"
            return css_block
        except Exception as e:
            print(f"⚠️  Erreur génération CSS pour {page}: {e}")
            return ""

    def ameliorer_esthetique_page(self, page: str) -> dict:
        """
        Améliore l'esthétique d'une page HTML spécifique :
        1. Lit le HTML actuel
        2. Demande à Claude des améliorations CSS
        3. Injecte les améliorations avant </head>
        4. Sauvegarde
        """
        filepath = os.path.join(self.SITE_DIR, page)
        if not os.path.exists(filepath):
            return {"page": page, "status": "missing"}

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Vérifie si déjà amélioré aujourd'hui
        today = datetime.now().strftime("%Y-%m-%d")
        marker = f"<!-- DA-AMELIORATIONS-{today} -->"
        if marker in content:
            print(f"   ⏭️  {page}: déjà amélioré aujourd'hui")
            return {"page": page, "status": "already_done"}

        print(f"   🎨 Amélioration esthétique de {page}...")

        # Génère les améliorations CSS via Claude
        css_ameliorations = self.generer_ameliorations_visuelles_claude(page, content)

        if not css_ameliorations:
            return {"page": page, "status": "no_improvements"}

        # ── Validation CSS : s'assurer que <style> est bien fermé ──
        import re as _re
        # Nettoie les backticks markdown si présentes
        css_ameliorations = _re.sub(r'```(?:css|html)?\s*', '', css_ameliorations).strip()
        if css_ameliorations.endswith("```"):
            css_ameliorations = css_ameliorations[:-3].strip()
        # Assure que le bloc est wrappé dans <style>...</style>
        if "<style>" not in css_ameliorations:
            css_ameliorations = "<style>\n" + css_ameliorations
        if "</style>" not in css_ameliorations:
            # Tronqué par Claude — fermer proprement
            # Retire la dernière propriété incomplète (ligne sans } final)
            lines = css_ameliorations.rstrip().split('\n')
            while lines and not lines[-1].rstrip().endswith('}') and '</style>' not in lines[-1] and '<style>' not in lines[-1]:
                lines.pop()
            css_ameliorations = '\n'.join(lines) + "\n</style>"
            print(f"   ⚠️  CSS tronqué par Claude — fermé automatiquement ({len(lines)} lignes conservées)")

        # Injecte juste avant </head>
        injection = f"\n{marker}\n{css_ameliorations}\n"
        if "</head>" in content:
            new_content = content.replace("</head>", injection + "</head>", 1)
        else:
            new_content = content + injection

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

        css_rules = css_ameliorations.count("{")
        print(f"   ✅ {page}: {css_rules} règles CSS injectées")
        return {"page": page, "status": "improved", "css_rules": css_rules}

    def run_mission_da_complete(self, donnees_veille: dict = None) -> dict:
        """
        Mission DA complète — 5 étapes autonomes :
        1. Audit esthétique du site entier
        2. Harmonisation navigation (tous les liens cohérents)
        3. Génération et injection insights géopolitiques dans index.html
        4. Améliorations visuelles Claude sur chaque page
        5. Rapport de mission

        C'est la méthode appelée en production via l'orchestrateur.
        """
        if _HAS_LOGGER:
            _log("Agent DA Site", "start", "Mission DA complète démarrée")

        rapport = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "etapes": {},
            "success": False,
            "pages_ameliorees": 0,
            "insights_count": 0,
        }

        # ── ÉTAPE 1 : Audit ──────────────────────────────────────────────────
        print("\n🔍 ÉTAPE 1/5 — Audit esthétique du site")
        try:
            audit = self.auditer_esthetique_site()
            rapport["etapes"]["audit"] = {
                "ok": True,
                "score": audit["score_global"],
                "problemes": len(audit["problemes"])
            }
        except Exception as e:
            rapport["etapes"]["audit"] = {"ok": False, "erreur": str(e)}
            audit = {"problemes": [], "score_global": 0, "pages": {}}

        # ── ÉTAPE 2 : Harmonisation navigation ──────────────────────────────
        print("\n🔗 ÉTAPE 2/5 — Harmonisation navigation")
        try:
            nav_resultats = self.harmoniser_navigation()
            pages_maj = sum(1 for v in nav_resultats.values() if v == "updated")
            rapport["etapes"]["navigation"] = {"ok": True, "pages_mises_a_jour": pages_maj}
            print(f"   ✅ {pages_maj} page(s) mise(s) à jour")
        except Exception as e:
            rapport["etapes"]["navigation"] = {"ok": False, "erreur": str(e)}
            print(f"   ❌ Erreur: {e}")

        # ── ÉTAPE 3 : Insights géopolitiques → index.html ───────────────────
        print("\n🌍 ÉTAPE 3/5 — Génération et injection insights")
        try:
            if not donnees_veille:
                donnees_veille = {
                    "marches": {"indices": ["CAC 40", "S&P 500"], "cryptos": ["Bitcoin"]},
                    "geopolitique": ["Tensions géopolitiques mondiales", "Politique monétaire Fed",
                                     "Réarmement européen", "Dollar vs marchés émergents"],
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
            insights = self.generer_insights_geopolitiques(donnees_veille)
            injected = self.injecter_insights_dans_index(insights)
            html_path = self.sauvegarder_contenu(insights, self.generer_section_editoriale_html(insights))
            rapport["etapes"]["insights"] = {
                "ok": True,
                "count": len(insights),
                "injected_in_index": injected,
                "html_path": html_path
            }
            rapport["insights_count"] = len(insights)
        except Exception as e:
            rapport["etapes"]["insights"] = {"ok": False, "erreur": str(e)}
            insights = []
            print(f"   ❌ Erreur: {e}")

        # ── ÉTAPE 4 : Améliorations visuelles Claude ─────────────────────────
        print("\n🎨 ÉTAPE 4/5 — Améliorations visuelles par page")
        ameliorations = []
        pages_prioritaires = ["index.html", "investissement.html", "newsletter.html"]
        try:
            for page in pages_prioritaires:
                result = self.ameliorer_esthetique_page(page)
                ameliorations.append(result)
                if result.get("status") == "improved":
                    rapport["pages_ameliorees"] += 1
            rapport["etapes"]["visuels"] = {"ok": True, "details": ameliorations}
        except Exception as e:
            rapport["etapes"]["visuels"] = {"ok": False, "erreur": str(e)}
            print(f"   ❌ Erreur: {e}")

        # ── ÉTAPE 5 : Rapport ────────────────────────────────────────────────
        print("\n📊 ÉTAPE 5/5 — Rapport de mission")
        rapport["success"] = all(
            rapport["etapes"].get(k, {}).get("ok", False)
            for k in ["navigation", "insights"]
        )

        rapport_path = os.path.join(DATA_DIR, f"rapport_da_{datetime.now().strftime('%Y-%m-%d')}.json")
        with open(rapport_path, "w", encoding="utf-8") as f:
            json.dump(rapport, f, indent=2, ensure_ascii=False)

        print(f"\n{'✅' if rapport['success'] else '⚠️ '} Mission DA terminée")
        print(f"   - Score audit: {rapport['etapes'].get('audit', {}).get('score', '?')}/100")
        print(f"   - Insights générés: {rapport['insights_count']}")
        print(f"   - Pages visuellement améliorées: {rapport['pages_ameliorees']}")
        print(f"   - Rapport: {rapport_path}")

        if _HAS_LOGGER:
            _log("Agent DA Site", "success",
                 f"Mission DA terminée ({rapport['pages_ameliorees']} pages améliorées)",
                 rapport)

        return rapport

    def run(self, donnees_veille: dict = None) -> dict:
        """
        Point d'entrée standard (appelé par l'orchestrateur).
        Déclenche la mission DA complète : insights + nav + améliorations visuelles.
        """
        return self.run_mission_da_complete(donnees_veille)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN TESTING
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    agent = AgentDASite()

    # Test data
    test_data = {
        "marches": {
            "indices": {
                "CAC 40": {"valeur": 8125, "variation_24h": 0.45},
                "S&P 500": {"valeur": 5248, "variation_24h": 0.3}
            },
            "cryptos": {
                "Bitcoin": {"prix": 67450, "variation_24h": 2.3},
                "Ethereum": {"prix": 3210, "variation_24h": -1.2}
            }
        },
        "geopolitique": [
            "Tensions géopolitiques Ukraine",
            "Politique monétaire restrictive Fed",
            "Réarmement européen et budgets défense",
            "Craintes inflation monétaire"
        ]
    }

    import sys
    if "--audit" in sys.argv:
        # Mode audit uniquement
        audit = agent.auditer_esthetique_site()
        print(f"\nScore: {audit['score_global']}/100")
        for pb in audit["problemes"]:
            print(f"  ⚠️  {pb}")
    elif "--nav" in sys.argv:
        # Harmonisation nav uniquement
        result = agent.harmoniser_navigation()
        print(f"\nRésultats: {result}")
    else:
        # Mission DA complète
        result = agent.run_mission_da_complete(test_data)
        print("\n✅ Mission DA terminée:")
        print(f"  - Succès: {result['success']}")
        print(f"  - Insights: {result['insights_count']}")
        print(f"  - Pages améliorées: {result['pages_ameliorees']}")
