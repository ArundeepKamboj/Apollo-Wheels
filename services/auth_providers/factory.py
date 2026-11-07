import os

from .corporate_oidc import CorporateOidcProvider
from .local_demo import LocalDemoProvider


def identity_provider():
    provider = os.getenv("AUTH_PROVIDER", "local").lower()
    if provider == "local":
        if os.getenv("AUTH_LOCAL_DEMO_ENABLED", "true").lower() != "true":
            raise RuntimeError("The local demo identity provider is disabled by configuration.")
        return LocalDemoProvider()
    if provider == "oidc":
        if os.getenv("AUTH_OIDC_ENABLED", "false").lower() != "true":
            raise RuntimeError("Corporate OIDC is disabled by configuration.")
        return CorporateOidcProvider()
    raise RuntimeError(f"Unsupported identity provider: {provider}")
