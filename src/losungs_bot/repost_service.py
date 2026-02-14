"""Service für automatisches Reposten/Boosten von Accounts."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from losungs_bot.mastodon_client import MastodonClient

logger = structlog.get_logger()


class RepostService:
    """Verwaltet das automatische Reposten von bestimmten Accounts."""

    def __init__(
        self,
        mastodon_client: MastodonClient,
        accounts: list[str],
    ):
        """
        Initialisiert den RepostService.

        Args:
            mastodon_client: Der Mastodon-Client
            accounts: Liste von Account-Namen zum Reposten (z.B. ["BibelTV"])
        """
        self._client = mastodon_client
        self._accounts = [a.strip() for a in accounts if a.strip()]
        logger.info(
            "repost_service_initialized",
            accounts=self._accounts,
        )

    def repost_recent_statuses(self, hours: int = 24) -> int:
        """
        Repostet alle Beiträge der konfigurierten Accounts aus den letzten Stunden.

        Args:
            hours: Zeitfenster in Stunden (default: 24)

        Returns:
            Anzahl der geboosteten Beiträge
        """
        if not self._accounts:
            logger.warning("no_repost_accounts_configured")
            return 0

        cutoff_time = datetime.now().astimezone() - timedelta(hours=hours)
        total_boosted = 0

        for acct in self._accounts:
            boosted = self._repost_account(acct, cutoff_time)
            total_boosted += boosted

        logger.info(
            "repost_completed",
            total_boosted=total_boosted,
            accounts_checked=len(self._accounts),
        )
        return total_boosted

    def _repost_account(self, acct: str, cutoff_time: datetime) -> int:
        """
        Repostet Beiträge eines einzelnen Accounts.

        Args:
            acct: Der Account-Name
            cutoff_time: Nur Beiträge nach diesem Zeitpunkt

        Returns:
            Anzahl der geboosteten Beiträge
        """
        # Account suchen
        account = self._client.search_account(acct)
        if not account:
            logger.warning("repost_account_not_found", acct=acct)
            return 0

        # Statuses abrufen
        statuses = self._client.get_account_statuses(
            account["id"],
            limit=40,
            exclude_replies=True,
            exclude_reblogs=True,
        )

        boosted_count = 0
        for status in statuses:
            # Prüfen ob Status im Zeitfenster liegt
            created_at = status.get("created_at")
            if not created_at:
                continue

            # created_at kann ein datetime-Objekt oder ein String sein
            if isinstance(created_at, str):
                # ISO-Format parsen
                try:
                    created_at = datetime.fromisoformat(
                        created_at.replace("Z", "+00:00")
                    )
                except ValueError:
                    continue

            if created_at < cutoff_time:
                # Status ist älter als das Zeitfenster, überspringe
                continue

            # Prüfen ob bereits geboosted
            if status.get("reblogged"):
                logger.debug(
                    "status_already_boosted",
                    status_id=status["id"],
                    acct=acct,
                )
                continue

            # Status boosten
            result = self._client.boost_status(status["id"])
            if result:
                boosted_count += 1
                logger.info(
                    "status_reposted",
                    status_id=status["id"],
                    acct=acct,
                    created_at=str(created_at),
                )

        logger.info(
            "account_repost_completed",
            acct=acct,
            boosted_count=boosted_count,
        )
        return boosted_count
