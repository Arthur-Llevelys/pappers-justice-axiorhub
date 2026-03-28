# pappers-justice-timo V5.5

Serveur MCP Python pour **Pappers Justice**, orienté **contentieux avocat** dans **Open WebUI**.

Cette V5.5 ajoute trois briques d’exploitation avancées :

- **persistance réelle** de la priorité des sources dans un fichier de configuration local
- **métriques d’usage par backend**
- **circuit breaker** quand un backend devient franchement instable

Backends supportés dans cette version :
- **Pappers Justice**
- **OpenLegi**
- **recherche-entreprises**

---

# 1. Ce que change la V5.5

La V5.4 savait :
- mettre en cache les schémas OpenAPI
- exécuter des healthchecks automatiques
- gérer une priorité configurable des sources

La V5.5 ajoute une couche de résilience opérationnelle plus sérieuse.

## 1.1 Persistance réelle de la priorité
La priorité des sources peut maintenant être enregistrée dans un fichier local.

Concrètement :
- `set_source_priority` peut persister les préférences
- `get_source_priority` retourne la configuration réellement active
- la configuration persiste entre redémarrages du conteneur si le volume est conservé

## 1.2 Métriques d’usage par backend
Le système comptabilise par backend :
- nombre d’appels
- nombre de succès
- nombre d’échecs
- dernière erreur
- latence cumulée
- latence moyenne

Ces métriques aident à identifier :
- les backends lents
- les backends cassés
- les bascules trop fréquentes
- les schémas OpenAPI pénibles, donc probablement écrits dans un moment d’égarement

## 1.3 Circuit breaker
Quand un backend enchaîne les erreurs :
- il passe en état **open**
- il est temporairement évité
- une nouvelle tentative n’est effectuée qu’après une durée d’attente
- si un appel de reprise réussit, il revient en état **closed**

Cela évite :
- de marteler un backend cassé
- de perdre du temps
- de ralentir toute la fédération

---

# 2. Nouveaux tools MCP

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

# 3. Variables d’environnement

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

# 4. Fichiers ajoutés

- `pappers_mcp/state_store.py`
- `pappers_mcp/metrics.py`
- `pappers_mcp/circuit_breaker.py`

---

# 5. Exemple de workflow

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

# 6. Exemple de prompt avocat

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

# 7. Installation

## Étape 1
Déployer dans :

```bash
/var/www/html/ai/pappers-justice-timo
```

## Étape 2
Créer `.env` :

```bash
cp .env.example .env
```

## Étape 3
Vérifier les variables V5.5 :

```env
LOCAL_STATE_DIR=/var/www/html/ai/pappers-justice-timo/state
SOURCE_PRIORITY_FILE=/var/www/html/ai/pappers-justice-timo/state/source_priority.json
BACKEND_METRICS_FILE=/var/www/html/ai/pappers-justice-timo/state/backend_metrics.json
CIRCUIT_BREAKER_FILE=/var/www/html/ai/pappers-justice-timo/state/circuit_breaker.json
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

# 8. Avertissement utile

La V5.5 améliore fortement :
- la persistance de la configuration
- l’observabilité
- la robustesse face aux backends instables

Mais :
- un circuit breaker n’invente pas des résultats si toutes les sources sont dégradées
- les métriques ne remplacent pas une vraie supervision externe
- la validation juridique finale reste humaine
