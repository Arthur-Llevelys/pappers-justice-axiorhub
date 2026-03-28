# pappers-justice-axiorhub

Serveur MCP Python pour **Pappers Justice**, orienté **contentieux avocat** dans **Open WebUI**.

Backends supportés dans cette version :
- **Pappers Justice**
- **OpenLegi**
- **recherche-entreprises**

---

# 1. Nouveaux tools MCP

## Priorité persistée
- `get_source_priority`
- `set_source_priority`

## Métriques
- `get_backend_metrics`
- `reset_backend_metrics`

## Circuit breaker
- `get_circuit_breaker_status`
- `reset_circuit_breaker`

Les tools précédents restent disponibles :
- `refresh_openapi_cache`
- `run_backend_healthchecks`
- `federated_search_jurisprudence`
- `federated_search_company`
- `get_backend_status`
- `explain_source_selection`

---

# 2. Variables d’environnement

Ajouts V5.5 :

```env
LOCAL_STATE_DIR=/var/www/html/ai/pappers-justice-timo/state
SOURCE_PRIORITY_FILE=/var/www/html/ai/pappers-justice-timo/state/source_priority.json
BACKEND_METRICS_FILE=/var/www/html/ai/pappers-justice-timo/state/backend_metrics.json
CIRCUIT_BREAKER_FILE=/var/www/html/ai/pappers-justice-timo/state/circuit_breaker.json
CIRCUIT_BREAKER_FAILURE_THRESHOLD=3
CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS=120
```

---

# 3. Fichiers ajoutés

- `pappers_mcp/state_store.py`
- `pappers_mcp/metrics.py`
- `pappers_mcp/circuit_breaker.py`

---

# 4. Exemple de workflow

## Voir la priorité effective
1. `get_source_priority`

## Modifier la priorité et la persister
1. `set_source_priority`

## Voir les métriques
1. `get_backend_metrics`

## Réinitialiser les métriques
1. `reset_backend_metrics`

## Voir le circuit breaker
1. `get_circuit_breaker_status`

## Réinitialiser manuellement un backend
1. `reset_circuit_breaker`

---

# 5. Exemple de prompt avocat

```text
Je veux :
1. vérifier l'état des backends
2. voir la priorité effective des sources
3. lancer une recherche fédérée en jurisprudence
4. vérifier quels backends ont été utilisés
5. voir les métriques d'usage
6. vérifier si un backend est temporairement coupé par le circuit breaker
```

---

# 6. Installation

## Étape 1
Déployer dans :

```bash
/var/www/html/ai/pappers-justice-axiorhub
```

## Étape 2
Créer `.env` :

```bash
cp .env.example .env
```

## Étape 3
Vérifier les variables V5.5 :

```env
LOCAL_STATE_DIR=/var/www/html/ai/pappers-justice-axiorhub/state
SOURCE_PRIORITY_FILE=/var/www/html/ai/pappers-justice-axiorhub/state/source_priority.json
BACKEND_METRICS_FILE=/var/www/html/ai/pappers-justice-axiorhub/state/backend_metrics.json
CIRCUIT_BREAKER_FILE=/var/www/html/ai/pappers-justice-axiorhub/state/circuit_breaker.json
CIRCUIT_BREAKER_FAILURE_THRESHOLD=3
CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS=120
```

## Étape 4
Lancer :

```bash
docker compose up -d --build
```

## Étape 5
Tester :
- `get_source_priority`
- `set_source_priority`
- `get_backend_metrics`
- `get_circuit_breaker_status`
- `federated_search_jurisprudence`

---

# 7. Avertissement utile

- la validation juridique finale reste humaine
