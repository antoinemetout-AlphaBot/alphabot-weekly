"""
AlphaBot — Agent Growth 📈
Rôle : Gérer la liste d'abonnés et envoyer la newsletter automatiquement par email.

Fonctionnalités :
  - Gestion de la liste abonnés (CSV local)
  - Envoi via Gmail SMTP (ou tout autre fournisseur SMTP)
  - A/B test sur les sujets d'emails
  - Tracking des envois (log CSV)
  - Rapport de performance hebdomadaire
"""

import os, csv, json, random, smtplib, logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NEWSLETTER_NAME, ANTHROPIC_API_KEY, CLAUDE_MODEL, OUTPUT_DIR
from utils.file_lock import file_lock
try:
    from utils.activity_logger import log_event as _log
    _AGENT_G = "Agent Growth"
except Exception:
    def _log(*a, **k): pass
    _AGENT_G = "Agent Growth"

# ─── LOGGING ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [Growth] %(message)s")
log = logging.getLogger("agent_growth")


# ─── HELPER FUNCTION FOR REQUIRED ENV VARS ───────────────────────────────────
def _require_env(key):
    """Charge une variable d'environnement requise. Lève une erreur si elle est manquante."""
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Variable d'environnement requise manquante : {key}")
    return val


# ─── CONFIG EMAIL (à remplir dans config.py ou variables d'environnement) ────
EMAIL_SENDER   = _require_env("ALPHABOT_EMAIL")
EMAIL_PASSWORD = _require_env("ALPHABOT_PASSWORD")
SMTP_HOST      = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", "587"))

# Fichiers de données
DATA_DIR        = "data"
SUBSCRIBERS_CSV = os.path.join(DATA_DIR, "subscribers.csv")
SEND_LOG_CSV    = os.path.join(DATA_DIR, "send_log.csv")


class AgentGrowth:
    """
    Agent Growth : gère la liste d'abonnés et orchestre l'envoi des newsletters.
    """

    def __init__(self):
        Path(DATA_DIR).mkdir(exist_ok=True)
        Path(OUTPUT_DIR).mkdir(exist_ok=True)
        self._init_files()
        log.info("Agent Growth initialisé ✅")

    # ─── INITIALISATION DES FICHIERS ─────────────────────────────────────────

    def _init_files(self):
        """Crée les fichiers CSV s'ils n'existent pas."""
        if not os.path.exists(SUBSCRIBERS_CSV):
            with file_lock(SUBSCRIBERS_CSV):
                with open(SUBSCRIBERS_CSV, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["email", "prenom", "source", "date_inscription", "actif", "opens", "clicks"])
            log.info(f"Fichier abonnés créé : {SUBSCRIBERS_CSV}")

        if not os.path.exists(SEND_LOG_CSV):
            with file_lock(SEND_LOG_CSV):
                with open(SEND_LOG_CSV, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["date", "edition", "nb_envoyes", "nb_erreurs", "sujet", "duree_sec"])
            log.info(f"Fichier log créé : {SEND_LOG_CSV}")

    # ─── GESTION DES ABONNÉS ─────────────────────────────────────────────────

    def ajouter_abonne(self, email: str, prenom: str = "", source: str = "manuel") -> bool:
        """Ajoute un abonné à la liste (vérifie les doublons)."""
        with file_lock(SUBSCRIBERS_CSV):
            abonnes = self.lire_abonnes()
            emails_existants = {a["email"].lower() for a in abonnes}

            if email.lower() in emails_existants:
                log.warning(f"Abonné déjà existant : {email}")
                return False

            with open(SUBSCRIBERS_CSV, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    email, prenom, source,
                    datetime.now().strftime("%Y-%m-%d"),
                    "oui", 0, 0
                ])
        log.info(f"Nouvel abonné ajouté : {email} (source: {source})")
        # Envoi automatique de l'email de bienvenue
        self.envoyer_email_bienvenue(email, prenom)
        return True

    def envoyer_email_bienvenue(self, email: str, prenom: str = "") -> bool:
        """Envoie un email de bienvenue premium personnalisé."""
        prenom_affiche = prenom if prenom else "futur investisseur"
        today = datetime.now().strftime("%Y-%m-%d")
        date_fr = datetime.now().strftime("%d/%m/%Y")
        sujet = f"Bienvenue {prenom_affiche} — Ton briefing financier IA commence maintenant"

        # URLs
        site_url = "https://alphabotweeklynetlifyapp.netlify.app"
        newsletter_url = f"{site_url}/outputs/alphabot_newsletter_{today}.html"
        archive_url = f"{site_url}/newsletters.html"

        # Vérifier si newsletter du jour existe
        newsletter_path = os.path.join(OUTPUT_DIR, f"alphabot_newsletter_{today}.html")
        newsletter_existe = os.path.exists(newsletter_path)

        # CTA principal selon disponibilité newsletter
        if newsletter_existe:
            cta_block = f"""
      <div style="text-align:center;margin:32px 0 8px;">
        <a href="{newsletter_url}" style="background:linear-gradient(135deg,#22d3ee,#3b82f6);color:#04091a;text-decoration:none;padding:18px 48px;border-radius:10px;font-weight:800;font-size:16px;display:inline-block;letter-spacing:0.5px;box-shadow:0 4px 24px rgba(34,211,238,0.3);">
          Lire mon premier briefing
        </a>
      </div>
      <p style="text-align:center;color:#64748b;font-size:12px;margin:8px 0 0;">Edition du {date_fr}</p>"""
        else:
            cta_block = f"""
      <div style="text-align:center;margin:32px 0 8px;">
        <a href="{site_url}" style="background:linear-gradient(135deg,#22d3ee,#3b82f6);color:#04091a;text-decoration:none;padding:18px 48px;border-radius:10px;font-weight:800;font-size:16px;display:inline-block;letter-spacing:0.5px;box-shadow:0 4px 24px rgba(34,211,238,0.3);">
          Decouvrir AlphaBot Weekly
        </a>
      </div>
      <p style="text-align:center;color:#64748b;font-size:12px;margin:8px 0 0;">Ton premier briefing arrive demain matin</p>"""

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bienvenue dans AlphaBot Weekly</title>
</head>
<body style="margin:0;padding:0;background:#04091a;font-family:'Segoe UI',Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;">

  <!-- Preheader invisible -->
  <div style="display:none;max-height:0;overflow:hidden;color:#04091a;">
    {prenom_affiche}, tes marches decryptes par l IA chaque matin. Bienvenue.
  </div>

  <div style="max-width:620px;margin:0 auto;padding:24px 16px;">

    <!-- HEADER -->
    <div style="background:linear-gradient(160deg,#0a1628 0%,#0d2137 40%,#142952 100%);border-radius:16px 16px 0 0;padding:48px 40px 40px;text-align:center;border:1px solid rgba(34,211,238,0.15);border-bottom:none;">
      <div style="width:56px;height:56px;margin:0 auto 16px;background:linear-gradient(135deg,#22d3ee,#3b82f6);border-radius:14px;display:flex;align-items:center;justify-content:center;">
        <img src="{site_url}/favicon.ico" alt="AB" style="width:32px;height:32px;" onerror="this.style.display='none'">
      </div>
      <h1 style="color:white;font-size:24px;margin:0 0 6px;font-weight:800;letter-spacing:1px;">ALPHABOT WEEKLY</h1>
      <div style="width:40px;height:2px;background:linear-gradient(90deg,#22d3ee,#3b82f6);margin:12px auto;border-radius:2px;"></div>
      <p style="color:#94a3b8;font-size:13px;margin:0;letter-spacing:2px;text-transform:uppercase;">Intelligence financiere automatisee</p>
    </div>

    <!-- CORPS PRINCIPAL -->
    <div style="background:linear-gradient(180deg,#0d1b2a,#111d32);padding:40px;border-left:1px solid rgba(34,211,238,0.15);border-right:1px solid rgba(34,211,238,0.15);">

      <!-- Salutation -->
      <h2 style="color:white;font-size:22px;margin:0 0 20px;font-weight:700;">
        Bonjour {prenom_affiche},
      </h2>

      <p style="color:#cbd5e1;font-size:15px;line-height:1.8;margin:0 0 24px;">
        Ton inscription est confirmee. A partir de maintenant, tu recois chaque matin un briefing complet des marches financiers, redige et analyse par nos agents IA.
      </p>

      <!-- Les 3 promesses -->
      <div style="margin:28px 0;padding:0;">

        <!-- Promesse 1 -->
        <div style="display:flex;align-items:flex-start;margin-bottom:20px;">
          <div style="min-width:44px;height:44px;background:rgba(34,211,238,0.1);border-radius:10px;display:flex;align-items:center;justify-content:center;margin-right:16px;border:1px solid rgba(34,211,238,0.15);">
            <span style="font-size:20px;">&#128200;</span>
          </div>
          <div>
            <p style="color:white;font-size:14px;font-weight:700;margin:0 0 4px;">Marches en temps reel</p>
            <p style="color:#94a3b8;font-size:13px;line-height:1.6;margin:0;">Bitcoin, CAC 40, S&amp;P 500, or, petrole, devises — toutes les donnees cles en un coup d'oeil.</p>
          </div>
        </div>

        <!-- Promesse 2 -->
        <div style="display:flex;align-items:flex-start;margin-bottom:20px;">
          <div style="min-width:44px;height:44px;background:rgba(59,130,246,0.1);border-radius:10px;display:flex;align-items:center;justify-content:center;margin-right:16px;border:1px solid rgba(59,130,246,0.15);">
            <span style="font-size:20px;">&#129302;</span>
          </div>
          <div>
            <p style="color:white;font-size:14px;font-weight:700;margin:0 0 4px;">Analyse IA approfondie</p>
            <p style="color:#94a3b8;font-size:13px;line-height:1.6;margin:0;">13 agents specialises decryptent la macro, la geopolitique et les tendances pour toi.</p>
          </div>
        </div>

        <!-- Promesse 3 -->
        <div style="display:flex;align-items:flex-start;margin-bottom:0;">
          <div style="min-width:44px;height:44px;background:rgba(34,197,94,0.1);border-radius:10px;display:flex;align-items:center;justify-content:center;margin-right:16px;border:1px solid rgba(34,197,94,0.15);">
            <span style="font-size:20px;">&#9201;</span>
          </div>
          <div>
            <p style="color:white;font-size:14px;font-weight:700;margin:0 0 4px;">5 minutes, pas plus</p>
            <p style="color:#94a3b8;font-size:13px;line-height:1.6;margin:0;">L'essentiel de la finance condense pour que tu prennes de meilleures decisions, sans y passer la journee.</p>
          </div>
        </div>

      </div>

      <!-- Separateur -->
      <div style="height:1px;background:linear-gradient(90deg,transparent,rgba(34,211,238,0.2),transparent);margin:32px 0;"></div>

      <!-- CTA principal -->
      {cta_block}

    </div>

    <!-- SECTION SECONDAIRE : liens utiles -->
    <div style="background:#0a1628;padding:32px 40px;border-left:1px solid rgba(34,211,238,0.15);border-right:1px solid rgba(34,211,238,0.15);">
      <p style="color:#64748b;font-size:11px;letter-spacing:2px;text-transform:uppercase;margin:0 0 16px;font-weight:700;">Tes raccourcis</p>
      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
            <a href="{site_url}" style="color:#22d3ee;font-size:14px;text-decoration:none;font-weight:600;">&#127758;&nbsp; Site AlphaBot Weekly</a>
          </td>
        </tr>
        <tr>
          <td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
            <a href="{archive_url}" style="color:#22d3ee;font-size:14px;text-decoration:none;font-weight:600;">&#128218;&nbsp; Archives des editions</a>
          </td>
        </tr>
        <tr>
          <td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
            <a href="{site_url}/investissement.html" style="color:#22d3ee;font-size:14px;text-decoration:none;font-weight:600;">&#128176;&nbsp; Portefeuille IA</a>
          </td>
        </tr>
        <tr>
          <td style="padding:10px 0;">
            <a href="{site_url}/dashboard-agents.html" style="color:#22d3ee;font-size:14px;text-decoration:none;font-weight:600;">&#129302;&nbsp; Voir nos agents en action</a>
          </td>
        </tr>
      </table>
    </div>

    <!-- FOOTER -->
    <div style="background:#060d1f;border-radius:0 0 16px 16px;padding:32px 40px;text-align:center;border:1px solid rgba(34,211,238,0.15);border-top:none;">
      <p style="color:#475569;font-size:12px;line-height:1.7;margin:0 0 16px;">
        <strong style="color:#64748b;">AlphaBot Weekly</strong> — Newsletter financiere IA<br>
        Fondee par Antoine Metout
      </p>
      <div style="margin:0 0 16px;">
        <a href="https://twitter.com/AlphaBot_Weekly" style="color:#64748b;text-decoration:none;font-size:12px;margin:0 8px;">Twitter</a>
        <span style="color:#1e293b;">|</span>
        <a href="{site_url}" style="color:#64748b;text-decoration:none;font-size:12px;margin:0 8px;">Site web</a>
      </div>
      <div style="height:1px;background:rgba(255,255,255,0.05);margin:16px 0;"></div>
      <p style="color:#334155;font-size:11px;margin:0;">
        Tu recois cet email car tu t'es inscrit(e) sur alphabotweekly.netlify.app<br>
        <a href="mailto:antoine.metout@gmail.com?subject=Desabonnement%20AlphaBot%20Weekly&body=Je%20souhaite%20me%20desabonner." style="color:#475569;text-decoration:underline;">Se desabonner</a>
      </p>
    </div>

  </div>
</body>
</html>"""

        texte = (
            f"Bonjour {prenom_affiche},\n\n"
            "Ton inscription a AlphaBot Weekly est confirmee !\n\n"
            "Chaque matin, tu recevras un briefing complet des marches financiers "
            "redige par nos 13 agents IA : Bitcoin, indices, matieres premieres, "
            "geopolitique — tout y est, en moins de 5 minutes.\n\n"
            f"Decouvre ton premier briefing : {newsletter_url}\n"
            f"Toutes les editions : {archive_url}\n"
            f"Notre site : {site_url}\n\n"
            "A demain matin pour ton prochain briefing !\n\n"
            "— Antoine Metout, Fondateur AlphaBot Weekly\n\n"
            "---\n"
            "Pour te desabonner, reponds a cet email avec le mot STOP."
        )

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = sujet
            msg["From"]    = f"AlphaBot Weekly <{EMAIL_SENDER}>"
            msg["To"]      = email
            msg['List-Unsubscribe'] = '<mailto:antoine.metout@gmail.com?subject=Desabonnement>'
            msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
            msg.attach(MIMEText(texte, "plain", "utf-8"))
            msg.attach(MIMEText(html,  "html",  "utf-8"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)

            log.info(f"📧 Email de bienvenue envoyé à {email} ✅")
            return True
        except Exception as e:
            log.error(f"❌ Erreur envoi bienvenue à {email} : {e}")
            return False

    def lire_abonnes(self, actifs_seulement: bool = True) -> list:
        """Lit et retourne la liste des abonnés."""
        abonnes = []
        try:
            with file_lock(SUBSCRIBERS_CSV):
                with open(SUBSCRIBERS_CSV, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if actifs_seulement and row.get("actif", "oui") != "oui":
                            continue
                        abonnes.append(row)
        except FileNotFoundError:
            pass
        return abonnes

    def desabonner(self, email: str) -> bool:
        """Désactive un abonné (soft delete, conserve les données)."""
        with file_lock(SUBSCRIBERS_CSV):
            abonnes = self.lire_abonnes(actifs_seulement=False)
            modifie = False
            for a in abonnes:
                if a["email"].lower() == email.lower():
                    a["actif"] = "non"
                    modifie = True

            if modifie:
                self._sauvegarder_abonnes(abonnes)
                log.info(f"Abonné désactivé : {email}")
        return modifie

    def stats_abonnes(self) -> dict:
        """Retourne les statistiques de la liste."""
        tous      = self.lire_abonnes(actifs_seulement=False)
        actifs    = [a for a in tous if a.get("actif") == "oui"]
        inactifs  = [a for a in tous if a.get("actif") != "oui"]

        sources   = {}
        for a in actifs:
            src = a.get("source", "inconnu")
            sources[src] = sources.get(src, 0) + 1

        return {
            "total_actifs":   len(actifs),
            "total_inactifs": len(inactifs),
            "total_liste":    len(tous),
            "sources":        sources,
        }

    def _sauvegarder_abonnes(self, abonnes: list):
        """Réécrit le fichier CSV complet."""
        if not abonnes:
            return
        champs = list(abonnes[0].keys())
        with file_lock(SUBSCRIBERS_CSV):
            with open(SUBSCRIBERS_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=champs)
                writer.writeheader()
                writer.writerows(abonnes)

    # ─── GÉNÉRATION DU SUJET (A/B TEST) ──────────────────────────────────────

    def generer_sujets(self, date: str, mood_val: int = 50) -> list:
        """
        Génère 3 variantes de sujet d'email pour A/B testing.
        Sélectionne automatiquement la meilleure selon les stats passées.
        """
        sentiment = "📈 haussier" if mood_val > 55 else "📉 baissier" if mood_val < 45 else "⚖️ neutre"

        sujets = [
            f"🤖 AlphaBot — {date} : Les marchés {sentiment} cette semaine",
            f"⚡ Votre briefing bourse & crypto du {date} — par l'IA",
            f"📊 {date} | Ce que les marchés ont retenu cette semaine",
        ]

        # Sélection aléatoire pondérée (en production : basé sur les taux d'ouverture)
        return sujets

    # ─── CONSTRUCTION DE L'EMAIL ─────────────────────────────────────────────

    def construire_email(self, newsletter_html: str, sujet: str,
                         destinataire: str, prenom: str = "") -> MIMEMultipart:
        """Construit le message MIME complet."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = sujet
        msg["From"]    = f"{NEWSLETTER_NAME} <{EMAIL_SENDER}>"
        msg["To"]      = destinataire

        # Version texte brut (fallback)
        texte_brut = (
            f"Bonjour{' ' + prenom if prenom else ''},\n\n"
            f"Votre newsletter {NEWSLETTER_NAME} est disponible.\n"
            "Ce message nécessite un client email compatible HTML.\n\n"
            "Pour vous désabonner, répondez à cet email avec 'STOP'.\n"
        )

        # Personnalisation HTML
        if prenom:
            html_perso = newsletter_html.replace(
                "<!-- PRENOM_PLACEHOLDER -->",
                f'<p style="color:#94a3b8;font-size:13px;">Bonjour <strong style="color:white;">{prenom}</strong> 👋</p>'
            )
        else:
            html_perso = newsletter_html

        # Ajouter le footer RGPD avant la fermeture </body>
        unsubscribe_footer = """
<div style="text-align:center; padding:20px 0; margin-top:30px; border-top:1px solid #333; font-size:12px; color:#64748b;">
  <p>Vous recevez cet email car vous êtes abonné(e) à AlphaBot Weekly.</p>
  <p><a href="mailto:antoine.metout@gmail.com?subject=Désabonnement AlphaBot Weekly&body=Je souhaite me désabonner de la newsletter AlphaBot Weekly." style="color:#22d3ee;">Se désabonner</a></p>
</div>
"""
        if "</body>" in html_perso:
            html_perso = html_perso.replace("</body>", unsubscribe_footer + "</body>")
        else:
            html_perso += unsubscribe_footer

        # Ajouter les headers RGPD
        msg['List-Unsubscribe'] = '<mailto:antoine.metout@gmail.com?subject=Desabonnement>'
        msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'

        msg.attach(MIMEText(texte_brut, "plain", "utf-8"))
        msg.attach(MIMEText(html_perso, "html",  "utf-8"))
        return msg

    # ─── ENVOI SMTP ──────────────────────────────────────────────────────────

    def envoyer_newsletter(self, newsletter_html_path: str,
                           sujet: str = None, test_email: str = None) -> dict:
        """
        Envoie la newsletter à toute la liste (ou à un email de test).

        Args:
            newsletter_html_path : chemin vers le fichier HTML de la newsletter
            sujet                : sujet de l'email (auto-généré si None)
            test_email           : si défini, envoie uniquement à cette adresse

        Returns:
            dict avec les stats d'envoi
        """
        debut = datetime.now()
        log.info("━━━ AGENT GROWTH : Début de l'envoi ━━━")
        _log(_AGENT_G, "start", f"Envoi newsletter démarré — {sujet or 'sujet auto'}")

        # Lecture du HTML
        try:
            with open(newsletter_html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
        except FileNotFoundError:
            log.error(f"Fichier newsletter introuvable : {newsletter_html_path}")
            return {"success": False, "erreur": "Fichier HTML introuvable"}

        # Choix du sujet
        date_str = datetime.now().strftime("%d/%m/%Y")
        if not sujet:
            sujets  = self.generer_sujets(date_str)
            sujet   = random.choice(sujets)

        # Liste de destinataires
        if test_email:
            destinataires = [{"email": test_email, "prenom": "Test"}]
            log.info(f"Mode TEST — envoi uniquement à : {test_email}")
        else:
            destinataires = self.lire_abonnes()
            log.info(f"Envoi à {len(destinataires)} abonné(s) actif(s)")

        if not destinataires:
            log.warning("Aucun abonné actif trouvé. Ajoutez des abonnés avec ajouter_abonne().")
            return {"success": False, "erreur": "Aucun abonné"}

        nb_ok  = 0
        nb_err = 0
        erreurs = []

        # Connexion SMTP
        try:
            log.info(f"Connexion SMTP : {SMTP_HOST}:{SMTP_PORT}")
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                log.info("Connexion SMTP réussie ✅")

                for dest in destinataires:
                    email  = dest.get("email", "")
                    prenom = dest.get("prenom", "")
                    try:
                        msg = self.construire_email(html_content, sujet, email, prenom)
                        server.send_message(msg)
                        nb_ok += 1
                        if nb_ok % 10 == 0:
                            log.info(f"  Envoyés : {nb_ok}/{len(destinataires)}")
                    except Exception as e:
                        nb_err += 1
                        erreurs.append({"email": email, "erreur": str(e)})
                        log.warning(f"  Échec envoi à {email}: {e}")

        except smtplib.SMTPAuthenticationError:
            log.error("❌ Erreur d'authentification SMTP.")
            log.error("→ Vérifie EMAIL_SENDER et EMAIL_PASSWORD dans les variables d'env.")
            log.error("→ Pour Gmail, active l'accès 2FA et crée un 'App Password'.")
            return {
                "success": False,
                "erreur": "Authentification SMTP échouée",
                "aide": "https://support.google.com/accounts/answer/185833"
            }
        except Exception as e:
            log.error(f"❌ Erreur SMTP : {e}")
            return {"success": False, "erreur": str(e)}

        # Log de l'envoi
        duree = (datetime.now() - debut).seconds
        self._log_envoi(date_str, nb_ok, nb_err, sujet, duree)

        resultat = {
            "success":       True,
            "sujet":         sujet,
            "envoyes":       nb_ok,
            "erreurs":       nb_err,
            "duree_sec":     duree,
            "details_err":   erreurs[:5],  # max 5 pour le log
        }

        log.info(f"\n✅ Envoi terminé : {nb_ok} succès, {nb_err} erreurs en {duree}s")
        log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        _log(_AGENT_G, "success" if nb_err == 0 else "warning",
             f"Newsletter envoyée — {nb_ok} succès, {nb_err} erreurs ({duree}s)",
             {"envoyes": nb_ok, "erreurs": nb_err})
        return resultat

    # ─── NOTIFICATION QUOTIDIENNE ────────────────────────────────────────────

    def envoyer_notification_quotidienne(self, newsletter_html_path: str,
                                          site_url: str = "https://alphabotweeklynetlifyapp.netlify.app") -> dict:
        """
        Envoie une notification courte à tous les abonnés avec les gros titres
        et un lien direct vers la newsletter complète.
        """
        import re as _re
        date_str  = datetime.now().strftime("%d/%m/%Y")
        date_file = datetime.now().strftime("%Y-%m-%d")
        nl_url    = f"{site_url}/outputs/alphabot_newsletter_{date_file}.html"
        site_nl   = f"{site_url}/newsletter"

        # Extraire les titres de la newsletter
        titres = []
        gros_titres = []
        try:
            with open(newsletter_html_path, "r", encoding="utf-8") as f:
                html = f.read()
            titres = [m.strip() for m in _re.findall(r'class="sec-title">([^<]+)<', html)][:6]
            gros_titres = [m.strip() for m in _re.findall(r'class="nl-h2">([^<]+)<', html)][:6]
        except Exception:
            titres = ["Marchés Crypto", "Macro & Géopolitique", "Marchés Boursiers"]

        # HTML sections
        sections_html = ""
        icons = {"Crypto": "₿", "Géo": "🌍", "Macro": "🌍", "Bourse": "📊", "Marché": "📊", "Concept": "💡", "Synthèse": "🧠", "Fear": "🧠", "Insights": "🌍"}
        for t in titres:
            icon = next((v for k, v in icons.items() if k in t), "📰")
            sections_html += f'<tr><td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,.06);"><span style="margin-right:10px;">{icon}</span><span style="color:#e2e8f0;font-size:14px;">{t}</span></td></tr>\n'

        highlights_html = ""
        for h in (gros_titres or titres)[:5]:
            highlights_html += f'<li style="margin-bottom:10px;color:#e2e8f0;font-size:14px;line-height:1.6;"><strong style="color:#22d3ee;">→</strong> {h}</li>\n'

        html_email = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#04091a;font-family:Arial,sans-serif;">
<div style="max-width:600px;margin:0 auto;padding:32px 20px;">
  <div style="text-align:center;padding:32px 24px;background:linear-gradient(135deg,rgba(59,130,246,.15),rgba(34,211,238,.08));border:1px solid rgba(59,130,246,.25);border-radius:16px;margin-bottom:24px;">
    <div style="font-size:32px;margin-bottom:12px;">⚡</div>
    <div style="font-size:24px;font-weight:900;color:white;margin-bottom:6px;">AlphaBot Weekly</div>
    <div style="font-size:13px;color:#64748b;">Édition du {date_str} · 100% Généré par IA</div>
  </div>
  <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:20px 24px;margin-bottom:20px;">
    <div style="font-size:16px;font-weight:700;color:white;margin-bottom:8px;">📬 Ton édition du jour est prête</div>
    <div style="font-size:14px;color:#94a3b8;line-height:1.7;">Nos agents IA ont analysé les marchés, la géopolitique et les cryptos. Voici ce qui t'attend :</div>
  </div>
  <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:20px 24px;margin-bottom:20px;">
    <div style="font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#22d3ee;margin-bottom:16px;">📋 AU PROGRAMME</div>
    <table style="width:100%;border-collapse:collapse;">{sections_html}</table>
  </div>
  <div style="background:rgba(34,211,238,.05);border:1px solid rgba(34,211,238,.2);border-radius:12px;padding:20px 24px;margin-bottom:24px;">
    <div style="font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#22d3ee;margin-bottom:14px;">🔑 POINTS CLÉS</div>
    <ul style="margin:0;padding-left:0;list-style:none;">{highlights_html}</ul>
  </div>
  <div style="text-align:center;margin-bottom:24px;">
    <a href="{nl_url}" style="display:inline-block;background:linear-gradient(135deg,#3b82f6,#22d3ee);color:white;text-decoration:none;padding:16px 40px;border-radius:12px;font-size:16px;font-weight:700;">Lire l'édition complète →</a>
    <div style="margin-top:12px;font-size:12px;color:#475569;">Toutes les éditions : <a href="{site_nl}" style="color:#22d3ee;">espace newsletter</a></div>
  </div>
  <div style="text-align:center;padding-top:20px;border-top:1px solid rgba(255,255,255,.06);">
    <div style="font-size:12px;color:#334155;">AlphaBot Weekly · Newsletter IA<br><a href="#" style="color:#475569;">Se désabonner</a> · <a href="{site_url}" style="color:#475569;">Visiter le site</a></div>
  </div>
  <!-- RGPD Unsubscribe Footer -->
  <div style="text-align:center; padding:20px 0; margin-top:30px; border-top:1px solid #333; font-size:12px; color:#64748b;">
    <p>Vous recevez cet email car vous êtes abonné(e) à AlphaBot Weekly.</p>
    <p><a href="mailto:antoine.metout@gmail.com?subject=Désabonnement AlphaBot Weekly&body=Je souhaite me désabonner de la newsletter AlphaBot Weekly." style="color:#22d3ee;">Se désabonner</a></p>
  </div>
</div></body></html>"""

        sujet = f"⚡ AlphaBot Weekly — Ton édition du {date_str} est prête"
        destinataires = self.lire_abonnes()
        if not destinataires:
            return {"success": False, "erreur": "Aucun abonné"}

        nb_ok = nb_err = 0
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                server.ehlo(); server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                for dest in destinataires:
                    email = dest.get("email", "")
                    prenom = dest.get("prenom", "lecteur")
                    try:
                        msg = MIMEMultipart("alternative")
                        msg["Subject"] = sujet
                        msg["From"]    = f"AlphaBot Weekly <{EMAIL_SENDER}>"
                        msg["To"]      = email
                        msg['List-Unsubscribe'] = '<mailto:antoine.metout@gmail.com?subject=Desabonnement>'
                        msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
                        msg.attach(MIMEText(html_email.replace("Ton édition", f"Bonjour {prenom} ! Ton édition"), "html", "utf-8"))
                        server.send_message(msg)
                        nb_ok += 1
                    except Exception as e:
                        nb_err += 1
                        log.warning(f"Notification échec {email}: {e}")
        except Exception as e:
            return {"success": False, "erreur": str(e)}

        log.info(f"✅ Notifications: {nb_ok} envoyées")
        _log(_AGENT_G, "success", f"Notification quotidienne → {nb_ok} abonnés")
        return {"success": True, "envoyes": nb_ok, "erreurs": nb_err}

    # ─── LOGS & STATS ────────────────────────────────────────────────────────

    def _log_envoi(self, date: str, nb_ok: int, nb_err: int,
                   sujet: str, duree: int):
        """Enregistre les stats d'envoi dans le log CSV."""
        with file_lock(SEND_LOG_CSV):
            with open(SEND_LOG_CSV, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([date, datetime.now().strftime("%Y-W%W"),
                                 nb_ok, nb_err, sujet, duree])

    def rapport_performance(self) -> str:
        """Génère un rapport texte sur les performances d'envoi."""
        stats   = self.stats_abonnes()
        log_data = []
        try:
            with file_lock(SEND_LOG_CSV):
                with open(SEND_LOG_CSV, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    log_data = list(reader)
        except FileNotFoundError:
            pass

        rapport = f"""
╔══════════════════════════════════════════════════╗
║        📈  RAPPORT AGENT GROWTH — AlphaBot        ║
╚══════════════════════════════════════════════════╝

👥 LISTE D'ABONNÉS
   Abonnés actifs   : {stats['total_actifs']}
   Abonnés inactifs : {stats['total_inactifs']}
   Total liste      : {stats['total_liste']}

📥 SOURCES D'ACQUISITION"""
        for src, nb in stats.get("sources", {}).items():
            rapport += f"\n   {src:<20} : {nb} abonnés"

        if log_data:
            recent = log_data[-5:]
            rapport += "\n\n📤 DERNIERS ENVOIS"
            for row in reversed(recent):
                rapport += f"\n   {row['date']} — {row['nb_envoyes']} envoyés, {row['nb_erreurs']} erreurs | {row['sujet'][:50]}..."

        rapport += "\n"
        return rapport

    # ─── IMPORT EN MASSE ─────────────────────────────────────────────────────

    def importer_csv(self, chemin_csv: str, colonne_email: str = "email",
                     colonne_prenom: str = "prenom") -> int:
        """
        Importe une liste d'emails depuis un fichier CSV externe.
        Utile pour migrer depuis Substack, Mailchimp, etc.
        """
        count = 0
        try:
            with file_lock(chemin_csv):
                with open(chemin_csv, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        email  = row.get(colonne_email, "").strip()
                        prenom = row.get(colonne_prenom, "").strip()
                        if email and "@" in email:
                            if self.ajouter_abonne(email, prenom, source="import_csv"):
                                count += 1
        except Exception as e:
            log.error(f"Erreur import CSV : {e}")
        log.info(f"Import terminé : {count} nouveaux abonnés ajoutés")
        return count


# ─── TEST STANDALONE ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    agent = AgentGrowth()

    # Exemple : ajouter des abonnés de test
    agent.ajouter_abonne("alice@example.com", "Alice", source="site_web")
    agent.ajouter_abonne("bob@example.com",   "Bob",   source="linkedin")
    agent.ajouter_abonne("charlie@example.com","Charlie", source="bouche_a_oreille")

    # Rapport
    print(agent.rapport_performance())
    print(json.dumps(agent.stats_abonnes(), indent=2, ensure_ascii=False))
