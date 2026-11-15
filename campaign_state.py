class CampaignProgress:
    """Gate map progression on a collected core and a cleared enemy roster."""

    def __init__(self, level_count: int) -> None:
        if level_count < 1:
            raise ValueError("A campaign needs at least one level.")
        self.level_count = level_count
        self.level_index = 0
        self.complete = False
        self.core_collected = False

    def collect_core(self) -> bool:
        if self.complete or self.core_collected:
            return False
        self.core_collected = True
        return True

    def can_exit(self, enemies_remaining: int) -> bool:
        return not self.complete and self.core_collected and enemies_remaining == 0

    def advance(self, enemies_remaining: int) -> bool:
        if not self.can_exit(enemies_remaining):
            return False
        if self.level_index + 1 == self.level_count:
            self.complete = True
        else:
            self.level_index += 1
            self.core_collected = False
        return True

    def retry(self) -> None:
        if self.complete:
            self.level_index = 0
        self.complete = False
        self.core_collected = False
