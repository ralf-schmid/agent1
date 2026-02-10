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

    def post_poll(
        self,
        content: str,
        options: list[str],
        expires_in: int = 86400,
        visibility: str = "public",
    ) -> dict | None:
        """
        Postet einen Status mit Umfrage (Poll).

        Args:
            content: Der Text des Posts
            options: Liste der Antwortmöglichkeiten (2-4 Optionen)
            expires_in: Dauer in Sekunden (default: 24 Stunden)
            visibility: Sichtbarkeit (public, unlisted, private, direct)

        Returns:
            Das erstellte Status-Objekt mit Poll oder None bei Fehler
        """
        try:
            status = self._client.status_post(
                status=content,
                poll={
                    "options": options,
                    "expires_in": expires_in,
                },
                visibility=visibility,
            )
            logger.info(
                "poll_posted",
                status_id=status["id"],
                poll_id=status.get("poll", {}).get("id"),
                options_count=len(options),
                expires_in_hours=expires_in / 3600,
            )
            return status
        except Exception as e:
            logger.error("poll_post_failed", error=str(e))
            return None

    def get_poll(self, poll_id: str) -> dict | None:
        """
        Ruft die Ergebnisse einer Umfrage ab.

        Args:
            poll_id: Die ID der Umfrage

        Returns:
            Das Poll-Objekt mit Ergebnissen oder None bei Fehler
        """
        try:
            poll = self._client.poll(poll_id)
            logger.info(
                "poll_fetched",
                poll_id=poll_id,
                votes_count=poll.get("votes_count", 0),
                expired=poll.get("expired", False),
            )
            return poll
        except Exception as e:
            logger.error("poll_fetch_failed", poll_id=poll_id, error=str(e))
            return None

    def get_status(self, status_id: str) -> dict | None:
        """
        Ruft einen Status ab.

        Args:
            status_id: Die ID des Status

        Returns:
            Das Status-Objekt oder None bei Fehler
        """
        try:
            return self._client.status(status_id)
        except Exception as e:
            logger.error("status_fetch_failed", status_id=status_id, error=str(e))
            return None

    def get_notifications(
        self,
        types: list[str] | None = None,
        since_id: str | None = None,
        limit: int = 40,
    ) -> list[dict]:
        """
        Ruft Benachrichtigungen ab.

        Args:
            types: Filter nach Typen (mention, favourite, reblog, follow)
            since_id: Nur Notifications nach dieser ID
            limit: Maximale Anzahl

        Returns:
            Liste von Notifications
        """
        try:
            notifications = self._client.notifications(
                types=types,
                since_id=since_id,
                limit=limit,
            )
            logger.info(
                "notifications_fetched",
                count=len(notifications),
                types=types,
            )
            return notifications
        except Exception as e:
            logger.error("notifications_fetch_failed", error=str(e))
            return []

    def dismiss_notification(self, notification_id: str) -> bool:
        """
        Markiert eine Benachrichtigung als gelesen.

        Args:
            notification_id: Die ID der Notification

        Returns:
            True wenn erfolgreich
        """
        try:
            self._client.notifications_dismiss(notification_id)
            return True
        except Exception as e:
            logger.error(
                "notification_dismiss_failed",
                notification_id=notification_id,
                error=str(e),
            )
            return False

    def send_direct_message(self, username: str, content: str) -> dict | None:
        """
        Sendet eine Direktnachricht an einen Benutzer.

        Args:
            username: Der Benutzername (mit oder ohne @)
            content: Die Nachricht

        Returns:
            Das Status-Objekt oder None bei Fehler
        """
        # Sicherstellen dass @ vorhanden ist
        if not username.startswith("@"):
            username = f"@{username}"

        message = f"{username} {content}"

        try:
            status = self._client.status_post(
                status=message,
                visibility="direct",
            )
            logger.info(
                "direct_message_sent",
                to_user=username,
                status_id=status["id"],
            )
            return status
        except Exception as e:
            logger.error("direct_message_failed", to_user=username, error=str(e))
            return None

    def get_total_likes(self) -> int:
        """
        Berechnet die Gesamtanzahl der Likes über alle Posts des Accounts.

        Returns:
            Gesamtanzahl der Likes (Favourites)
        """
        total_likes = 0
        try:
            # Eigene Account-ID holen
            me = self._client.me()
            account_id = me["id"]

            # Alle Statuses paginiert abrufen
            statuses = self._client.account_statuses(account_id, limit=40)
            while statuses:
                for status in statuses:
                    total_likes += status.get("favourites_count", 0)

                # Nächste Seite holen
                statuses = self._client.fetch_next(statuses)

            logger.info("total_likes_calculated", total_likes=total_likes)
            return total_likes
        except Exception as e:
            logger.error("total_likes_calculation_failed", error=str(e))
            return 0

