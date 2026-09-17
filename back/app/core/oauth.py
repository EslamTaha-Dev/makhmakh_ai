from authlib.integrations.starlette_client import OAuth

from app.core.config import get_settings


oauth = OAuth()
settings = get_settings()

if settings.google_client_id and settings.google_client_secret:
    oauth.register(
        name="google",
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        client_kwargs={"scope": "openid email profile"},
    )

if settings.ms_client_id and settings.ms_client_secret:
    oauth.register(
        name="microsoft",
        server_metadata_url=(
            f"https://login.microsoftonline.com/{settings.ms_tenant}/v2.0/"
            ".well-known/openid-configuration"
        ),
        client_id=settings.ms_client_id,
        client_secret=settings.ms_client_secret,
        client_kwargs={"scope": "openid email profile"},
    )
