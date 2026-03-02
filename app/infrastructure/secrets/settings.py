"""Settings resolution with optional Azure Key Vault override."""

from __future__ import annotations

from functools import lru_cache

from app.config import Settings


def _load_from_akv(base: Settings) -> Settings:
    if not base.AZURE_KEY_VAULT_URL:
        return base

    try:
        from azure.identity import DefaultAzureCredential  # type: ignore[import-untyped]

        from app.infrastructure.secrets.azure_key_vault import AzureKeyVaultClient

        credential = DefaultAzureCredential()
        client = AzureKeyVaultClient(vault_url=base.AZURE_KEY_VAULT_URL, credential=credential)

        overrides: dict[str, str] = {}
        db_url = client.get_secret(base.AKV_SECRET_DATABASE_URL)
        if db_url:
            overrides["DATABASE_URL"] = db_url

        if overrides:
            return base.model_copy(update=overrides)
    except Exception:  # noqa: BLE001
        pass

    return base


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached, fully-resolved settings instance (AKV > .env)."""
    from app.config import Settings as S
    base = S()
    return _load_from_akv(base)
