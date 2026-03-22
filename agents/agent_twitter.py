"""
AlphaBot — Agent Twitter 🐦
============================
Rôle : Poster automatiquement les tweets générés par l'Agent Growth Booster
       sur le compte @AlphaBot_Weekly, aux bonnes heures, sans intervention humaine.

Fonctionnement :
  1. Lit le plan Twitter du jour depuis data/twitter_plan_YYYY-MM-DD.json
  2. Si aucun plan n'existe, en génère un via AgentGrowthBooster
  3. Poste les tweets dont l'heure est dans la fenêtre ±15 min et non encore postés
  4. Pour les threads, poste chaque tweet en reply du précédent
  5. Garde un log dans data/twitter_log.json pour éviter les doublons

API X (Twitter) utilisée : Free tier (jusqu'à 50 tweets/jour — largement suffisant)
Bibliothèque : tweepy

Prérequis dans .env :
  TWITTER_API_KEY=...
  TWITTER_API_SECRET=...
  TWITTER_ACCESS_TOKEN=...
  TWITTER_ACCESS_TOKEN_SECRET=...
"""

import os, sys, json, time
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY
from utils.activity_logger import log_event as _log

_AGENT = "Agent Twitter"

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

DATA_DIR     = "data"
OUTPUT_DIR   = "outputs"
TWITTER_LOG  = os.path.join(DATA_DIR, "twitter_log.json")
FENETRE_MIN  = 20  # Minutes de fenêtre autour de l'heure prévue


class AgentTwitter:
    """
    Poste automatiquement les tweets planifiés sur @AlphaBot_Weekly.
    """

    def __init__(self):
        Path(DATA_DIR).mkdir(exist_ok=True)

        # Chargement des clés depuis .env (aucune valeur par défaut)
        self.api_key              = os.getenv("TWITTER_API_KEY")
        self.api_secret           = os.getenv("TWITTER_API_SECRET")
        self.access_token         = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret  = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.bearer_token         = os.getenv("TWITTER_BEARER_TOKEN")

        self.client = None
        self.ready  = False

        # Vérification au démarrage que les 5 variables sont présentes
        required_vars = {
            "TWITTER_API_KEY": self.api_key,
            "TWITTER_API_SECRET": self.api_secret,
            "TWITTER_ACCESS_TOKEN": self.access_token,
            "TWITTER_ACCESS_TOKEN_SECRET": self.access_token_secret,
            "TWITTER_BEARER_TOKEN": self.bearer_token,
        }
        missing_vars = [name for name, value in required_vars.items() if not value]

        if missing_vars:
            error_msg = f"❌ Erreur critique : variables d'environnement manquantes : {', '.join(missing_vars)}\n   Ajouter à .env : {', '.join(missing_vars)}"
            print(error_msg)
            _log(_AGENT, "error", error_msg)
            return

        try:
            if not TWEEPY_AVAILABLE:
                print("⚠️  Agent Twitter : tweepy non installé (pip install tweepy)")
                return

            self.client = tweepy.Client(
                consumer_key        = self.api_key,
                consumer_secret     = self.api_secret,
                access_token        = self.access_token,
                access_token_secret = self.access_token_secret,
                bearer_token        = self.bearer_token,
            )
            # Vérifier l'authentification immédiatement
            self._verify_auth()
            self.ready = True
            print("🐦 Agent Twitter initialisé ✅ — @AlphaBot_Weekly connecté")

        except tweepy.errors.Unauthorized as e:
            error_msg = "⚠️  Erreur Twitter : Tokens expirés. Régénérer sur https://developer.twitter.com et mettre à jour .env"
            print(error_msg)
            _log(_AGENT, "error", error_msg)
        except Exception as e:
            print(f"⚠️  Agent Twitter : erreur connexion X — {e}")
            _log(_AGENT, "error", f"Erreur initialisation : {str(e)[:80]}")

    def _verify_auth(self) -> bool:
        """Vérifie que l'authentification fonctionne. Retourne True si OK."""
        try:
            me = self.client.get_me()
            _log(_AGENT, "info", f"Authentification vérifiée : @{me.data.username}")
            return True
        except tweepy.errors.Unauthorized:
            raise
        except Exception as e:
            _log(_AGENT, "error", f"Erreur vérification auth : {str(e)[:80]}")
            raise

    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API Twitter sans poster.
        Retourne True si l'authentification est OK.
        """
        if not self.client:
            print("❌ Client non initialisé")
            return False
        try:
            me = self.client.get_me()
            print(f"✅ Connexion réussie : @{me.data.username}")
            return True
        except tweepy.errors.Unauthorized:
            print("❌ Erreur : Tokens Twitter expirés. Régénérer sur https://developer.twitter.com et mettre à jour .env")
            return False
        except Exception as e:
            print(f"❌ Erreur connexion : {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # LOG DES TWEETS POSTÉS (anti-doublon)
    # ═══════════════════════════════════════════════════════════════════════════

    def _charger_log(self) -> dict:
        try:
            with open(TWITTER_LOG, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"tweets_postes": []}

    def _sauvegarder_log(self, log: dict):
        with open(TWITTER_LOG, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)

    def _est_deja_poste(self, tweet_id: str) -> bool:
        log = self._charger_log()
        return tweet_id in [t.get("id") for t in log.get("tweets_postes", [])]

    def _marquer_poste(self, tweet_id: str, contenu: str, x_id: str, type_: str = "tweet"):
        log = self._charger_log()
        log.setdefault("tweets_postes", []).append({
            "id":        tweet_id,
            "x_id":      x_id,
            "type":      type_,
            "apercu":    contenu[:80],
            "timestamp": datetime.now().isoformat(),
        })
        # Garder seulement les 500 derniers logs
        log["tweets_postes"] = log["tweets_postes"][-500:]
        self._sauvegarder_log(log)

    # ═══════════════════════════════════════════════════════════════════════════
    # CHARGEMENT DU PLAN DU JOUR
    # ═══════════════════════════════════════════════════════════════════════════

    def _charger_plan_du_jour(self) -> dict:
        """Charge le plan Twitter depuis data/twitter_plan_YYYY-MM-DD.json"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        chemin   = os.path.join(DATA_DIR, f"twitter_plan_{date_str}.json")

        if os.path.exists(chemin):
            try:
                with open(chemin, "r", encoding="utf-8") as f:
                    plan = json.load(f)
                print(f"  📅 Plan chargé : {len(plan.get('tweets_du_jour', []))} tweets prévus")
                return plan
            except Exception as e:
                print(f"  ⚠️ Erreur lecture plan : {e}")

        # Pas de plan pour aujourd'hui → en générer un
        print("  ⚙️  Aucun plan Twitter pour aujourd'hui — génération en cours...")
        try:
            from agents.agent_growth_booster import AgentGrowthBooster
            booster = AgentGrowthBooster()
            plan    = booster.generer_plan_twitter()
            # Sauvegarder en JSON pour usage futur
            with open(chemin, "w", encoding="utf-8") as f:
                json.dump(plan, f, indent=2, ensure_ascii=False)
            print(f"  ✅ Plan généré et sauvegardé : {chemin}")
            return plan
        except Exception as e:
            print(f"  ❌ Impossible de générer le plan : {e}")
            return {}

    # ═══════════════════════════════════════════════════════════════════════════
    # POSTING
    # ═══════════════════════════════════════════════════════════════════════════

    def _is_retryable_error(self, status_code: int) -> bool:
        """Vérifie si une erreur peut être relancée."""
        return status_code in (429, 500, 502, 503, 504)

    def poster_tweet(self, texte: str) -> Optional[str]:
        """Poste un tweet simple. Retourne l'ID X ou None si échec."""
        if not self.ready:
            print("  ⚠️  Impossible de poster — client non initialisé")
            return None

        # Tronquer si dépassement des 280 caractères
        if len(texte) > 280:
            texte = texte[:277] + "..."

        max_retries = 2
        retry_delay = 5

        for attempt in range(max_retries + 1):
            try:
                response = self.client.create_tweet(text=texte)
                x_id = str(response.data["id"])
                print(f"  ✅ Tweet posté — ID: {x_id}")
                return x_id

            except tweepy.errors.Unauthorized as e:
                print(f"  ❌ Erreur authentification : Tokens expirés. Régénérer sur https://developer.twitter.com et mettre à jour .env")
                _log(_AGENT, "error", "Tokens Twitter expirés")
                return None

            except tweepy.errors.TweepyException as e:
                status_code = getattr(e.response, "status_code", None) if hasattr(e, "response") else None

                if status_code and self._is_retryable_error(status_code):
                    if attempt < max_retries:
                        print(f"  ⚠️  Erreur {status_code} (relançable) — Tentative {attempt + 2}/{max_retries + 1} dans {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        print(f"  ❌ Erreur {status_code} après {max_retries + 1} tentatives")
                        _log(_AGENT, "error", f"Erreur {status_code} après retries : {str(e)[:80]}")
                        return None
                else:
                    print(f"  ❌ Erreur Twitter API : {e}")
                    _log(_AGENT, "error", f"Erreur posting : {str(e)[:80]}")
                    return None

            except Exception as e:
                print(f"  ❌ Erreur inattendue : {e}")
                _log(_AGENT, "error", f"Erreur inattendue : {str(e)[:80]}")
                return None

        return None

    def poster_thread(self, tweets: list) -> list:
        """
        Poste une liste de tweets en thread.
        Chaque tweet répond au précédent.
        Retourne la liste des IDs postés.
        """
        if not self.ready or not tweets:
            return []

        ids_postes  = []
        reply_to_id = None
        max_retries = 2
        retry_delay = 5

        for i, texte in enumerate(tweets):
            if len(texte) > 280:
                texte = texte[:277] + "..."

            success = False
            for attempt in range(max_retries + 1):
                try:
                    if reply_to_id:
                        response = self.client.create_tweet(
                            text                = texte,
                            in_reply_to_tweet_id = reply_to_id,
                        )
                    else:
                        response = self.client.create_tweet(text=texte)

                    x_id = str(response.data["id"])
                    ids_postes.append(x_id)
                    reply_to_id = x_id
                    print(f"  ✅ Thread {i+1}/{len(tweets)} posté — ID: {x_id}")
                    success = True
                    break

                except tweepy.errors.Unauthorized as e:
                    print(f"  ❌ Erreur authentification tweet {i+1} : Tokens expirés")
                    _log(_AGENT, "error", f"Tokens expirés au tweet {i+1}")
                    return ids_postes

                except tweepy.errors.TweepyException as e:
                    status_code = getattr(e.response, "status_code", None) if hasattr(e, "response") else None

                    if status_code and self._is_retryable_error(status_code):
                        if attempt < max_retries:
                            print(f"  ⚠️  Erreur {status_code} tweet {i+1} — Tentative {attempt + 2}/{max_retries + 1} dans {retry_delay}s...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            print(f"  ❌ Erreur {status_code} tweet {i+1} après {max_retries + 1} tentatives")
                            _log(_AGENT, "error", f"Erreur {status_code} thread tweet {i+1} : {str(e)[:80]}")
                            return ids_postes
                    else:
                        print(f"  ❌ Erreur thread tweet {i+1} : {e}")
                        _log(_AGENT, "error", f"Erreur thread tweet {i+1} : {str(e)[:80]}")
                        return ids_postes

                except Exception as e:
                    print(f"  ❌ Erreur inattendue tweet {i+1} : {e}")
                    _log(_AGENT, "error", f"Erreur inattendue tweet {i+1} : {str(e)[:80]}")
                    return ids_postes

            if not success:
                break

            # Pause naturelle entre les tweets du thread (paraît humain)
            if i < len(tweets) - 1:
                time.sleep(3)

        return ids_postes

    # ═══════════════════════════════════════════════════════════════════════════
    # VÉRIFICATION ET POSTING SELON L'HEURE
    # ═══════════════════════════════════════════════════════════════════════════

    def verifier_et_poster(self) -> dict:
        """
        Point d'entrée principal.
        Vérifie si un tweet est prévu dans la fenêtre actuelle (±15 min)
        et le poste s'il ne l'a pas encore été.
        """
        print(f"\n  🐦 Vérification des tweets à poster ({datetime.now().strftime('%H:%M')})...")

        if not self.ready:
            msg = "Agent Twitter non prêt (clés manquantes ou tweepy non installé)"
            _log(_AGENT, "warning", msg)
            return {"status": "not_ready", "message": msg}

        plan = self._charger_plan_du_jour()
        if not plan:
            return {"status": "no_plan", "postes": []}

        maintenant = datetime.now()
        date_str   = maintenant.strftime("%Y-%m-%d")
        postes     = []
        ignores    = []

        for tweet in plan.get("tweets_du_jour", []):
            heure_str = tweet.get("heure_publication", "")
            if not heure_str:
                continue

            # Parser l'heure prévue
            try:
                h, m = map(int, heure_str.split(":"))
            except ValueError:
                continue

            heure_prevue = maintenant.replace(hour=h, minute=m, second=0, microsecond=0)
            diff_sec = abs((maintenant - heure_prevue).total_seconds())

            # Fenêtre de ±FENETRE_MIN minutes
            if diff_sec > FENETRE_MIN * 60:
                continue

            # ID unique pour éviter les doublons
            tweet_id = f"{date_str}_{heure_str}"

            if self._est_deja_poste(tweet_id):
                ignores.append(heure_str)
                continue

            # Récupérer le contenu
            contenu    = tweet.get("contenu", "").strip()
            si_thread  = tweet.get("si_thread", [])
            type_tweet = tweet.get("type", "tweet")

            if not contenu:
                continue

            print(f"  📤 Posting tweet {heure_str} (type: {type_tweet})...")
            _log(_AGENT, "progress", f"Posting tweet {heure_str} — {contenu[:60]}...")

            if si_thread:
                # Thread : tweet principal + suite
                all_tweets = [contenu] + si_thread
                ids = self.poster_thread(all_tweets)
                if ids:
                    self._marquer_poste(tweet_id, contenu, ids[0], "thread")
                    postes.append({
                        "heure": heure_str,
                        "type":  "thread",
                        "nb_tweets": len(all_tweets),
                        "id":    ids[0],
                    })
                    _log(_AGENT, "success",
                         f"Thread posté ({len(all_tweets)} tweets) à {heure_str}",
                         {"id": ids[0]})
            else:
                # Tweet simple
                x_id = self.poster_tweet(contenu)
                if x_id:
                    self._marquer_poste(tweet_id, contenu, x_id, type_tweet)
                    postes.append({
                        "heure": heure_str,
                        "type":  type_tweet,
                        "apercu": contenu[:60],
                        "id":    x_id,
                    })
                    _log(_AGENT, "success",
                         f"Tweet posté à {heure_str} : {contenu[:60]}...",
                         {"id": x_id})

        # Résumé
        if postes:
            print(f"\n  🎉 {len(postes)} tweet(s) posté(s) cette session !")
        elif ignores:
            print(f"  ⏭️  {len(ignores)} tweet(s) déjà posté(s) — rien à faire")
        else:
            print(f"  💤 Aucun tweet prévu dans la fenêtre actuelle")

        return {
            "status": "ok",
            "postes":  postes,
            "ignores": ignores,
            "heure":   maintenant.strftime("%H:%M"),
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # RAPPORT
    # ═══════════════════════════════════════════════════════════════════════════

    def rapport(self) -> str:
        log      = self._charger_log()
        postes   = log.get("tweets_postes", [])
        auj_str  = datetime.now().strftime("%Y-%m-%d")
        auj      = [t for t in postes if t.get("timestamp", "").startswith(auj_str)]

        return f"""
╔══════════════════════════════════════════════════╗
║      🐦  RAPPORT AGENT TWITTER                   ║
╚══════════════════════════════════════════════════╝

✅ Tweets postés aujourd'hui : {len(auj)}
📊 Total tweets postés (all time) : {len(postes)}
🔑 Client Twitter : {'✅ Connecté' if self.ready else '❌ Non connecté'}

Derniers tweets :
{"".join(f"  → {t.get('timestamp','')[:16]} | {t.get('type','?'):8} | {t.get('apercu','')[:50]}" + chr(10) for t in postes[-5:])}
"""

    # ═══════════════════════════════════════════════════════════════════════════
    # RUN (point d'entrée orchestrateur)
    # ═══════════════════════════════════════════════════════════════════════════

    def run(self) -> dict:
        """Point d'entrée utilisé par l'orchestrateur."""
        print("\n━━━ AGENT TWITTER : Démarrage ━━━")
        _log(_AGENT, "start", "Vérification des tweets à poster...")
        resultat = self.verifier_et_poster()
        print(self.rapport())
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        return resultat


# ─── POINT D'ENTRÉE STANDALONE ────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Agent Twitter AlphaBot")
    parser.add_argument("--test", action="store_true",
                        help="Tester la connexion sans poster de tweet")
    parser.add_argument("--poster", type=str, default=None,
                        help="Poster un tweet de test (ex: --poster 'Hello from AlphaBot!')")
    args = parser.parse_args()

    agent = AgentTwitter()

    if args.test:
        print("\n🔑 Test de connexion à l'API X...")
        agent.test_connection()

    elif args.poster:
        print(f"\n📤 Posting tweet de test : '{args.poster}'")
        x_id = agent.poster_tweet(args.poster)
        if x_id:
            print(f"✅ Tweet posté ! ID : {x_id}")
        else:
            print("❌ Échec du post.")

    else:
        agent.run()
