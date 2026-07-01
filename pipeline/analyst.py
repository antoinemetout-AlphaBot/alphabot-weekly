"""Analyse éditoriale — un seul appel Claude structuré pour toute la newsletter.

V1 faisait 5+ appels séparés (coûteux, incohérent, fragile).
V2 : un appel → JSON validé avec toutes les sections. Retry en cas de JSON invalide.
Style éditorial : aktionnaire.com (faits chiffrés, accroches pop culture, zéro blabla).
"""
import json
import re

import anthropic

from . import config

SECTIONS_REQUISES = ["titre_edition", "essentiel", "macro", "bourse", "crypto", "concept"]

SYSTEM = f"""Tu es la rédaction d'{config.NEWSLETTER_NAME}, newsletter financière quotidienne
pour des {config.TARGET_AUDIENCE}. Tu écris EXACTEMENT comme aktionnaire.com.

TON STYLE (non négociable) :
- Chaque section commence par un FAIT concret avec un chiffre précis en **gras**.
  Jamais "le Bitcoin monte" → toujours "le Bitcoin gagne **3,7%** à **87 400$**".
- Accroches percutantes : comparaison pop culture, image forte, fait choc.
  Ex : "Le BTC enchaîne les ATH comme Mbappé les buts en Ligue 1."
- Structure des sections longues avec marqueurs en gras :
  **Dans les faits :** chiffres précis (prix, variations, volumes)
  **Plus encore :** approfondissement avec un chiffre
  **Un peu de recul.** contexte historique ou géopolitique en 2-3 phrases
  **Bref.** conclusion 1-2 phrases, mémorable, parfois drôle
- Jargon toujours expliqué inline : "les whales (=gros détenteurs)"
- Ton : tu expliques à un ami intelligent autour d'un café. Jamais condescendant.
- Paragraphes courts (3-4 lignes max). JAMAIS de phrases creuses
  ("les marchés sont volatils", "il faut rester prudent").
- JAMAIS de conseil d'achat ou de vente. Tu informes, tu ne recommandes pas.

FORMAT DE SORTIE : tu réponds UNIQUEMENT avec un objet JSON valide, sans backticks,
sans texte avant ou après. Les valeurs texte utilisent du markdown simple
(**gras**, listes avec "- "). Pas de titres ## dans les valeurs (les titres
sont des champs séparés)."""

PROMPT = """Données marchés du {date_label} :

{donnees}

{contexte_veille}

Génère le JSON suivant (respecte les longueurs) :

{{
  "titre_edition": "Titre accrocheur de l'édition avec un chiffre (max 80 caractères)",
  "essentiel": ["3 puces : l'essentiel du jour, une phrase chacune, avec chiffres en gras"],
  "macro": {{
    "titre": "Accroche journalistique avec chiffre",
    "texte": "Analyse macro & géopolitique (DXY, or, pétrole, EUR/USD, banques centrales). Structure Dans les faits / Concrètement / Un peu de recul / Bref. 200 mots max."
  }},
  "bourse": {{
    "titre": "Accroche journalistique avec chiffre",
    "texte": "Analyse indices + 2-3 actions notables de la watchlist. Structure Dans les faits / Plus encore / Un peu de recul / Bref. 200 mots max."
  }},
  "crypto": {{
    "titre": "Accroche journalistique avec chiffre",
    "texte": "Analyse Bitcoin + Fear & Greed. Structure Dans les faits / Plus encore / Un peu de recul / Bref. 180 mots max."
  }},
  "concept": {{
    "titre": "Nom du concept du jour (pédagogie investissement, différent chaque jour, lié si possible à l'actualité du jour)",
    "texte": "Explication simple avec un exemple concret chiffré. 120 mots max."
  }},
  "commentaire_portefeuille": "1-2 phrases sur la journée des portefeuilles simulés au vu des marchés. Facultatif si pas pertinent."
}}"""


def _extraire_json(texte: str) -> dict:
    texte = texte.strip()
    texte = re.sub(r"^```(?:json)?\s*|\s*```$", "", texte)
    debut, fin = texte.find("{"), texte.rfind("}")
    if debut == -1 or fin == -1:
        raise ValueError("Pas de JSON dans la réponse")
    return json.loads(texte[debut:fin + 1])


def _formater_donnees(rapport: dict) -> str:
    lignes = []
    btc = rapport["crypto"].get("Bitcoin")
    if btc:
        lignes.append(f"Bitcoin: {btc['prix']:,.0f}$ | 24h: {btc['var_24h']:+.2f}% | 7j: {btc['var_7j']:+.2f}%")
    fg = rapport.get("fear_greed")
    if fg:
        lignes.append(f"Fear & Greed crypto: {fg['valeur']}/100 ({fg['label']})")
    for groupe, label in (("indices", "INDICES"), ("commodities", "MACRO"), ("watchlist", "ACTIONS")):
        if rapport.get(groupe):
            lignes.append(f"\n{label}:")
            for nom, d in rapport[groupe].items():
                lignes.append(f"  {nom}: {d['prix']:,.2f} | 24h: {d['var_24h']:+.2f}% | 7j: {d['var_7j']:+.2f}%")
    return "\n".join(lignes)


def _client():
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY manquante")
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def appel_claude(system: str, user: str, max_tokens: int = 4000) -> str:
    resp = _client().messages.create(
        model=config.CLAUDE_MODEL, max_tokens=max_tokens, temperature=0.7,
        system=system, messages=[{"role": "user", "content": user}])
    return resp.content[0].text


def analyser(rapport: dict, memoire: dict | None = None) -> dict:
    """Rapport marchés → contenu éditorial JSON validé. Retry x1 si invalide."""
    date_label = config.date_fr(config.now_paris())
    contexte = ""
    if memoire and memoire.get("titres_recents"):
        contexte = ("Titres et concepts des éditions récentes (ne te répète pas) :\n- "
                    + "\n- ".join(memoire["titres_recents"][-10:]))

    prompt = PROMPT.format(date_label=date_label,
                           donnees=_formater_donnees(rapport),
                           contexte_veille=contexte)
    derniere_erreur = None
    for _ in range(2):
        try:
            contenu = _extraire_json(appel_claude(SYSTEM, prompt))
            manquantes = [s for s in SECTIONS_REQUISES if not contenu.get(s)]
            if manquantes:
                raise ValueError(f"Sections manquantes: {manquantes}")
            if not isinstance(contenu["essentiel"], list):
                contenu["essentiel"] = [str(contenu["essentiel"])]
            return contenu
        except Exception as e:  # noqa: BLE001
            derniere_erreur = e
    raise RuntimeError(f"Analyse Claude invalide après 2 essais: {derniere_erreur}")


def posts_linkedin(rapport: dict, portfolio_resume: str) -> str:
    """3 posts LinkedIn prêts à copier-coller (lundi). Envoyés par email au CEO."""
    system = ("Tu écris des posts LinkedIn en français pour AlphaBot Weekly, newsletter "
              "financière IA gratuite pour investisseurs débutants. Objectif : attirer des "
              "abonnés. Ton : accessible, chiffré, un peu storytelling 'je construis un média "
              "100% IA en public'. Chaque post finit par un appel à s'abonner avec le lien "
              f"{config.SITE_URL}. Pas de hashtags excessifs (3 max par post).")
    user = (f"Données marchés de la semaine :\n{_formater_donnees(rapport)}\n\n"
            f"Portefeuilles simulés : {portfolio_resume}\n\n"
            "Écris 3 posts LinkedIn différents : 1) chiffre marquant de la semaine + analyse "
            "éclair, 2) coulisses du projet (agents IA autonomes qui rédigent une newsletter), "
            "3) pédagogie (un concept d'investissement expliqué simplement). "
            "Sépare-les par une ligne '---'. 150 mots max chacun.")
    return appel_claude(system, user, max_tokens=2000)
