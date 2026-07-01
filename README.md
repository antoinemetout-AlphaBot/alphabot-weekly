# ⚡ AlphaBot Weekly

**La bourse et la crypto, décryptées chaque jour par des agents IA — pour les
investisseurs débutants francophones.**

🌐 https://antoinemetout-alphabot.github.io/alphabot-weekly

## Comment ça marche

Chaque matin à 7h30 (Paris), un pipeline autonome hébergé sur GitHub Actions :

1. **Collecte** les prix réels — Bitcoin (CoinGecko), indices mondiaux, or, pétrole,
   devises, actions (Yahoo Finance), indice Fear & Greed.
2. **Analyse** les marchés avec Claude (Anthropic) — macro, géopolitique, bourse, crypto,
   pédagogie — dans un style journalistique chiffré et accessible.
3. **Met à jour** trois portefeuilles simulés (10 000 € virtuels chacun) : l'IA propose
   ses arbitrages chaque lundi, un programme les valide et les exécute.
4. **Publie** la newsletter sur le site et l'envoie par email aux abonnés.

Les prix du site sont rafraîchis toutes les 30 minutes pendant les heures de marché.
Le journal d'activité du pipeline est public : [/coulisses.html](https://antoinemetout-alphabot.github.io/alphabot-weekly/coulisses.html).

## Structure

```
pipeline/     Le cerveau (Python) : collecte, analyse IA, portefeuilles, rendu, envoi
templates/    Templates Jinja2 du site et des newsletters (base unique)
static/       CSS unique du site
data/         État persistant : index des éditions, portefeuilles, journal
newsletters/  Toutes les éditions publiées
.github/      Workflows (pipeline quotidien, prix live, déploiement Pages)
```

## ⚠️ Avertissement

Contenu 100% généré par IA, sans conseil en investissement. Les portefeuilles sont des
**simulations pédagogiques** avec de l'argent virtuel — aucun argent réel n'est investi.
Détails : [mentions & avertissements](https://antoinemetout-alphabot.github.io/alphabot-weekly/mentions.html).

---
Projet créé par [Antoine Metout](mailto:antoine.metout@gmail.com) · V2 reconstruite en juillet 2026
