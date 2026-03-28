from dataclasses import dataclass
import os
from pathlib import Path


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name, str(default))
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer") from exc


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name, "true" if default else "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _csv_env(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    pappers_api_key: str
    pappers_justice_base_url: str
    timeout_seconds: int
    max_page: int
    max_per_page: int
    content_preview_length: int
    log_level: str
    install_path: str
    exports_dir: str
    openlegi_openapi_url: str
    recherche_entreprises_openapi_url: str
    openapi_discovery_timeout_seconds: int
    openapi_cache_dir: str
    openapi_cache_ttl_seconds: int
    auto_healthcheck_on_start: bool
    auto_healthcheck_before_search: bool
    source_priority_jurisprudence: list[str]
    source_priority_company: list[str]
    local_state_dir: str
    source_priority_file: str
    backend_metrics_file: str
    circuit_breaker_file: str
    circuit_breaker_failure_threshold: int
    circuit_breaker_reset_timeout_seconds: int

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("PAPPERS_API_KEY", "").strip()
        if not api_key:
            raise ValueError("PAPPERS_API_KEY is missing")
        exports_dir = os.getenv("EXPORTS_DIR", "/var/www/html/ai/pappers-justice-axiorhub/exports")
        cache_dir = os.getenv("OPENAPI_CACHE_DIR", "/var/www/html/ai/pappers-justice-axiorhub/cache")
        state_dir = os.getenv("LOCAL_STATE_DIR", "/var/www/html/ai/pappers-justice-axiorhub/state")
        Path(exports_dir).mkdir(parents=True, exist_ok=True)
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        Path(state_dir).mkdir(parents=True, exist_ok=True)
        return cls(
            pappers_api_key=api_key,
            pappers_justice_base_url=os.getenv("PAPPERS_JUSTICE_BASE_URL", "https://api.pappers.fr/v1/justice").rstrip("/"),
            timeout_seconds=_int_env("PAPPERS_TIMEOUT_SECONDS", 30),
            max_page=_int_env("PAPPERS_MAX_PAGE", 200),
            max_per_page=_int_env("PAPPERS_MAX_PER_PAGE", 100),
            content_preview_length=_int_env("PAPPERS_CONTENT_PREVIEW_LENGTH", 4000),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            install_path=os.getenv("INSTALL_PATH", "/var/www/html/ai/pappers-justice-axiorhub"),
            exports_dir=exports_dir,
            openlegi_openapi_url=os.getenv("OPENLEGI_OPENAPI_URL", "http://host.docker.internal:8000/Legifrance/openapi.json").strip(),
            recherche_entreprises_openapi_url=os.getenv("RECHERCHE_ENTREPRISES_OPENAPI_URL", "http://host.docker.internal:8000/recherche-entreprises/openapi.json").strip(),
            openapi_discovery_timeout_seconds=_int_env("OPENAPI_DISCOVERY_TIMEOUT_SECONDS", 15),
            openapi_cache_dir=cache_dir,
            openapi_cache_ttl_seconds=_int_env("OPENAPI_CACHE_TTL_SECONDS", 3600),
            auto_healthcheck_on_start=_bool_env("AUTO_HEALTHCHECK_ON_START", True),
            auto_healthcheck_before_search=_bool_env("AUTO_HEALTHCHECK_BEFORE_SEARCH", False),
            source_priority_jurisprudence=_csv_env("SOURCE_PRIORITY_JURISPRUDENCE", "pappers_justice,openlegi"),
            source_priority_company=_csv_env("SOURCE_PRIORITY_COMPANY", "recherche_entreprises"),
            local_state_dir=state_dir,
            source_priority_file=os.getenv("SOURCE_PRIORITY_FILE", f"{state_dir}/source_priority.json"),
            backend_metrics_file=os.getenv("BACKEND_METRICS_FILE", f"{state_dir}/backend_metrics.json"),
            circuit_breaker_file=os.getenv("CIRCUIT_BREAKER_FILE", f"{state_dir}/circuit_breaker.json"),
            circuit_breaker_failure_threshold=_int_env("CIRCUIT_BREAKER_FAILURE_THRESHOLD", 3),
            circuit_breaker_reset_timeout_seconds=_int_env("CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS", 120),
        )
