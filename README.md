# ⛽ PompeRadar : CI/CD Azure DevOps sur les prix réels des carburants

![Azure DevOps](https://img.shields.io/badge/Azure%20DevOps-Boards%20%C2%B7%20Repos%20%C2%B7%20Pipelines-0078D4?logo=azuredevops&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/tests-14%20r%C3%A9ussis-2E8B57?logo=pytest&logoColor=white)
![Ruff](https://img.shields.io/badge/lint-ruff-D7FF64?logo=ruff&logoColor=black)
![Coût](https://img.shields.io/badge/co%C3%BBt%20Azure-0%20%E2%82%AC-2E8B57)
![Données](https://img.shields.io/badge/donn%C3%A9es-Licence%20Ouverte%20Etalab-1F4E9A)

![Architecture](docs/images/schemas/architecture.png)

> Un pipeline de données industrialisé de bout en bout avec **Azure DevOps**. Il ingère le flux officiel des prix des carburants de **toutes les stations-service de France** (≈ 9 800, mis à jour toutes les 10 minutes), le transforme, le contrôle par une **porte qualité**, puis le publie en production **après approbation humaine**. Chaque ligne de code est reliée à une User Story, chaque déploiement à une approbation. **Coût Azure : 0 €.**

| 📘 Guide pas à pas | 📄 Version PDF | 🗂️ Dictionnaire des données | ⚙️ Pipeline |
|---|---|---|---|
| [docs/GUIDE.md](docs/GUIDE.md) | [15 pages, 9 schémas](docs/Guide_Public_DevOps_1_PompeRadar.pdf) | [data/README.md](data/README.md) | [azure-pipelines.yml](azure-pipelines.yml) |

---

## 📸 Aperçu

![Aperçu animé](docs/images/apercu.gif)

| Sur `main`, après approbation | Sur une branche de fonctionnalité |
|---|---|
| ![Pipeline complet sur main](docs/images/captures/04_pipeline_complet_main.png) | ![CI seule sur une branche](docs/images/captures/03_ci_sur_branche.png) |
| CI, Données (1 artefact), CD (1 contrôle réussi) | CI verte, Données et CD sautés par condition |

| Pull request prête à fusionner | Historique final |
|---|---|
| ![Pull request](docs/images/captures/02_pull_request_prete.png) | ![Historique Git](docs/images/captures/05_historique_git_final.png) |
| contrôles verts, squash, suppression de branche | un commit par pull request, tag `v1.0.0` |

---

## 📊 Résultats clés

| Indicateur | Valeur |
|---|---|
| Stations ingérées par exécution | **9 820** (flux national complet) |
| Stations publiées avec au moins un prix | **9 264** |
| Lignes station x carburant publiées | **30 995** |
| Lignes en quarantaine | **0** |
| Tests unitaires | **14**, exécutés à chaque pull request |
| Règles de la porte qualité | **5** |
| Stages du pipeline | **3** : CI, Données, CD |
| Pull requests livrées | **7**, un commit squash chacune |
| Stratégies de branche sur `main` | **5** |
| Consommation Azure | **0 €** |

---

## 💼 Impact métier

- **Aucune donnée non contrôlée en production.** La porte qualité bloque tout lot suspect ; les lignes irréparables partent en quarantaine au lieu de faire échouer les milliers de lignes saines.
- **Traçabilité de bout en bout.** Du besoin (User Story) au code (pull request), puis au déploiement (environnement approuvé) : on sait qui a livré quoi, quand, et quels commits sont partis.
- **Livraison sûre.** Rien n'entre dans `main` sans relecture, CI verte, élément de travail lié et commentaires résolus.
- **Données vivantes, coût nul.** Une chaîne CI/CD complète sur un flux public réel, sans aucune ressource Azure facturable.

---

## 🧭 Synthèse

| Brique | Ce qui est mis en place |
|---|---|
| **Azure Boards** | processus Agile : 1 Epic, 1 Feature, 4 User Stories, chacune liée à sa pull request |
| **Azure Repos** | `main` protégée par 5 stratégies, trunk-based, fusion squash, tag de version |
| **Azure Pipelines** | YAML en 3 stages, conditions, artefact, résultats de tests publiés, Build Validation |
| **Agent pools** | agent auto-hébergé Windows dans le pool `PoolLocal` |
| **Environments** | `pompe-radar-prod` avec approbation humaine avant publication |
| **Git** | les 8 situations du quotidien pratiquées sur le vrai dépôt |

### Ce qu'il faut créer dans Azure DevOps

| Objet | Nom | Réglage clé |
|---|---|---|
| Projet | `PompeRadar` | privé, Git, processus **Agile** |
| Work items | Epic, Feature, 4 User Stories | hiérarchie parent-enfant |
| Stratégies de branche | `main` | 1 relecteur, work item lié, commentaires résolus, squash seul, CI obligatoire |
| Pool d'agents | `PoolLocal` | Self-hosted, accès à tous les pipelines |
| Jeton d'accès personnel | `agent-pompe-radar` | portée Agent Pools : Read & manage, 30 jours |
| Environnement | `pompe-radar-prod` | contrôle Approvals |
| Pipeline | `PompeRadar` | fichier existant `/azure-pipelines.yml` |
| Build Validation | `CI obligatoire` | Required, déclenchement automatique |

---

## ⚙️ Pipeline

![Pipeline CI/CD](docs/images/schemas/pipeline.png)

| Stage | Quand | Étapes |
|---|---|---|
| **CI** | chaque pull request et chaque commit sur `main` | venv, dépendances, `ruff`, `pytest` (14 tests), publication des résultats |
| **Données** | `main` uniquement | téléchargement du flux réel, transformation, quarantaine, porte qualité, artefact `donnees-propres` |
| **CD** | après Données, avec approbation | téléchargement de l'artefact, copie en production |

| Élément du YAML | Rôle |
|---|---|
| `trigger` + `paths: exclude` | lance sur `main`, sauf si seuls `README.md` ou le dossier `docs` changent |
| `pool: name: PoolLocal` | exécute les jobs sur l'agent auto-hébergé |
| `condition: … refs/heads/main` | réserve le stage Données à `main` |
| `condition: succeededOrFailed()` | publie le rapport qualité même quand la porte refuse |
| `deployment` + `environment` | soumet le stage CD à l'approbation |

> Avec Azure Repos, le déclenchement sur pull request ne passe pas par le mot-clé YAML `pr:` (réservé à GitHub et Bitbucket) mais par la **Build Validation** des stratégies de branche.

---

## 🔗 Lignage des données

![Porte qualité](docs/images/schemas/donnees.png)

| Étape | Module | Entrée | Sortie |
|---|---|---|---|
| Ingestion | [`src/ingestion.py`](src/ingestion.py) | flux officiel (API d'export JSON) | `data/brut/carburants_AAAAMMJJ_HHMM.json` |
| Transformation | [`src/transformation.py`](src/transformation.py) | une ligne par station | une ligne par station et par carburant, contrat de schéma vérifié |
| Qualité | [`src/qualite.py`](src/qualite.py) | format long | lignes valides, quarantaine, liste d'anomalies |
| Orchestration | [`src/executer.py`](src/executer.py) | tout ce qui précède | `prix_carburants.csv`, `synthese_departements.csv`, `quarantaine.csv`, `rapport_qualite.json` |
| Publication | stage CD | artefact `donnees-propres` | dossier de production |

| Règle de la porte qualité | Seuil |
|---|---|
| Volume | au moins 5 000 stations |
| Complétude | aucune valeur vide dans les clés |
| Unicité | une ligne par station et par carburant |
| Plausibilité | au plus 1 % de lignes rejetées |
| Fraîcheur | mise à jour de moins de 3 jours |

Schéma complet de chaque fichier, format des CSV et réconciliation des volumes : **[data/README.md](data/README.md)**. Exemples de sorties : [`data/exemples/`](data/exemples).

---

## 🏗️ Architecture et méthode de travail

**Le parcours en 6 phases**, chacune visible dans Azure DevOps :

![Parcours](docs/images/schemas/parcours.png)

| Phase | Ce que vous faites | Guide |
|---|---|---|
| 1. Préparer | outils, configuration Git, projet Azure DevOps à 0 € | [Phase 1](docs/GUIDE.md#phase-1-préparer-le-terrain) |
| 2. Planifier | Epic, Feature, 4 User Stories dans Boards | [Phase 2](docs/GUIDE.md#phase-2-planifier-dans-azure-boards) |
| 3. Coder | premier commit, protection de `main`, première pull request | [Phase 3](docs/GUIDE.md#phase-3-coder-comme-une-équipe) |
| 4. Données | flux réel, quarantaine, porte qualité | [Phase 4](docs/GUIDE.md#phase-4-les-données-réelles-et-la-porte-qualité) |
| 5. Industrialiser | agent, environnement, pipeline YAML | [Phase 5](docs/GUIDE.md#phase-5-industrialiser) |
| 6. Git | les 8 situations du quotidien | [Phase 6](docs/GUIDE.md#phase-6-latelier-git--les-8-situations-du-quotidien) |

**Les quatre zones de Git :**

![Zones de Git](docs/images/schemas/zones.png)

**La boucle quotidienne d'une User Story :**

![Boucle quotidienne](docs/images/schemas/boucle.png)

**La stratégie de branches trunk-based**, une branche courte par User Story, fusion squash :

![Branches](docs/images/schemas/branches.png)

**Les 8 situations Git pratiquées sur le dépôt :**

| Situation | Commandes |
|---|---|
| Corriger le dernier message | `git commit --amend` |
| Mettre un travail de côté | `git stash push` puis `git stash pop` |
| Nettoyer des commits « wip » | `git rebase -i HEAD~3` |
| Résoudre un conflit avec `main` | `git fetch`, `git rebase origin/main`, `git push --force-with-lease` |
| Annuler ce qui est sur `main` | bouton **Revert** sur la pull request (`git revert`) |
| Marquer une version | `git tag -a v1.0.0` puis `git push origin v1.0.0` |
| Retrouver un commit perdu | `git reflog` puis `git reset --hard 'HEAD@{1}'` |
| Recopier un seul commit | `git cherry-pick <sha>` |

![Conflit résolu par rebase](docs/images/schemas/conflit.png)

**Organisation du dépôt :**

![Carte du dépôt](docs/images/schemas/depot.png)

---

## 🧰 Stack technique

| Domaine | Outils |
|---|---|
| Plateforme DevOps | Azure DevOps : Boards, Repos, Pipelines, Environments |
| Exécution | agent auto-hébergé Windows, pool `PoolLocal` |
| Langage et données | Python 3.11+, pandas, requests |
| Qualité du code | pytest, ruff, publication JUnit |
| Gestion de version | Git : trunk-based, pull requests, squash, rebase, tags |
| Source | Ministère de l'Économie, « Prix des carburants en France, flux instantané v2 », Licence Ouverte Etalab |

### Lancer en local

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check src tests
.venv\Scripts\python.exe src\executer.py
```

Résultats dans `data\propre\`, statut dans `rapport_qualite.json`.

### Antisèche d'entretien

| Question | Réponse courte |
|---|---|
| fetch ou pull ? | `fetch` rapatrie sans toucher au travail ; `pull` = `fetch` + intégration |
| merge ou rebase ? | merge relie sans réécrire ; rebase linéarise mais réécrit les SHA |
| reset ou revert ? | reset déplace la branche (local) ; revert ajoute un commit inverse (partagé) |
| Microsoft-hosted ou self-hosted ? | simplicité, ou contrôle, coût et accès au réseau interne |
| Un secret dans un pipeline ? | jamais dans le YAML : variable secrète, groupe relié à Key Vault, connexion de service |
| `!47` et `#16` ? | `!` cite une pull request, `#` cite un work item |

---

## ✅ Conclusion

PompeRadar réunit une chaîne DevOps complète sur un vrai flux de données publiques : planification dans Boards, revue de code sous stratégies de branche, intégration continue, contrôle de la qualité des données et déploiement approuvé, sans aucun coût d'infrastructure. Le [guide](docs/GUIDE.md) permet de reproduire chaque étape, avec le résultat attendu à chaque fois, puis de pratiquer les huit situations Git du quotidien.

---

## 💡 Le mot de la fin

> Une donnée n'a de valeur que si l'on peut prouver d'où elle vient, qui l'a validée et quand elle est arrivée en production. Azure DevOps rend cette preuve automatique.

**Abdoul Hamid Diallo** · Data & AI Engineer
Microsoft Certified : DP-600 · DP-700 · PL-300 · AI-102 · DP-100 · AI-900 · DP-900
[LinkedIn](https://www.linkedin.com/in/abdoul-hamid-diallo-fabric-data-engineer/)

Données : Ministère de l'Économie, « Prix des carburants en France, flux instantané v2 », Licence Ouverte Etalab.
