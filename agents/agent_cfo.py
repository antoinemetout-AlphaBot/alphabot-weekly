"""
AlphaBot — Agent CFO 💰
Rôle : Suivre les revenus, modéliser les projections financières,
       et conseiller sur la stratégie de monétisation avec Claude.

Fonctionnalités :
  - Tracking des revenus (sponsorings, abonnements premium, affiliation)
  - Projections de croissance sur 12 mois
  - Calcul du break-even et jalons financiers
  - Rapport financier mensuel avec recommandations IA
  - Conseil stratégique sur la monétisation
"""

import os, csv, json
from datetime import datetime, timedelta
from pathlib import Path

import anthropic

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, NEWSLETTER_NAME, OUTPUT_DIR

DATA_DIR     = "data"
REVENUES_CSV = os.path.join(DATA_DIR, "revenues.csv")
COSTS_CSV    = os.path.join(DATA_DIR, "costs.csv")


# ─── GRILLE DE PRIX (modèle de revenus cible) ────────────────────────────────
TARIFS_SPONSORING = {
    "encart_standard":     {"prix": 300,  "desc": "Encart 150 mots dans la newsletter"},
    "sponsor_principal":   {"prix": 800,  "desc": "Sponsor principal + mention intro + bannière"},
    "edition_branded":     {"prix": 1500, "desc": "Édition entière co-brandée"},
    "partenariat_annuel":  {"prix": 8000, "desc": "Sponsor annuel exclusif (12 éditions)"},
}
TARIFS_PREMIUM = {
    "mensuel":   {"prix": 9,   "desc": "Accès analyses approfondies + alertes"},
    "annuel":    {"prix": 79,  "desc": "Abonnement annuel (économie 25%)"},
}
COUTS_FIXES = {
    # Coûts RÉELS constatés (mis à jour le 21/03/2026)
    "claude_abonnement": 92.93,  # €/mois — Plan Max (renouvellement 20 avril)
    "anthropic_api":      5.00,  # €/mois — estimation usage API agents (crédits $10 achetés)
    # À ajouter quand actif :
    # "domaine":          12.00,  # €/an ÷ 12 = 1€/mois
}


class AgentCFO:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        Path(DATA_DIR).mkdir(exist_ok=True)
        Path(OUTPUT_DIR).mkdir(exist_ok=True)
        self._init_fichiers()
        print("💰 Agent CFO initialisé ✅")

    # ─── INIT FICHIERS ────────────────────────────────────────────────────────

    def _init_fichiers(self):
        if not os.path.exists(REVENUES_CSV):
            with open(REVENUES_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["date","type","source","montant","description","statut"])
            print(f"  ✅ Fichier revenus créé : {REVENUES_CSV}")

        if not os.path.exists(COSTS_CSV):
            with open(COSTS_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["date","categorie","montant","description","recurrent"])
            # Insérer les coûts fixes récurrents
            with open(COSTS_CSV, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for nom, montant in COUTS_FIXES.items():
                    writer.writerow([
                        datetime.now().strftime("%Y-%m-%d"),
                        nom, montant, f"Coût récurrent {nom}", "oui"
                    ])
            print(f"  ✅ Fichier coûts créé : {COSTS_CSV}")

    # ─── GESTION DES REVENUS ─────────────────────────────────────────────────

    def enregistrer_revenu(self, type_rev: str, source: str,
                            montant: float, description: str = "",
                            statut: str = "encaisse") -> bool:
        """
        Enregistre un revenu.

        Args:
            type_rev    : "sponsoring" | "premium" | "affiliation" | "autre"
            source      : nom du sponsor ou abonné
            montant     : montant en euros
            description : détails
            statut      : "encaisse" | "facture" | "en_attente"
        """
        with open(REVENUES_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d"),
                type_rev, source, montant, description, statut
            ])
        print(f"  ✅ Revenu enregistré : {montant}€ ({type_rev} — {source})")
        return True

    def enregistrer_cout(self, categorie: str, montant: float,
                          description: str = "", recurrent: bool = False):
        """Enregistre une dépense."""
        with open(COSTS_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d"),
                categorie, montant, description, "oui" if recurrent else "non"
            ])
        print(f"  ✅ Coût enregistré : {montant}€ ({categorie})")

    def _lire_csv(self, path: str) -> list:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        except FileNotFoundError:
            return []

    # ─── CALCULS FINANCIERS ──────────────────────────────────────────────────

    def calculer_financials(self) -> dict:
        """Calcule tous les indicateurs financiers clés."""
        revenus  = self._lire_csv(REVENUES_CSV)
        couts    = self._lire_csv(COSTS_CSV)

        now = datetime.now()

        def jours_depuis(date_str):
            try:
                return (now - datetime.strptime(date_str[:10], "%Y-%m-%d")).days
            except:
                return 9999

        # ── Revenus ──
        rev_total     = sum(float(r["montant"]) for r in revenus)
        rev_30j       = sum(float(r["montant"]) for r in revenus if jours_depuis(r["date"]) <= 30)
        rev_encaisses = sum(float(r["montant"]) for r in revenus if r.get("statut") == "encaisse")

        par_type = {}
        for r in revenus:
            t = r.get("type", "autre")
            par_type[t] = par_type.get(t, 0) + float(r["montant"])

        # ── Coûts ──
        cout_total   = sum(float(c["montant"]) for c in couts)
        cout_30j     = sum(float(c["montant"]) for c in couts if jours_depuis(c["date"]) <= 30)
        cout_recur   = sum(float(c["montant"]) for c in couts if c.get("recurrent") == "oui")

        # ── P&L ──
        marge_brute  = round(rev_total - cout_total, 2)
        marge_30j    = round(rev_30j - cout_30j, 2)

        return {
            "rev_total":        round(rev_total, 2),
            "rev_30j":          round(rev_30j, 2),
            "rev_encaisses":    round(rev_encaisses, 2),
            "par_type":         par_type,
            "cout_total":       round(cout_total, 2),
            "cout_30j":         round(cout_30j, 2),
            "cout_mensuel_rec": round(cout_recur, 2),
            "marge_brute":      marge_brute,
            "marge_30j":        marge_30j,
        }

    # ─── PROJECTIONS ─────────────────────────────────────────────────────────

    def projections_12_mois(self, abonnes_actuels: int = 0,
                             croissance_mensuelle: float = 0.20) -> dict:
        """
        Modélise les projections financières sur 12 mois.

        Args:
            abonnes_actuels     : nombre d'abonnés actifs aujourd'hui
            croissance_mensuelle: taux de croissance mensuel (0.20 = +20%/mois)
        """
        cout_fixe_mensuel = sum(COUTS_FIXES.values())  # ~75€/mois de base
        mois_data = []

        abonnes  = max(abonnes_actuels, 1)
        rev_cumul = 0

        for m in range(1, 13):
            abonnes = round(abonnes * (1 + croissance_mensuelle))

            # Revenus estimés selon les paliers d'abonnés
            if abonnes < 100:
                rev_spon    = 0        # Pas encore vendable
                taux_prem   = 0.00
            elif abonnes < 300:
                rev_spon    = 300      # 1 encart standard
                taux_prem   = 0.01
            elif abonnes < 500:
                rev_spon    = 800      # Sponsor principal
                taux_prem   = 0.02
            elif abonnes < 1000:
                rev_spon    = 1600     # 2 sponsors
                taux_prem   = 0.03
            elif abonnes < 3000:
                rev_spon    = 3200     # Sponsor principal + standard
                taux_prem   = 0.04
            else:
                rev_spon    = 5000     # Multiple sponsors
                taux_prem   = 0.05

            rev_premium  = round(abonnes * taux_prem * TARIFS_PREMIUM["mensuel"]["prix"])
            rev_affil    = round(abonnes * 0.001 * 40)  # 0.1% clique, 40€ commission
            rev_mensuel  = rev_spon + rev_premium + rev_affil
            rev_cumul   += rev_mensuel
            profit       = rev_mensuel - cout_fixe_mensuel

            mois_data.append({
                "mois":          m,
                "label":         (datetime.now() + timedelta(days=30*m)).strftime("%b %Y"),
                "abonnes":       abonnes,
                "rev_sponsoring": rev_spon,
                "rev_premium":   rev_premium,
                "rev_affil":     rev_affil,
                "rev_mensuel":   rev_mensuel,
                "cout_mensuel":  cout_fixe_mensuel,
                "profit":        profit,
                "rev_cumul":     rev_cumul,
                "break_even":    profit >= 0,
            })

        break_even_mois = next(
            (m["mois"] for m in mois_data if m["break_even"]), None
        )

        return {
            "mois_data":       mois_data,
            "break_even_mois": break_even_mois,
            "rev_annuel":      mois_data[-1]["rev_cumul"],
            "abonnes_fin_an":  mois_data[-1]["abonnes"],
            "profit_m12":      mois_data[-1]["profit"],
        }

    # ─── CONSEIL IA ──────────────────────────────────────────────────────────

    def conseil_monetisation(self, financials: dict, projections: dict,
                              nb_abonnes: int) -> str:
        """
        Claude analyse la situation financière et donne des recommandations
        concrètes pour accélérer la monétisation.
        """
        print("  🧠 Génération des conseils de monétisation par Claude...")

        context = f"""
Situation actuelle de la newsletter {NEWSLETTER_NAME} :
- Abonnés actifs : {nb_abonnes}
- Revenus ce mois : {financials['rev_30j']}€
- Revenus totaux : {financials['rev_total']}€
- Coûts mensuels fixes : ~{financials['cout_mensuel_rec']}€
- Marge brute (30j) : {financials['marge_30j']}€
- Break-even estimé : mois {projections.get('break_even_mois','?')} ({projections.get('break_even_mois','?') or '?'} mois)

Revenus par type : {json.dumps(financials['par_type'], ensure_ascii=False)}

Tarifs disponibles :
- Encart standard : {TARIFS_SPONSORING['encart_standard']['prix']}€/édition
- Sponsor principal : {TARIFS_SPONSORING['sponsor_principal']['prix']}€/édition
- Premium mensuel : {TARIFS_PREMIUM['mensuel']['prix']}€/mois
        """

        system = """Tu es le CFO d'une startup newsletter IA fintech.
Tu donnes des conseils financiers directs, pragmatiques et actionnables.
Tu priorises les actions à fort impact immédiat.
Pas de théorie, que des actions concrètes avec des chiffres précis.
Réponds en français, max 250 mots, format : 3-4 recommandations numérotées."""

        user = f"""{context}

Analyse cette situation et donne-moi 3-4 recommandations prioritaires pour :
1. Atteindre la rentabilité le plus vite possible
2. Maximiser les revenus avec le niveau d'abonnés actuel
3. Identifier le levier de croissance le plus efficace ce mois

Sois très concret (ex: "Contacter [type d'entreprise] avec un tarif de [X€]")."""

        response = self.client.messages.create(
            model=CLAUDE_MODEL, max_tokens=500,
            messages=[{"role": "user", "content": user}],
            system=system,
        )
        return response.content[0].text

    # ─── RAPPORT CFO ─────────────────────────────────────────────────────────

    def rapport_mensuel(self, nb_abonnes: int = 0) -> str:
        """Génère le rapport CFO mensuel complet."""
        print("\n━━━ AGENT CFO : Rapport mensuel ━━━")

        financials  = self.calculer_financials()
        projections = self.projections_12_mois(abonnes_actuels=nb_abonnes)

        cout_mensuel_reel = sum(COUTS_FIXES.values())
        rapport = f"""
╔══════════════════════════════════════════════════╗
║       💰  RAPPORT CFO — {datetime.now().strftime("%B %Y"):<24}║
╚══════════════════════════════════════════════════╝

💸 CHARGES RÉELLES (mises à jour 21/03/2026)
   Claude Max (abonnement)  :  92,93 €/mois
   Anthropic API (agents)   :   ~5,00 €/mois
   ─────────────────────────────────────
   TOTAL CHARGES FIXES      :  ~{cout_mensuel_reel:.2f} €/mois
   Investissement cumulé    :  {financials['cout_total']:.2f} €
   (Pro mars: 21,60€ + Max: 92,93€ + API: 10€)

💵 P&L (Profits & Pertes)
   Revenus ce mois     : {financials['rev_30j']:>10.2f} €
   Coûts ce mois       : {financials['cout_30j']:>10.2f} €
   Marge brute (30j)   : {financials['marge_30j']:>10.2f} €
   ─────────────────────────────────────
   Revenus totaux      : {financials['rev_total']:>10.2f} €
   Investissement total : {financials['cout_total']:>10.2f} €
   P&L total           : {financials['marge_brute']:>10.2f} €

🎯 SEUIL DE RENTABILITÉ
   Besoin mensuel      :  {cout_mensuel_reel:.0f} € de revenus pour couvrir les charges
   Équivalent sponsors :  1 encart standard (300€) + 1 offre affiliation suffit à ~mi-chemin
   Objectif réaliste   :  Premier sponsor dès 200 abonnés humains engagés

📊 REVENUS PAR SOURCE"""

        for t, m in financials["par_type"].items():
            rapport += f"\n   {t:<20} : {m:.2f} €"

        if not financials["par_type"]:
            rapport += "\n   (Aucun revenu enregistré — utilisez enregistrer_revenu())"

        rapport += f"""

🔮 PROJECTIONS 12 MOIS (taux croissance +20%/mois)
   Break-even         : mois {projections['break_even_mois'] or '?'}
   Abonnés dans 1 an  : {projections['abonnes_fin_an']:,}
   Revenus mois 12    : {projections['mois_data'][-1]['rev_mensuel']:,} €
   Revenus cumulés    : {projections['rev_annuel']:,} €
   Profit mois 12     : {projections['profit_m12']:,} €

📈 PROJECTIONS DÉTAILLÉES (6 prochains mois)
   {'Mois':<12} {'Abonnés':>8} {'Rev.Mois':>10} {'Profit':>8} {'Cumul':>10}
   {'─'*50}"""

        for m in projections["mois_data"][:6]:
            be = " ✅" if m["break_even"] else ""
            rapport += f"\n   {m['label']:<12} {m['abonnes']:>8,} {m['rev_mensuel']:>10,}€ {m['profit']:>+8,}€ {m['rev_cumul']:>9,}€{be}"

        rapport += f"""

💡 TARIFS RECOMMANDÉS
   Encart standard     : {TARIFS_SPONSORING['encart_standard']['prix']}€
   Sponsor principal   : {TARIFS_SPONSORING['sponsor_principal']['prix']}€
   Édition brandée     : {TARIFS_SPONSORING['edition_branded']['prix']}€
   Partenariat annuel  : {TARIFS_SPONSORING['partenariat_annuel']['prix']}€
   Premium mensuel     : {TARIFS_PREMIUM['mensuel']['prix']}€/mois
   Premium annuel      : {TARIFS_PREMIUM['annuel']['prix']}€/an
"""
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        return rapport

    def rapport_avec_conseils(self, nb_abonnes: int = 0) -> str:
        """Rapport CFO complet + recommandations Claude."""
        rapport     = self.rapport_mensuel(nb_abonnes)
        financials  = self.calculer_financials()
        projections = self.projections_12_mois(nb_abonnes)

        try:
            conseils = self.conseil_monetisation(financials, projections, nb_abonnes)
            rapport += f"\n🤖 RECOMMANDATIONS IA (Claude)\n{'─'*50}\n{conseils}\n"
        except Exception as e:
            rapport += f"\n⚠️ Conseil IA non disponible : {e}\n"

        return rapport


if __name__ == "__main__":
    cfo = AgentCFO()

    # Simulation de quelques revenus pour demo
    cfo.enregistrer_revenu("sponsoring", "Trade Republic", 300,
                            "Encart standard édition #1", "encaisse")

    print(cfo.rapport_mensuel(nb_abonnes=150))

    print("\n💡 Pour générer les projections avec conseils IA :")
    print("   cfo.rapport_avec_conseils(nb_abonnes=150)")
