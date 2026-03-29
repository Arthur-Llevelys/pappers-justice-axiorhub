# ⚖️ pappers-justice-axiorhub

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Docker](https://img.shields.io/badge/Docker-ready-blue)
![MCP](https://img.shields.io/badge/MCP-compatible-green)
![OpenWebUI](https://img.shields.io/badge/OpenWebUI-ready-purple)
![Status](https://img.shields.io/badge/status-production--ready-success)

Serveur **MCP (Model Context Protocol)** pour **Open WebUI** permettant d’exploiter :

- 🧠 **Pappers Justice** (source principale) : https://justice.pappers.fr/blog/api
- ⚖️ **OpenLegi** (fallback / enrichissement - Legifrance - Droit Français ) : https://www.openlegi.fr/
- 🏢 **recherche-entreprises** (données sociétés -Inpi base de données entreprises en France) : https://www.data.gouv.fr/reuses/mcp-recherche-dentreprises

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

* Un ordinateur sous linux (Ubuntu 24.04), de préférence avec une ou deux cartes graphiques, ou un Mac.
* Docker + Docker Compose :
  * https://www.datacamp.com/fr/tutorial/install-docker-compose
* Open WebUI :
  * https://docs.openwebui.com/getting-started/quick-start/ , ou :
  * https://axiorhub.com/openwebui/#openwebui
* Ollama :
  * https://docs.ollama.com/docker , ou :
  * https://juris-tyr.com/artificial-intelligence-open-source/#ollama
* Un MCP Docker : 
  * https://github.com/masterno12/webui-mcpo ou
  * https://deepwiki.com/open-webui/mcpo/5.1-docker-deployment , ou :
  * https://axiorhub.com/openwebui/#mcp
* MCP **OpenLegi** :
  * https://auth.openlegi.fr/documentation/ 
* MCP **recherche-entreprises** :
  * https://lobehub.com/fr/mcp/yoanbernabeu-mcp-recherche-entreprises 
* une clé API **Pappers Justice** :
  * https://moncompte.pappers.fr/api 

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
Le contenair Docker se connecte sur  le port **8001**. 

# 6. Paramétrer Open WebU :

**Dans Open WebUI :**

- Aller dans **Admin Settings** puis ***External Tools / Connections** ou **Intégration**.
- Cliquer sur **Add Server.**
- Choisir Type = **MCP (Streamable HTTP)** (et pas OpenApi).
Il ne faut surtout pas choisir OpenAPI
- Indiquer comme URL :
**http://host.docker.internal:8001/mcp/**
si Open WebUI est dans Docker et peut résoudre host.docker.internal. La doc Open WebUI recommande justement host.docker.internal:<port> quand le serveur MCP est sur l’hôte.
- **Authentication** : mets **None**.
- Nom : **papper-justice**
- **Sauvegarde**.
Recharge Open WebUI si nécessaire.

- Puis, aller dans **Admin Settings* puis **Models** :
Dans le **prompt system** du modèle LLM, je propose le prompt suivant :

"Tu es un assistant juridique français connecté aux outils MCP suivants : Legifrance, recherche-entreprises, pappers-justice-axiorhub .

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

1 'Legifrance' ou 'openlegi' 
2 'recherche-entreprises' 
3 'pappers-justice-axiorhub' 

I. RECHERCHE EN DROIT POSITIF – TOOL 'Legifrance' ou 'openlegi' 

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
Ce mcp et API est accessible avec l'adresse : http://host.docker.internal:8001/mcp/

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

Quand tu appelles les tools pappers-justice-axiorhub :

- Respecter strictement les valeurs autorisées par le tool
- Ne jamais inventer de paramètres ou d’enums
- Si un champ de tri ou de filtre semble évident mais n’est pas explicitement autorisé, utiliser la valeur la plus proche autorisée

RÈGLES DE PARAMÉTRAGE POUR PAPPERS JUSTICE :

Pour toute recherche de décisions via pappers-justice-axiorhub :

- Le paramètre `tri` ne peut prendre que les valeurs suivantes :
  - `pertinence`
  - `date`
  - `ancien`

Ne jamais utiliser :
- `date_desc`
- `date_asc`
- `relevance`
- `desc`
- `asc`

Interprétation :
- `tri="date"` = décisions les plus récentes d’abord
- `tri="ancien"` = décisions les plus anciennes d’abord
- `tri="pertinence"` = tri par pertinence

Par défaut :
- utiliser `tri="pertinence"`
- utiliser `tri="date"` seulement si l’utilisateur demande les décisions les plus récentes
- utiliser `tri="ancien"` seulement si l’utilisateur demande les décisions les plus anciennes

Comparaison :

Tool : 
render_comparative_table_markdown

Génération contentieuse :

Tools : 
generate_conclusions_document
generate_assignation_document
generate_case_file_bundle

Pour la génération de conclusions, d'assignation  ou de requête :
Respecte la forme usuelle des conclusions d’avocat ou d'une assignation ou requête :
Conclusions devant le /la [juridiction] , ou Assignation devant le /la [juridiction] , ou Requête devant le /la [juridiction] 
Pour : Identité de la ou des parties 
Ayant pour avocat : (avocat de la partie représentée) 
Contre : Identité de la ou des parties adverses 
Ayant pour avocat : (avocat de la partie adverse) 
Plaise à la / au [juridiction] : 
Rappel des faits et de la procédure : 
Discussion : 
Par ces motifs : 
Visa (Vu les articles ... , Vu la Loi ..., vu la jurisprudence citée, vu les pièces") 
Il est demandé à la / au [juridiction]: 
Demandes  : "JUGER que ...", "REJETER ...", "CONDAMNER ...", "DEBOUTER..." 
Bordereau de communication de pièces 
Liste des pièces. 

L'utilisateur doit pouvoir copier coller le texte rédigé directement dans un traitement de texte. 

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

Toujours privilégier la fidélité aux textes officiels et à la jurisprudence citée.""

**Puis dans les reglages du Modèle de LLM cocher la case Pappers-justice pour activer ce mcp et Sauvergarder les réglages.**

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

# 🧠 Exemples de prompts :

## Recherche + fallback :

```text
Recherche jurisprudence sur licenciement faute grave
priorité Pappers
fallback OpenLegi si nécessaire
```

---

## Génération conclusions : 

```text
Génère des conclusions avec jurisprudence et pièces
```

---

## Analyse backend : 

```text
Donne-moi l'état des backends et métriques
```

---

# 🛠️ Tools disponibles :

## 🔎 Recherche : 

* `federated_search_jurisprudence`
* `fallback_search_jurisprudence`
* `federated_search_company`

## 📊 Diagnostic : 

* `get_backend_status`
* `run_backend_healthchecks`
* `get_backend_metrics`
* `get_circuit_breaker_status`

## 🧠 Exploitation :

* `summarize_decision_for_llm`
* `extract_motivation_snippets`
* `build_conclusion_ready_citations`

## 🧾 Génération : 

* `generate_conclusions_document`
* `generate_assignation_document`
* `generate_case_file_bundle`

---

# 📊 Supervision & métriques : 

✔ métriques par backend
✔ latence moyenne
✔ erreurs
✔ circuit breaker
✔ fallback usage

👉 base pour Grafana / Prometheus

---

# ❗ Dépannage : 

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

# ⚠️ Disclaimer :

Ce projet :

* ❌ ne remplace pas un avocat
* ❌ ne garantit pas l’exactitude juridique
* ✔ accélère la recherche 
* ✔ structure le travail
* ✔ améliore la productivité en préparant des projets de conclusions ou d'assignations.

---

# 🧠 Philosophie :

> Automatiser la mécanique de rédaction de conclusions ou d'une assignation.
> Garder l’intelligence humaine pour la stratégie.

---


