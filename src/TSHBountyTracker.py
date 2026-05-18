from qtpy.QtCore import QObject, Signal
from .StateManager import StateManager
from .TSHTournamentDataProvider import TSHTournamentDataProvider
from .Helpers.TSHDictHelper import deep_get


class TSHBountyTrackerSignals(QObject):
    bounty_refresh = Signal()


class TSHBountyTracker:
    instance: "TSHBountyTracker" = None
    signals: TSHBountyTrackerSignals = TSHBountyTrackerSignals()

    BOUNTY_SEED_THRESHOLD = 8

    def __init__(self):
        # Gamertags (lowercase) of top-8 players who have been upset in this bracket
        self._claimed: set[str] = set()
        TSHTournamentDataProvider.instance.signals.completed_sets_updated.connect(
            self._on_completed_sets_updated)

    def _on_completed_sets_updated(self, sets: list):
        self._recompute_claimed(sets)
        self.signals.bounty_refresh.emit()

    def _recompute_claimed(self, sets: list):
        self._claimed = set()
        for s in sets:
            loser_seed = s.get("loser_seed", 0)
            winner_seed = s.get("winner_seed", 0)
            loser_tag = deep_get(s, "loser_team.1.gamertag", "").lower()

            if not loser_tag or not loser_seed:
                continue

            # Upset: a higher-seeded player (worse rank) beat a top-8 seed
            if loser_seed <= self.BOUNTY_SEED_THRESHOLD and winner_seed > loser_seed:
                self._claimed.add(loser_tag)

    def has_active_bounty(self, gamertag: str, seed: int) -> bool:
        """Return True if this player holds an unclaimed bounty."""
        return (
            seed <= self.BOUNTY_SEED_THRESHOLD
            and gamertag.lower() not in self._claimed
        )


TSHBountyTracker.instance = TSHBountyTracker()
