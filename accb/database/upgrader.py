from __future__ import annotations

from typing import Callable

UpgradeFunc = Callable[[], None]


class Upgrader:
    def __init__(self) -> None:
        self.upgrades: list[UpgradeFunc] = []
        """Upgrade-funcs to run, where the i-th function runs only if the version number less than or equal to i."""

    def until_version(self, version: int):
        must_be_for = len(self.upgrades)
        if version != must_be_for:
            raise ValueError(f"next until_version must be for version {must_be_for}")

        def inner(func):
            self.upgrades.append(func)
            return func

        return inner

    def upgrade(self, current_version: int) -> None:
        if current_version < 0:
            raise ValueError(f"invalid version: {current_version}")

        for func in self.upgrades[current_version:]:
            func()

    def get_final_version(self) -> int:
        return len(self.upgrades)
