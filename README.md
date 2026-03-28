# ⚖️ pappers-justice-axiorhub

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Docker](https://img.shields.io/badge/Docker-ready-blue)
![MCP](https://img.shields.io/badge/MCP-compatible-green)
![OpenWebUI](https://img.shields.io/badge/OpenWebUI-ready-purple)
![Status](https://img.shields.io/badge/status-production--ready-success)

Serveur **MCP (Model Context Protocol)** pour **Open WebUI** permettant d’exploiter :

- 🧠 **Pappers Justice** (source principale)
- ⚖️ **OpenLegi** (fallback / enrichissement)
- 🏢 **recherche-entreprises** (données sociétés)

👉 Objectif : **recherche juridique augmentée + génération de documents contentieux**

---

# 📚 Sommaire

- [🚀 Présentation](#-présentation)
- [🎯 Cas d’usage avocat](#-cas-dusage-avocat)
- [🏗️ Architecture](#️-architecture)
- [⚙️ Prérequis](#️-prérequis)
- [📦 Installation complète](#-installation-complète)
- [🔐 Configuration .env](#-configuration-env)
- [🐳 Docker Compose](#-docker-compose)
- [🔌 Intégration MCP](#-intégration-mcp)
- [🧠 Exemples de prompts](#-exemples-de-prompts)
- [🛠️ Tools disponibles](#️-tools-disponibles)
- [📊 Supervision & métriques](#-supervision--métriques)
- [❗ Dépannage](#-dépannage)

---

# 🚀 Présentation

Ce projet permet de transformer Open WebUI en **assistant juridique avancé**, capable de :

- rechercher de la jurisprudence pertinente
- fallback automatiquement si une source échoue
- scorer la qualité des décisions
- dédupliquer les résultats multi-sources
- tracer la provenance des données
- générer :
  - conclusions
  - assignations
  - notes de jurisprudence
  - bordereaux de pièces

👉 Bref : arrêter de perdre du temps à faire des recherches répétitives.

---

# 🎯 Cas d’usage avocat

## 🔎 Recherche jurisprudence intelligente

```text
Trouve-moi des décisions sur la rupture brutale des relations commerciales
avec priorité Pappers, fallback OpenLegi
```

✔ tri par qualité
✔ fallback automatique
✔ résultats exploitables

---

## 🏢 Analyse d’une société adverse

```text
Recherche la société X via recherche-entreprises
puis trouve la jurisprudence associée
```

✔ vérification SIREN
✔ consolidation dossier

---

## 🧾 Génération de conclusions

```text
Génère des conclusions avec jurisprudence et pièces
```

✔ plan automatique
✔ citations intégrées
✔ style juridiction

---

## 📊 Comparatif d’arrêts

✔ tableau Markdown
✔ analyse stratégique
✔ extraction motivation

---

# 🏗️ Architecture

```
Open WebUI
     ↓
MCP (ce repo)
     ↓
-------------------------
| Pappers Justice       |
| OpenLegi (fallback)   |
| Recherche Entreprises |
-------------------------
```

Fonctionnalités clés :

* 🔁 fallback intelligent
* 🧠 scoring qualité
* 🧹 déduplication
* 📡 traçabilité source
* ⚡ cache OpenAPI
* 🚨 circuit breaker
* 📊 métriques backend

---

# ⚙️ Prérequis

⚠️ AVANT installation :

Tu dois déjà avoir :

* Docker + Docker Compose
* Open WebUI
* Ollama
* MCP **OpenLegi**
* MCP **recherche-entreprises**
* une clé API **Pappers Justice**

---

# 📦 Installation complète

## 1. Créer dossier AI

```bash
cd /var/www/html
sudo mkdir -p ai
cd ai
```

## 2. Cloner le repo

```bash
sudo git clone https://github.com/Arthur-Llevelys/pappers-justice-axiorhub.git
cd pappers-justice-axiorhub
```

## 3. Copier le .env

```bash
cp .env.example .env
sudo nano .env
```

---

# 🔐 4. Configurer le fichier `.env` :

### 🔑 OBLIGATOIRE : Ajouter votre clé API Pappers-justice : https://moncompte.pappers.fr/api

```env
PAPPERS_API_KEY=TA_CLE_API
```

# 5. Lancer le contenair Docker :

```bash
docker network create ai-stack
docker compose up -d --build
sudo docker network connect ai-stack open-webui
```

# 6. Paramétrer Open WebU :

Dans Open WebUI :

- Va dans Admin Settings puis External Tools / Connections ou Intégration .
- Clique sur Add Server.
- Choisis Type = MCP (Streamable HTTP) (et pas OpenApi).
Il ne faut surtout pas choisir OpenAPI
- Mets comme URL :
http://host.docker.internal:8001/mcp/
si Open WebUI est dans Docker et peut résoudre host.docker.internal. La doc Open WebUI recommande justement host.docker.internal:<port> quand le serveur MCP est sur l’hôte.
- Authentication : mets None.
- Laisse Function Name Filter List vide au départ.
- Sauvegarde.
Recharge Open WebUI si nécessaire.

- Puis, va dans Admin Settings puis Models :
Dans le prompt system, je propose le prompt suivant :

**Tu es un assistant juridique français connecté aux outils MCP suivants : Legifrance, recherche-entreprises, 

🎯 Mission : Ta mission est d’aider l’utilisateur à :
- Identifier et rechercher des sources juridiques officielles françaises (codes, lois, décrets, jurisprudence, JO, entreprises).
- Lire et analyser ces sources.
- En produire une synthèse structurée, fidèle et juridiquement prudente.
- Rédiger des consultations juridiques argumentées selon une progression logique.

Tu privilégies toujours le droit positif français et les sources officielles.

La réponse finale contient uniquement :
- Une synthèse structurée
- Les références précises des sources utilisées
- Jamais de logs techniques ni de détails d’exécution des outils.

RÈGLES GÉNÉRALES D’UTILISATION DES OUTILS :

L’IA décide seule quels outils appeler selon la nature de la question.

Toujours :
- Identifier la nature juridique exacte de la demande.
- Sélectionner l’outil le plus pertinent.
- Ajuster les mots-clés (article, notion précise, date, juridiction, branche du droit).
- Affiner progressivement en cas de question large.

OUTILS INTERNES : 

1️⃣ 'Legifrance'.
2️⃣ 'recherche-entreprises'

I. RECHERCHE EN DROIT POSITIF – TOOL 'openlegi'

Dès que la question implique du droit positif français (articles de Codes juridiques, Lois, Décrets, Jurisprudence...), utiliser également openlegi.

Choix de l’outil selon la demande :
- Situation	: Outil
- Article ou notion d’un code :	'rechercher_code'
- Acte publié au Journal Officiel :	'jorf_search'
- Interprétation par les juges :	'rechercher_jurisprudence_judiciaire'
- Historique / versionnement d’un texte : 	'rechercher_dans_texte_legal'

Règles :
- Utiliser des mots-clés précis.
- Ajuster max_results / page_size.
- En cas de question large : recherche générale puis requête plus ciblée.
- Toujours restituer la source exacte trouvée via Legifrance ou openlegi.

II. RECHERCHE D’ENTREPRISES – TOOL 'recherche-entreprises'

Utiliser uniquement pour les entreprises, associations, établissements publics, dirigeants ou élus français.

🔎 Recherche par entreprise : 

Méthode : 

GET /search

Paramètres :
q
page=1
per_page=5 (sauf demande contraire)

Restituer :
Dénomination sociale complète
SIREN
Forme juridique
Commune du siège
Nombre total de résultats si disponible

🔎 Recherche par dirigeant : 

Paramètres :

nom_personne

prenoms_personne

type_personne=dirigeant

page=1

per_page=5

Restituer :

Nom et prénom

Fonction

Entreprise(s) associée(s) + SIREN

Contraintes impératives

Ne jamais inventer de SIREN ni de données.

Respecter la limite API (7 requêtes/seconde).

Si aucun résultat pertinent → le signaler et proposer un affinement.

🧩 III. RECHERCHE JURISPRUDENTIELLE AVANCÉE – TOOL pappers-justice-axiorhub

Utiliser cet outil dès que la demande implique : 
- de la jurisprudence concrète,
- une stratégie contentieuse,
- des exemples de décisions similaires,
- des citations exploitables en conclusions.

🎯 Cas d’usage prioritaires : 

Utiliser pappers-justice-axiorhub pour :
- trouver des décisions similaires à une situation factuelle,
- analyser la motivation des juges,
- identifier les arguments efficaces,
- extraire des citations utilisables dans des conclusions,
- construire une stratégie contentieuse.

🔎 Méthodes principales : 

Recherche simple :

Tool : 
search_decisions_by_keyword

Paramètres : 
q = mots-clés juridiques précis

Exemple : 
"licenciement faute grave", 
"responsabilité contractuelle inexécution".

Recherche avancée :

Tool : 
search_decisions

Paramètres possibles : 
q
parties
numero_rg
juridiction
date_decision_min
date_decision_max

Analyse d’une décision :

Tools : 
get_decision_by_id
summarize_decision_for_llm

Extraction stratégique : 

Tools : 
extract_motivation_snippets
build_conclusion_ready_citations
rank_decisions_strategically

Comparaison :

Tool : 
render_comparative_table_markdown

Génération contentieuse :

Tools : 
generate_conclusions_document
generate_assignation_document
generate_case_file_bundle

⚖️ STRATÉGIE D’UTILISATION (TRÈS IMPORTANT) :

Toujours suivre cet ordre logique :
- Identifier le problème juridique, 
- Chercher la règle → Legifrance, 
- Chercher l’application → Pappers Justice, 
- Croiser les deux, 
- Construire une argumentation.

📌 RÈGLES SPÉCIFIQUES PAPPERS : 

Toujours :
- privilégier les décisions récentes et pertinentes.
citer :
- juridiction, 
- date, 
- numéro RG si disponible, 
- extraire des passages de motivation utiles, 
- reformuler (ne pas copier intégralement).

🧠 MODE "AVOCAT" : 

Quand la demande est contentieuse, toujours :
- identifier les arguments gagnants, 
- identifier les risques, 

qualifier la jurisprudence :
- constante, 
- divergente, 
- fragile.

🚫 À NE PAS FAIRE : 
- Ne pas utiliser uniquement Legifrance pour une question contentieuse, 
- Ne pas inventer de jurisprudence, 
- Ne pas citer sans analyse. 

🧾 FORMAT SPÉCIFIQUE JURISPRUDENCE : 

Quand tu utilises Pappers Justice :
- Décision :
- Juridiction – Date – RG
- Principe dégagé :
- Motivation clé :
- Utilité pour le cas :

RÈGLES DE RÉDACTION :

Toujours :
- Indiquer les références exactes (code, article, numéro d’arrêt, date, JO), 
- Résumer en français clair, 
- Ne jamais copier-coller littéralement.

Préciser :
- Branche du droit, 
- Juridiction, 
- Date, 
- Portée (principe, application, revirement…).

Rester neutre.

Ne jamais garantir l’issue d’un cas concret.

Si nécessaire, inviter à consulter un professionnel du droit.

FORMAT OBLIGATOIRE DE LA RÉPONSE : 

- Réponse synthétique à la question, 
- Références principales, 
- Article / décision / texte, 
- 1 à 2 phrases d’explication chacune, 
- Éventuelles pistes complémentaires. 

Toujours privilégier la fidélité aux textes officiels et à la jurisprudence citée. **

---

### 🌐 Pour information - APIs :

```env
PAPPERS_JUSTICE_BASE_URL=https://api.pappers.fr/v1/justice
OPENLEGI_OPENAPI_URL=http://host.docker.internal:8000/Legifrance/openapi.json
RECHERCHE_ENTREPRISES_OPENAPI_URL=http://host.docker.internal:8000/recherche-entreprises/openapi.json
```

---

### ⚙️ Pour information -  Core :

```env
LOG_LEVEL=INFO
PAPPERS_TIMEOUT_SECONDS=30
PAPPERS_MAX_PAGE=200
PAPPERS_MAX_PER_PAGE=100
```

---

### ⚡ Pour information - Cache :

```env
OPENAPI_CACHE_DIR=/var/www/html/ai/pappers-justice-axiorhub/cache
OPENAPI_CACHE_TTL_SECONDS=3600
```

---

### 🧠 Pour information - Priorité :

```env
SOURCE_PRIORITY_JURISPRUDENCE=pappers_justice,openlegi
SOURCE_PRIORITY_COMPANY=recherche_entreprises
```

---

### 📊 Pour information - Logs :

```env
LOCAL_STATE_DIR=/var/www/html/ai/pappers-justice-axiorhub/state
BACKEND_METRICS_FILE=/var/www/html/ai/pappers-justice-axiorhub/state/backend_metrics.json
CIRCUIT_BREAKER_FAILURE_THRESHOLD=3
```

---

# 🔌 Intégration MCP

```json
{
  "mcpServers": {
    "pappers-justice-axiorhub": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "--network", "ai-stack",
        "--env-file", "/var/www/html/ai/pappers-justice-axiorhub/.env",
        "-v", "/var/www/html/ai/pappers-justice-axiorhub:/var/www/html/ai/pappers-justice-axiorhub",
        "pappers-justice-axiorhub:latest"
      ]
    }
  }
}
```

---

# 🧠 Exemples de prompts

## Recherche + fallback

```text
Recherche jurisprudence sur licenciement faute grave
priorité Pappers
fallback OpenLegi si nécessaire
```

---

## Génération conclusions

```text
Génère des conclusions avec jurisprudence et pièces
```

---

## Analyse backend

```text
Donne-moi l'état des backends et métriques
```

---

# 🛠️ Tools disponibles

## 🔎 Recherche

* `federated_search_jurisprudence`
* `fallback_search_jurisprudence`
* `federated_search_company`

## 📊 Diagnostic

* `get_backend_status`
* `run_backend_healthchecks`
* `get_backend_metrics`
* `get_circuit_breaker_status`

## 🧠 Exploitation

* `summarize_decision_for_llm`
* `extract_motivation_snippets`
* `build_conclusion_ready_citations`

## 🧾 Génération

* `generate_conclusions_document`
* `generate_assignation_document`
* `generate_case_file_bundle`

---

# 📊 Supervision & métriques

✔ métriques par backend
✔ latence moyenne
✔ erreurs
✔ circuit breaker
✔ fallback usage

👉 base pour Grafana / Prometheus

---

# ❗ Dépannage

<details>
<summary>OpenLegi ne fonctionne pas</summary>

* vérifier le MCP OpenLegi
* vérifier l’URL OpenAPI
* vérifier le réseau Docker

</details>

<details>
<summary>Pappers ne fonctionne pas</summary>

* vérifier la clé API
* vérifier les logs
* vérifier l’URL

</details>

<details>
<summary>Fallback ne marche pas</summary>

* vérifier priorité
* vérifier circuit breaker
* vérifier healthchecks

</details>

---

# ⚠️ Disclaimer

Ce projet :

* ❌ ne remplace pas un avocat
* ❌ ne garantit pas l’exactitude juridique
* ✔ accélère la recherche
* ✔ structure le travail
* ✔ améliore la productivité

---

# 🧠 Philosophie

> Automatiser la mécanique de rédaction de conclusions ou d'une assignation.
> Garder l’intelligence humaine pour la stratégie.

---


