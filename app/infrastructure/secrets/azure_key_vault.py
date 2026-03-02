"""Azure Key Vault client wrapper."""

from __future__ import annotations


class AzureKeyVaultClient:
    """Thin wrapper around the Azure Key Vault Secrets SDK."""

    def __init__(self, vault_url: str, credential: object) -> None:
        from azure.keyvault.secrets import SecretClient  # type: ignore[import-untyped]

        self._client = SecretClient(vault_url=vault_url, credential=credential)

    def get_secret(self, name: str) -> str | None:
        """Return the secret value or *None* if it does not exist."""
        try:
            secret = self._client.get_secret(name)
            return secret.value
        except Exception:
            return None
