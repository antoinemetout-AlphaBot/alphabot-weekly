"""
AlphaBot — Agent Analyste 🧠
Rôle : Prendre les données brutes de l'Agent Veille et les transformer
       en insights structurés, accessibles pour des débutants.
Utilise : Claude API (claude-opus-4-6)
"""

import json
import anthropic

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, TARGET_AUDIENCE
from utils.api_retry import retry_api


class AgentAnalyste:
    """
    Agent analyste : interprète les données de marché avec Claude.
    Produit une analyse structurée en 4 sections.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        print("🧠 Agent Analyste initialisé")

    @retry_api(max_retries=3, base_delay=2, retryable_exceptions=(anthropic.APIError,), agent_name="Agent Analyste")
    def _appel_claude(self, system_prompt: str, user_prompt: str) -> str:
        """Appel générique à l'API Claude avec retry automatique."""
        message = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
        )
        return message.content[0].text

    # ─── ANALYSE CRYPTO ──────────────────────────────────────────────────────

    def analyser_crypto(self, crypto_data: dict, mood: dict, mode: str = "quotidien") -> str:
        """Analyse les données crypto et le sentiment de marché."""
        print("  🔬 Analyse du marché crypto...")

        # Formate les données pour Claude
        lignes = []
        for symbol, d in crypto_data.items():
            emoji = "🟢" if d["variation_24h"] > 0 else "🔴"
            lignes.append(
                f"{emoji} {d['nom']} ({symbol}): ${d['prix_usd']:,.0f} | "
                f"24h: {d['variation_24h']:+.1f}% | 7j: {d['variation_7j']:+.1f}% | "
                f"Market cap: ${d['market_cap_mrd']}Mrd"
            )

        mood_str = ""
        if mood:
            mood_str = (
                f"\nFear & Greed Index : {mood['valeur']}/100 — {mood['sentiment']}"
            )
            if mood.get("hier_valeur"):
                diff = mood["valeur"] - mood["hier_valeur"]
                mood_str += f" (hier: {mood['hier_valeur']}, variation: {diff:+d})"

        donnees = "\n".join(lignes) + mood_str

        system = f"""Tu es un analyste financier expert en cryptomonnaies.
Tu t'adresses à des {TARGET_AUDIENCE}.
Ton style est pédagogique, clair et enthousiaste sans être sensationnaliste.
Tu n'utilises JAMAIS de jargon sans l'expliquer immédiatement.
Tu ne donnes JAMAIS de conseil d'investissement direct (pas de "achète" ou "vends").
Tu restes factuel et objectif.

Style éditorial : comme aktionnaire.com ou The Economist en français.
- Chaque section commence par un FAIT concret avec un chiffre
- Les titres ## sont des accroches journalistiques, pas des labels ("Bitcoin cède 3% après les minutes de la Fed" pas "Vue d'ensemble")
- Les chiffres importants sont mis en évidence avec **gras**
- Termine chaque section par une implication pratique pour l'investisseur
- Ton : expert mais accessible, direct, jamais alarmiste
- JAMAIS de phrases génériques comme "les marchés ont été volatiles\""""

        # Mode-aware prompts
        if mode == "quotidien":
            vue_ensemble_text = "Comment se porte le marché crypto ce matin ? (2-3 phrases accessibles, avec les chiffres clés)"
            point_cle_text = "Point clé du jour"
            word_limit = "200 mots max"
        else:
            vue_ensemble_text = "Comment se porte le marché crypto en ce moment ? (2-3 phrases accessibles, avec les chiffres clés)"
            point_cle_text = "Point clé à retenir"
            word_limit = "280 mots max"

        user = f"""Voici les données du marché crypto d'aujourd'hui :

{donnees}

Analyse ces données en utilisant des titres ## Markdown pour chaque section :

## Vue d'ensemble
{vue_ensemble_text}

## Mouvements notables
Quelles cryptos retiennent l'attention et pourquoi ? Chaque crypto importante mérite une phrase.

## Ce que ça signifie
Contexte et interprétation pour un investisseur débutant. Qu'est-ce qui a provoqué ces mouvements ?

## {point_cle_text}
1 insight fort. En gras.

Sois direct, {word_limit}, pédagogique et factuel."""

        analyse = self._appel_claude(system, user)
        print("    ✅ Analyse crypto générée")
        return analyse

    # ─── ANALYSE COMMODITÉS & GÉOPOLITIQUE ───────────────────────────────────

    def analyser_commodities(self, commodities_data: dict, mode: str = "quotidien") -> str:
        """Analyse DXY, pétrole, or, EUR/USD avec angle géopolitique."""
        if not commodities_data:
            return ""
        print("  🔬 Analyse des matières premières & géopolitique...")

        lignes = []
        for nom, d in commodities_data.items():
            emoji = "🟢" if d["variation_24h"] > 0 else "🔴"
            lignes.append(
                f"{emoji} {nom}: {d['valeur']:,.4f} | "
                f"Jour: {d['variation_24h']:+.2f}% | Semaine: {d['variation_7j']:+.2f}%"
            )
        donnees = "\n".join(lignes)

        system = f"""Tu es un analyste macroéconomique et géopolitique expert.
Tu t'adresses à des {TARGET_AUDIENCE}.
Tu relies les mouvements du DXY, du pétrole, de l'or et du forex aux événements géopolitiques mondiaux
(tensions USA/Chine, conflit Ukraine, décisions Fed, OPEP, élections, sanctions...).
Tu expliques pourquoi Bitcoin est sensible à ces facteurs macro.
Style : clair, factuel, pédagogique. Jamais de conseil d'investissement.

Style éditorial : comme aktionnaire.com ou The Economist en français.
- Chaque section commence par un FAIT concret avec un chiffre
- Les titres ## sont des accroches journalistiques ("Le dollar bondit à 105, freinant l'or" pas "Le Dollar & les marchés macro")
- Les chiffres importants sont mis en évidence avec **gras**
- Termine chaque section par une implication pratique pour l'investisseur
- Ton : expert mais accessible, direct, jamais alarmiste
- JAMAIS de phrases génériques comme "les marchés ont été volatiles\""""

        # Mode-aware prompts
        if mode == "quotidien":
            signal_text = "Signal du jour"
            word_limit = "160 mots max"
        else:
            signal_text = "Signal de la semaine"
            word_limit = "220 mots max"

        user = f"""Voici les données des matières premières et devises :

{donnees}

Analyse avec des titres ## Markdown :

## Le Dollar & les marchés macro
Que dit le DXY sur l'état de l'économie mondiale ? Quels événements géopolitiques expliquent ces mouvements ?

## Or & Pétrole — Signaux géopolitiques
Que signalent ces actifs refuges/cycliques ? Y a-t-il des tensions géopolitiques (énergie, conflits, sanctions) visibles ?

## Impact sur Bitcoin
Comment ces facteurs macro influencent-ils Bitcoin ? Pourquoi un investisseur crypto doit surveiller le DXY et l'or ?

## {signal_text}
1 événement géopolitique à surveiller. En gras.

{word_limit}"""

        analyse = self._appel_claude(system, user)
        print("    ✅ Analyse macro/géopolitique générée")
        return analyse

    # ─── ANALYSE BOURSE ──────────────────────────────────────────────────────

    def analyser_bourse(self, bourse_data: dict, mode: str = "quotidien") -> str:
        """Analyse les indices et actions boursières."""
        print("  🔬 Analyse des marchés boursiers...")

        indices = bourse_data.get("indices", {})
        actions = bourse_data.get("actions", {})

        lignes_indices = []
        for nom, d in indices.items():
            emoji = "🟢" if d["variation_24h"] > 0 else "🔴"
            lignes_indices.append(
                f"{emoji} {nom}: {d['valeur']:,.0f} pts | "
                f"Jour: {d['variation_24h']:+.2f}% | Semaine: {d['variation_7j']:+.2f}%"
            )

        lignes_actions = []
        for nom, d in actions.items():
            emoji = "🟢" if d["variation_24h"] > 0 else "🔴"
            lignes_actions.append(
                f"{emoji} {nom} ({d['ticker']}): {d['prix']:.2f} {d['devise']} | "
                f"Jour: {d['variation_24h']:+.2f}%"
            )

        donnees = "INDICES :\n" + "\n".join(lignes_indices)
        if lignes_actions:
            donnees += "\n\nACTIONS :\n" + "\n".join(lignes_actions)

        system = f"""Tu es un analyste boursier expert.
Tu t'adresses à des {TARGET_AUDIENCE}.
Style pédagogique, clair, sans jargon non expliqué.
Jamais de conseil d'investissement direct.

Style éditorial : comme aktionnaire.com ou The Economist en français.
- Chaque section commence par un FAIT concret avec un chiffre
- Les titres ## sont des accroches journalistiques ("Le CAC 40 touche les 8100 points" pas "Vue des marchés cette semaine")
- Les chiffres importants sont mis en évidence avec **gras**
- Termine chaque section par une implication pratique pour l'investisseur
- Ton : expert mais accessible, direct, jamais alarmiste
- JAMAIS de phrases génériques comme "les marchés ont été volatiles\""""

        # Mode-aware prompts
        if mode == "quotidien":
            vue_text = "Les marchés aujourd'hui"
            point_cle_text = "Point clé du jour"
            word_limit = "180 mots max"
        else:
            vue_text = "Vue des marchés cette semaine"
            point_cle_text = "Point clé investisseur"
            word_limit = "250 mots max"

        user = f"""Voici les données des marchés boursiers :

{donnees}

Analyse avec des titres ## Markdown :

## {vue_text}
Comment se comportent les grands indices ? Quels mouvements notables ?

## Actions & secteurs à surveiller
Quels titres individuels méritent l'attention ? Qu'est-ce qui bouge ?

## Lecture géopolitique
Comment les tensions mondiales ou décisions politiques impactent-elles les marchés ?

## {point_cle_text}
1 insight. En gras.

{word_limit}"""

        analyse = self._appel_claude(system, user)
        print("    ✅ Analyse bourse générée")
        return analyse

    # ─── SYNTHÈSE GLOBALE ────────────────────────────────────────────────────

    def synthese_globale(self, analyse_crypto: str, analyse_bourse: str, analyse_macro: str, news: list, mode: str = "quotidien") -> str:
        """Génère la synthèse éditoriale globale de la semaine."""
        print("  🔬 Génération de la synthèse globale...")

        titres_news = "\n".join([f"- {n['titre']} ({n['source']})" for n in news[:5]])

        system = f"""Tu es le rédacteur en chef d'AlphaBot, une newsletter financière pour {TARGET_AUDIENCE}.
Tu analyses les marchés avec un angle géopolitique : tu relies les événements mondiaux
aux mouvements de Bitcoin, du dollar et des matières premières.
Tu écris l'intro de la newsletter : engageante, accessible, motivante, avec un regard stratégique.
Jamais de conseil d'investissement. Toujours pédagogique.

Style éditorial : comme aktionnaire.com ou The Economist en français.
- Chaque section commence par un FAIT concret avec un chiffre
- Les titres ## sont des accroches journalistiques fortes et directes
- Les chiffres importants sont mis en évidence avec **gras**
- Termine chaque section par une implication pratique pour l'investisseur
- Ton : expert mais accessible, direct, jamais alarmiste
- JAMAIS de phrases génériques comme "les marchés ont été volatiles\""""

        macro_section = f"\nANALYSE MACRO/GÉOPOLITIQUE :\n{analyse_macro}\n" if analyse_macro else ""

        # Mode-aware prompts
        if mode == "quotidien":
            essentiel_text = "L'essentiel du jour"
            conviction_text = "Notre conviction du jour"
            word_limit = "220 mots max"
            actualites_label = "ACTUALITÉS DU JOUR"
        else:
            essentiel_text = "L'essentiel de cette semaine"
            conviction_text = "Notre conviction de la semaine"
            word_limit = "300 mots max"
            actualites_label = "ACTUALITÉS DE LA SEMAINE"

        user = f"""Voici le résumé de la semaine financière :

ANALYSE CRYPTO (Bitcoin focus) :
{analyse_crypto}
{macro_section}
ANALYSE BOURSE :
{analyse_bourse}

{actualites_label} :
{titres_news}

Écris une synthèse éditoriale complète avec des titres ## Markdown :

## {essentiel_text}
Résumé factuel des mouvements clés des marchés. Les chiffres qui comptent.

## Géopolitique & marchés : le lien
Comment les événements mondiaux (tensions, décisions politiques, économie) impactent Bitcoin, le dollar et les actions ?

## Ce que ça change pour toi
Qu'est-ce que ça signifie pour un investisseur débutant ? Qu'est-ce qu'il faut retenir ?

## {conviction_text}
1 phrase forte et directe.

{word_limit}"""

        synthese = self._appel_claude(system, user)
        print("    ✅ Synthèse globale générée")
        return synthese

    # ─── CONCEPT PÉDAGOGIQUE ─────────────────────────────────────────────────

    def generer_concept(self, mode: str = "quotidien") -> str:
        """Génère une mini-leçon sur un concept financier pour débutants."""
        print("  🔬 Génération du concept pédagogique...")

        system = f"""Tu es un professeur de finance bienveillant qui s'adresse à des {TARGET_AUDIENCE}.
Tu expliques des concepts complexes de façon simple, avec des analogies du quotidien.

Style éditorial : clair, factuel, direct.
- Explique avec des chiffres ou exemples concrets
- Chaque section apporte une information nouvelle et utile
- Les points importants sont mis en évidence avec **gras**
- Termine par une implication pratique pour l'investisseur
- Jamais de phrases vagues ou génériques"""

        # Mode-aware prompts
        if mode == "quotidien":
            intro_text = "💡 Le concept du jour : **[NOM DU CONCEPT]**"
            word_limit = "150 mots max"
        else:
            intro_text = "💡 Le concept de la semaine : **[NOM DU CONCEPT]**"
            word_limit = "200 mots max"

        user = f"""Choisis un concept financier ou crypto important pour un débutant
(ex: ETF, DCA, halving, diversification, P/E ratio, stablecoin, blockchain, etc.)
et explique-le avec des titres ## :

## C'est quoi ?
Définition simple et directe.

## Pourquoi c'est important ?
Quel est son rôle dans le monde de la finance ou de la crypto ?

## Exemple concret
Une analogie du quotidien pour que ça devienne clair.

## À retenir
1 phrase clé à mémoriser.

{word_limit}

Format : commence par "{intro_text}" """

        concept = self._appel_claude(system, user)
        print("    ✅ Concept pédagogique généré")
        return concept

    # ─── ANECDOTE BOURSE ─────────────────────────────────────────────────────

    def generer_anecdote_bourse(self) -> str:
        """Génère une anecdote ou fait historique surprenant sur la bourse."""
        print("  🔬 Génération de l'anecdote bourse...")

        system = f"""Tu es un passionné d'histoire financière qui s'adresse à des {TARGET_AUDIENCE}.
Tu connais des centaines d'anecdotes fascinantes sur la bourse, Wall Street, les krachs,
les traders légendaires, les entreprises mythiques et les faits méconnus de la finance.

Style : captivant, court, surprenant. Comme une rubrique "Le saviez-vous ?"
- Commence par un fait choc avec un chiffre
- Raconte l'histoire en 3-4 phrases max
- Termine par un lien avec le marché actuel si possible
- Jamais vu, jamais banal"""

        user = """Raconte une anecdote fascinante et méconnue sur la bourse ou la finance.
Ça peut être : un krach historique, un trade légendaire, une entreprise qui est passée de rien à tout
(ou l'inverse), un fait statistique surprenant, ou une coïncidence incroyable des marchés.

Format:
## 📖 L'anecdote du jour
[L'anecdote en 80 mots max]

Choisis quelque chose de VRAIMENT surprenant que peu de gens connaissent."""

        anecdote = self._appel_claude(system, user)
        print("    ✅ Anecdote bourse générée")
        return anecdote

    # ─── ANALYSE PRINCIPALE ──────────────────────────────────────────────────

    def analyser(self, rapport_veille: dict, mode: str = "quotidien") -> dict:
        """
        Lance toutes les analyses sur les données collectées par l'Agent Veille.
        Retourne un dict d'analyses prêt pour l'Agent Rédacteur.
        """
        print("\n━━━ AGENT ANALYSTE : Début de l'analyse ━━━")

        analyse_crypto_txt     = self.analyser_crypto(rapport_veille["crypto"], rapport_veille["mood"], mode=mode)
        analyse_bourse_txt     = self.analyser_bourse(rapport_veille["bourse"], mode=mode)
        analyse_macro_txt      = self.analyser_commodities(rapport_veille.get("commodities", {}), mode=mode)

        analyses = {
            "meta":            rapport_veille["meta"],
            "intro":           self.synthese_globale(
                                   analyse_crypto_txt,
                                   analyse_bourse_txt,
                                   analyse_macro_txt,
                                   rapport_veille["news_crypto"],
                                   mode=mode
                               ),
            "crypto":          analyse_crypto_txt,
            "bourse":          analyse_bourse_txt,
            "macro":           analyse_macro_txt,
            "concept":         self.generer_concept(mode=mode),
            "anecdote":        self.generer_anecdote_bourse(),
            "news_raw":        rapport_veille["news_crypto"],
            "mood":            rapport_veille["mood"],
            "commodities_raw": rapport_veille.get("commodities", {}),
            "donnees_brutes":  rapport_veille,
        }

        print("\n✅ Agent Analyste : Toutes les analyses sont prêtes !")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        return analyses
