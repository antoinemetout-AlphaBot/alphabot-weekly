# 🤖 AlphaBot Weekly V2 — Brief pour Claude

> Contexte de travail pour toute session Claude sur ce projet.
> La V2 a été reconstruite de zéro le 1er juillet 2026. Ce document est la référence.

## Le projet

Newsletter financière quotidienne 100% générée par IA pour investisseurs débutants
francophones (25-45 ans). Bourse, crypto, macro/géopolitique + portefeuilles simulés.
Style éditorial : aktionnaire.com — faits chiffrés, accroches pop culture, zéro blabla.

- **Site** : https://antoinemetout-alphabot.github.io/alphabot-weekly
- **Repo** : `antoinemetout-AlphaBot/alphabot-weekly` (public)
- **CEO** : Antoine Metout (antoine.metout@gmail.com) — non-développeur, directives en
  français, veut du concret. Si Antoine dit « fais-le » → le faire.

## Architecture V2 (vs V1)

**Tout tourne sur GitHub Actions** — plus aucune dépendance au PC d'Antoine (défaut n°1
de la V1, morte silencieusement en avril 2026 quand le PC a cessé de lancer l'orchestrateur).

| Workflow | Quand | Rôle |
|---|---|---|
| `daily.yml` | 5h30 UTC tous les jours | Pipeline complet : collecte → analyse Claude → portefeuilles → newsletter → site → emails |
| `prices.yml` | Toutes les 30 min, heures de marché | MAJ prix live + rebuild site |
| `static.yml` | Push manuel sur main | Déploiement Pages |

**Un seul package Python** `pipeline/` (6 modules) remplace les 15 agents V1 :
`market` (collecte + retries + validation), `analyst` (UN appel Claude structuré JSON pour
toute l'édition, au lieu de 5+ appels V1), `portfolio` (simulation : l'IA propose, le code
valide — univers fermé, plafonds), `render` (Jinja2 + markdown sûr échappé — fini le bug
CSS/backticks V1), `site` (build statique, base template unique — fini la duplication
nav/CSS), `mailer` (SMTP Gmail + alertes échec au CEO), `run` (entrypoint + log + alerting).

**Supervision** : toute exception → email d'alerte à Antoine + run rouge dans Actions.
Le journal public est sur /coulisses.html (data/pipeline_log.json).

## Secrets GitHub Actions (Settings → Secrets → Actions)

| Secret | Contenu |
|---|---|
| `ANTHROPIC_API_KEY` | Clé API Anthropic |
| `ALPHABOT_EMAIL` | antoine.metout@gmail.com |
| `ALPHABOT_PASSWORD` | App password Gmail |
| `SUBSCRIBERS_CSV` | Liste abonnés, une ligne par abonné : `email,prenom` |

⚠️ **RGPD : les emails d'abonnés ne vont JAMAIS dans le repo (public).** La V1 les avait
committés — corrigé et purgé de l'historique. Nouvel abonné (via Formspree → email à
Antoine) = ajouter une ligne au secret `SUBSCRIBERS_CSV`.

## Décisions V2 vs V1 (résumé)

1. **Hébergement GitHub Actions** au lieu du PC (résilience).
2. **6 modules au lieu de 15 agents / ~60 tâches par jour** — même valeur produite,
   surface de panne divisée par 10.
3. **1 appel Claude structuré** par édition au lieu de 5+ (cohérence, coût, fiabilité).
4. **Markdown échappé + validation avant publication** (pages refusées si backticks/HTML
   tronqué) — le site ne peut plus devenir blanc.
5. **Templates Jinja2 + CSS unique** (`static/site.css`) — fini la duplication par page.
   Toggle dark/light ajouté.
6. **Portefeuilles Saison 2** relancés au 01/07/2026 (10 000 € virtuels × 3 profils) —
   pas de fausse continuité après 3 mois d'arrêt. L'IA propose les trades le lundi,
   le code valide (univers fermé `config.UNIVERSE`, plafonds 20-35%/position, cash).
   Robot trader intraday V1 supprimé (complexité sans valeur, risque réglementaire).
7. **Transparence renforcée** : disclaimers « simulation pédagogique » partout,
   page /mentions.html, désinscription dans chaque email.
8. **Anciennes URLs V1 redirigées** (arena, dashboard-agents, communaute, landing_page).
   Pages privées CEO supprimées (un dashboard « privé » sur un repo public n'était pas privé).
9. **Twitter/growth-booster/commercial/CFO non reconstruits.** LinkedIn conservé en
   semi-auto : 3 posts générés chaque lundi, envoyés par email à Antoine (copier-coller).
10. **Croissance** : à >20 abonnés, migrer l'envoi vers un vrai ESP (Brevo/Buttondown) —
    deliverabilité, désinscription 1-clic, stats d'ouverture.

## Commandes

```bash
pip install -r requirements.txt
python -m pipeline.run daily    # pipeline complet (nécessite les secrets en env)
python -m pipeline.run prices   # MAJ prix + rebuild site
python -m pipeline.run build    # rebuild site seul (aucun secret requis)
```

Déclencher un run manuel : GitHub → Actions → « 📰 Pipeline quotidien » → Run workflow.

## Règles pour Claude

- Ne jamais committer d'email d'abonné, de clé ou de mot de passe.
- Toute modification de template → `python -m pipeline.run build` + vérifier le HTML avant push.
- Le style éditorial aktionnaire.com est non négociable (prompt dans `pipeline/analyst.py`).
- Jamais de conseil d'investissement ; les disclaimers simulation restent visibles.
- Préférer l'action à l'explication. Expliquer en français simple, résultats concrets.
