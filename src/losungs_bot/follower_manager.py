"""Verwaltung von Follower-Interaktionen."""

import json
from pathlib import Path

import structlog
from mastodon import Mastodon

logger = structlog.get_logger()


class FollowerManager:
    """Verwaltet Follower-Interaktionen wie Auto-Follow und Willkommensnachrichten."""

    # Willkommensnachricht für neue Follower
    WELCOME_MESSAGE = """👋 Willkommen bei den Losungen!

Schön, dass du dabei bist! 📖

Jeden Morgen um 6:00 Uhr poste ich die Herrnhuter Tageslosung mit:
✨ Altes Testament Vers
💫 Neues Testament Vers
🔗 Links zu BibleServer

Samstags gibt es außerdem eine Gottesdienst-Erinnerung für den Sonntag.

🎧 Die Losungen als Podcast:
🍎 https://podcasts.apple.com/de/podcast/die-losungen/id1434728607
🟢 https://open.spotify.com/show/12L3SnnMI5JMDJVtQCqBxh

Gottes Segen! 🙏"""

    def __init__(
        self,
        client: Mastodon,
        state_file: str = "data/follower_state.json",
        notify_account: str | None = None,
    ):
        """
        Initialisiert den FollowerManager.

        Args:
            client: Mastodon API Client
            state_file: Pfad zur State-Datei für bekannte Follower
            notify_account: Account für Benachrichtigungen (z.B. "ralf_schmid@chaos.social")
        """
        self._client = client
        self._state_file = Path(state_file)
        self._notify_account = notify_account
        self._known_followers: set[str] = self._load_state()

        logger.info(
            "follower_manager_initialized",
            known_followers=len(self._known_followers),
            notify_account=notify_account,
        )

    def _load_state(self) -> set[str]:
        """Lädt bekannte Follower aus der State-Datei."""
        if self._state_file.exists():
            try:
                with open(self._state_file) as f:
                    data = json.load(f)
                    return set(data.get("known_followers", []))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("state_load_failed", error=str(e))
        return set()

    def _save_state(self) -> None:
        """Speichert bekannte Follower in die State-Datei."""
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self._state_file, "w") as f:
                json.dump({"known_followers": list(self._known_followers)}, f)
        except OSError as e:
            logger.error("state_save_failed", error=str(e))

    def check_new_followers(self) -> list[dict]:
        """
        Prüft auf neue Follower.

        Returns:
            Liste der neuen Follower-Accounts
        """
        try:
            # Alle Follower abrufen (limitiert auf die neuesten)
            followers = self._client.account_followers(
                self._client.me()["id"],
                limit=40,
            )

            new_followers = []
            for follower in followers:
                follower_id = str(follower["id"])
                if follower_id not in self._known_followers:
                    new_followers.append(follower)
                    self._known_followers.add(follower_id)

            if new_followers:
                self._save_state()
                logger.info(
                    "new_followers_found",
                    count=len(new_followers),
                    accounts=[f["acct"] for f in new_followers],
                )

            return new_followers

        except Exception as e:
            logger.error("check_followers_failed", error=str(e))
            return []

    def follow_back(self, account: dict) -> bool:
        """
        Folgt einem Account zurück.

        Args:
            account: Der Account dem gefolgt werden soll

        Returns:
            True bei Erfolg
        """
        try:
            self._client.account_follow(account["id"])
            logger.info(
                "followed_back",
                account=account["acct"],
                display_name=account.get("display_name", ""),
            )
            return True
        except Exception as e:
            logger.error("follow_back_failed", account=account["acct"], error=str(e))
            return False

    def send_welcome_message(self, account: dict) -> bool:
        """
        Sendet eine Willkommensnachricht an einen neuen Follower.

        Args:
            account: Der neue Follower

        Returns:
            True bei Erfolg
        """
        try:
            # Unlisted Post mit Mention (keine DM, respektvoller)
            mention = f"@{account['acct']}"
            message = f"{mention}\n\n{self.WELCOME_MESSAGE}"

            self._client.status_post(
                status=message,
                visibility="unlisted",  # Nicht im öffentlichen Feed
            )

            logger.info("welcome_message_sent", account=account["acct"])
            return True

        except Exception as e:
            logger.error(
                "welcome_message_failed",
                account=account["acct"],
                error=str(e),
            )
            return False

    def notify_admin(self, message: str) -> bool:
        """
        Sendet eine Benachrichtigung an den Admin-Account.

        Args:
            message: Die Nachricht

        Returns:
            True bei Erfolg
        """
        if not self._notify_account:
            return False

        try:
            mention = f"@{self._notify_account}"
            full_message = f"{mention}\n\n{message}"

            self._client.status_post(
                status=full_message,
                visibility="direct",  # Nur für den Empfänger sichtbar
            )

            logger.info("admin_notified", account=self._notify_account)
            return True

        except Exception as e:
            logger.error(
                "admin_notify_failed",
                account=self._notify_account,
                error=str(e),
            )
            return False

    def process_new_followers(self) -> int:
        """
        Verarbeitet alle neuen Follower: Follow-Back + Willkommensnachricht.

        Returns:
            Anzahl verarbeiteter Follower
        """
        new_followers = self.check_new_followers()

        for follower in new_followers:
            # Follow zurück
            self.follow_back(follower)

            # Willkommensnachricht senden
            self.send_welcome_message(follower)

            # Admin benachrichtigen
            if self._notify_account:
                self.notify_admin(
                    f"🆕 Neuer Follower: @{follower['acct']}\n"
                    f"Name: {follower.get('display_name', 'Unbekannt')}\n"
                    f"Followers: {follower.get('followers_count', 0)}"
                )

        return len(new_followers)

    def initialize_known_followers(self) -> int:
        """
        Initialisiert die Liste bekannter Follower (ohne Nachrichten zu senden).
        Nützlich beim ersten Start.

        Returns:
            Anzahl der initialisierten Follower
        """
        try:
            me = self._client.me()
            # Alle bestehenden Follower laden (paginiert)
            followers = self._client.account_followers(me["id"], limit=80)

            # Pagination: Alle Follower laden
            all_followers = list(followers)
            while followers:
                followers = self._client.fetch_next(followers)
                if followers:
                    all_followers.extend(followers)

            # Als bekannt markieren
            for follower in all_followers:
                self._known_followers.add(str(follower["id"]))

            self._save_state()
            logger.info("followers_initialized", count=len(self._known_followers))
            return len(self._known_followers)

        except Exception as e:
            logger.error("initialize_followers_failed", error=str(e))
            return 0
