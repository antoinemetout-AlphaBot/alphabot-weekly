"""
Script de diagnostic Twitter — AlphaBot Weekly
Vérifie le chargement des credentials et tente un tweet de test.
Usage : python test_twitter.py
"""
import os, sys
from pathlib import Path

# Charger le .env
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
    print("✅ .env chargé")
except ImportError:
    print("❌ python-dotenv non installé")
    sys.exit(1)

# Vérifier les 4 clés
keys = {
    "TWITTER_API_KEY":              os.getenv("TWITTER_API_KEY", ""),
    "TWITTER_API_SECRET":           os.getenv("TWITTER_API_SECRET", ""),
    "TWITTER_ACCESS_TOKEN":         os.getenv("TWITTER_ACCESS_TOKEN", ""),
    "TWITTER_ACCESS_TOKEN_SECRET":  os.getenv("TWITTER_ACCESS_TOKEN_SECRET", ""),
}

print("\n🔑 Vérification des clés :")
all_ok = True
for name, val in keys.items():
    if val:
        print(f"  ✅ {name} = {val[:6]}...{val[-4:]} ({len(val)} chars)")
    else:
        print(f"  ❌ {name} = MANQUANT")
        all_ok = False

if not all_ok:
    print("\n❌ Des clés sont manquantes dans le .env — arrêt.")
    sys.exit(1)

# Tester tweepy
try:
    import tweepy
    print(f"\n✅ tweepy version : {tweepy.__version__}")
except ImportError:
    print("\n❌ tweepy non installé — pip install tweepy")
    sys.exit(1)

# Tenter la connexion
print("\n🔌 Connexion à l'API X...")
try:
    client = tweepy.Client(
        consumer_key        = keys["TWITTER_API_KEY"],
        consumer_secret     = keys["TWITTER_API_SECRET"],
        access_token        = keys["TWITTER_ACCESS_TOKEN"],
        access_token_secret = keys["TWITTER_ACCESS_TOKEN_SECRET"],
    )

    # Test : poster un tweet minimal
    print("📤 Tentative de tweet...")
    response = client.create_tweet(text="🤖 AlphaBot Weekly — test de connexion API. #AlphaBotWeekly")
    print(f"\n✅✅✅ SUCCÈS ! Tweet posté — ID : {response.data['id']}")
    print("🎉 Le bot Twitter est 100% opérationnel !")

except tweepy.errors.Unauthorized as e:
    print(f"\n❌ 401 Unauthorized : {e}")
    print("\n💡 Causes possibles :")
    print("  1. API Key ou Secret incorrect (caractère O vs 0 ?)")
    print("  2. Access Token généré avant les permissions Read+Write")
    print("  3. L'app n'a pas les permissions 'Lire et écrire' confirmées")
    print("\n→ Solution : Régénérer la Clé Consommateur sur developer.twitter.com")

except tweepy.errors.Forbidden as e:
    print(f"\n❌ 403 Forbidden : {e}")
    print("→ Les permissions Write ne sont pas activées sur l'app")

except Exception as e:
    print(f"\n❌ Erreur inattendue : {type(e).__name__} — {e}")
