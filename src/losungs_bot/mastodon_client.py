"""Mastodon Client für den Losungs-Bot."""

import structlog
from mastodon import Mastodon

logger = structlog.get_logger()


class MastodonClient:
    """Wrapper für die Mastodon API."""

    def __init__(self, instance_url: str, access_token: str):
        """
        Initialisiert den Mastodon Client.

        Args:
            instance_url: URL der Mastodon-Instanz (z.B. https://mastodon.social)
            access_token: API Access Token
        """
        self.instance_url = instance_url
        self._client = Mastodon(
            access_token=access_token,
            api_base_url=instance_url,
        )
        logger.info("mastodon_client_initialized", instance=instance_url)

    def post_status(
        self,
        content: str,
        visibility: str = "public",
        in_reply_to_id: str | None = None,
    ) -> dict | None:
        """
        Postet einen neuen Status (Toot).

        Args:
            content: Der Text des Posts
            visibility: Sichtbarkeit (public, unlisted, private, direct)
            in_reply_to_id: Optional - ID eines Posts auf den geantwortet wird

        Returns:
            Das erstellte Status-Objekt oder None bei Fehler
        """
        try:
            status = self._client.status_post(
                status=content,
                visibility=visibility,
                in_reply_to_id=in_reply_to_id,
            )
            logger.info(
                "status_posted",
                status_id=status["id"],
                visibility=visibility,
                content_length=len(content),
                is_reply=in_reply_to_id is not None,
            )
            return status
        except Exception as e:
            logger.error("status_post_failed", error=str(e))
            return None

    def verify_credentials(self) -> bool:
        """Überprüft, ob die API-Credentials gültig sind."""
        try:
            account = self._client.account_verify_credentials()
            logger.info(
                "credentials_verified",
                username=account["username"],
                display_name=account["display_name"],
            )
            return True
        except Exception as e:
            logger.error("credentials_verification_failed", error=str(e))
            return False

    def get_account_info(self) -> dict | None:
        """Gibt Informationen über den eigenen Account zurück."""
        try:
            return self._client.account_verify_credentials()
        except Exception as e:
            logger.error("get_account_info_failed", error=str(e))
            return None
