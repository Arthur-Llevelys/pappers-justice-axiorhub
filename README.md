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

# 🔐 Configuration `.env`

### 🔑 OBLIGATOIRE : Ajouter votre clé API Pappers-justice : https://moncompte.pappers.fr/api

```env
PAPPERS_API_KEY=TA_CLE_API
```

---

### 🌐 APIs

```env
PAPPERS_JUSTICE_BASE_URL=https://api.pappers.fr/v1/justice
OPENLEGI_OPENAPI_URL=http://host.docker.internal:8000/Legifrance/openapi.json
RECHERCHE_ENTREPRISES_OPENAPI_URL=http://host.docker.internal:8000/recherche-entreprises/openapi.json
```

---

### ⚙️ Core

```env
LOG_LEVEL=INFO
PAPPERS_TIMEOUT_SECONDS=30
PAPPERS_MAX_PAGE=200
PAPPERS_MAX_PER_PAGE=100
```

---

### ⚡ Cache

```env
OPENAPI_CACHE_DIR=/var/www/html/ai/pappers-justice-axiorhub/cache
OPENAPI_CACHE_TTL_SECONDS=3600
```

---

### 🧠 Priorité

```env
SOURCE_PRIORITY_JURISPRUDENCE=pappers_justice,openlegi
SOURCE_PRIORITY_COMPANY=recherche_entreprises
```

---

### 📊 Observabilité

```env
LOCAL_STATE_DIR=/var/www/html/ai/pappers-justice-axiorhub/state
BACKEND_METRICS_FILE=/var/www/html/ai/pappers-justice-axiorhub/state/backend_metrics.json
CIRCUIT_BREAKER_FAILURE_THRESHOLD=3
```

---

# 🐳 Docker Compose

```yaml
services:
  pappers-justice-axiorhub:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: pappers-justice-axiorhub
    restart: unless-stopped
    env_file:
      - .env
    environment:
      INSTALL_PATH: /var/www/html/ai/pappers-justice-axiorhub
      EXPORTS_DIR: /var/www/html/ai/pappers-justice-axiorhub/exports
      LOG_LEVEL: INFO
      PAPPERS_TIMEOUT_SECONDS: 30
      PAPPERS_MAX_PAGE: 200
      PAPPERS_MAX_PER_PAGE: 100
      PAPPERS_CONTENT_PREVIEW_LENGTH: 4000
      PAPPERS_JUSTICE_BASE_URL: https://api.pappers.fr/v1/justice
    volumes:
      - /var/www/html/ai/pappers-justice-axiorhub:/var/www/html/ai/pappers-justice-axiorhub
    networks:
      - ai-stack

networks:
  ai-stack:
    external: true
```

---

## Lancer

```bash
docker compose up -d --build
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
        "-v", "/var/www/html/ai/pappers-justice-axiorhub:/app",
        "pappers-justice-axiorhub"
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


