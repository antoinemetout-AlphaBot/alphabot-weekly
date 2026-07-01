"""Envoi d'emails — SMTP Gmail (SSL 465).

Abonnés : lus depuis la variable d'environnement SUBSCRIBERS_CSV
(une ligne par abonné : email,prenom). Jamais dans le repo public (RGPD).
Fallback local : data/subscribers.local.csv (gitignoré) pour les tests.
"""
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from . import config


def abonnes() -> list[dict]:
    brut = os.getenv("SUBSCRIBERS_CSV", "")
    if not brut:
        local = config.DATA / "subscribers.local.csv"
        if local.exists():
            brut = local.read_text(encoding="utf-8")
    out = []
    for ligne in brut.strip().splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("email"):
            continue
        parts = [x.strip() for x in ligne.split(",")]
        if "@" in parts[0]:
            out.append({"email": parts[0],
                        "prenom": parts[1] if len(parts) > 1 and parts[1] else "cher lecteur"})
    return out


def _envoyer(destinataire: str, sujet: str, html: str, texte: str = ""):
    if not (config.ALPHABOT_EMAIL and config.ALPHABOT_PASSWORD):
        raise RuntimeError("Credentials email manquants (ALPHABOT_EMAIL / ALPHABOT_PASSWORD)")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = sujet
    msg["From"] = f"{config.NEWSLETTER_NAME} <{config.ALPHABOT_EMAIL}>"
    msg["To"] = destinataire
    msg.attach(MIMEText(texte or "Ouvrez cet email dans un client compatible HTML.", "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
        s.login(config.ALPHABOT_EMAIL, config.ALPHABOT_PASSWORD)
        s.sendmail(config.ALPHABOT_EMAIL, destinataire, msg.as_string())


def envoyer_newsletter(sujet: str, html_email: str) -> int:
    """Envoie la newsletter à tous les abonnés. Retourne le nombre d'envois réussis."""
    envoyes = 0
    for ab in abonnes():
        try:
            perso = html_email.replace("{{PRENOM}}", ab["prenom"])
            _envoyer(ab["email"], sujet, perso)
            envoyes += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️ Échec envoi {ab['email']}: {e}")
    return envoyes


def alerte_ceo(sujet: str, corps: str):
    """Alerte le CEO en cas de problème pipeline. Ne lève jamais d'exception."""
    try:
        html = (f"<div style='font-family:sans-serif'><h2 style='color:#ef4444'>⚠️ {sujet}</h2>"
                f"<pre style='background:#f1f5f9;padding:12px;border-radius:8px;"
                f"white-space:pre-wrap'>{corps}</pre>"
                f"<p>Voir les logs : <a href='https://github.com/antoinemetout-AlphaBot/"
                f"alphabot-weekly/actions'>GitHub Actions</a></p></div>")
        _envoyer(config.ALPHABOT_EMAIL, f"🚨 AlphaBot — {sujet}", html, corps)
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠️ Alerte CEO impossible: {e}")


def email_ceo(sujet: str, html: str):
    _envoyer(config.ALPHABOT_EMAIL, sujet, html)
