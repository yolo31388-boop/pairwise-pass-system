"""赛季通行证系统"""
from dataclasses import dataclass, field

EXP_PER_LEVEL = 1000
MAX_LEVEL = 100
PURCHASE_CUTOFF_DAYS = 7
POTION_DAILY_LIMIT = 3
POTION_STACK_LIMIT = 5
POTION_EXP = 1000
VALID_SOURCES = {"daily", "weekly", "season", "purchase"}


@dataclass
class PassLevel:
    level: int
    free_reward: dict
    paid_reward: dict


class PassSystem:
    def __init__(self):
        self.levels: dict[int, PassLevel] = {}
        self.player_exp = {}
        self.paid = {}
        self.claimed = {}
        self.accounts = {}
        self.task_progress = {}
        self.overflow_rewards = {}
        self.potions_used_today = {}
        self.active_potions = {}
        self.season = 1

    def _account(self, player_id):
        return self.accounts.get(player_id, player_id)

    def bind_character(self, account_id, player_id):
        self.accounts[player_id] = account_id

    def get_level(self, player_id):
        exp = self.player_exp.get(self._account(player_id), 0)
        return min(exp // EXP_PER_LEVEL, MAX_LEVEL)

    def add_exp(self, player_id, amount, source):
        # fix1: 每日/每周/赛季任务/购买等级均为合法经验来源
        if source not in VALID_SOURCES:
            raise ValueError(f"非法经验来源: {source}")
        if amount < 0:
            raise ValueError("经验不能为负")
        account = self._account(player_id)
        exp = self.player_exp.get(account, 0) + amount
        # fix3: 等级上限，超出部分转为溢出奖励
        cap = MAX_LEVEL * EXP_PER_LEVEL
        if exp > cap:
            overflow = exp - cap
            exp = cap
            crates = overflow // EXP_PER_LEVEL
            if crates:
                self.overflow_rewards[account] = (
                    self.overflow_rewards.get(account, 0) + crates
                )
        self.player_exp[account] = exp

    def get_reward(self, player_id, level):
        # fix2: 付费线发付费专属奖励，免费线发免费奖励
        account = self._account(player_id)
        pl = self.levels[level]
        if self.paid.get(account) or self.paid.get(player_id):
            return pl.paid_reward
        return pl.free_reward

    def get_max_level(self):
        # fix3: 通行证等级上限
        return MAX_LEVEL

    def add_task_progress(self, player_id, task_id, amount):
        # fix4: 任务进度按账号统一，同账号多角色共享
        account = self._account(player_id)
        progress = self.task_progress.setdefault(account, {})
        progress[task_id] = progress.get(task_id, 0) + amount

    def get_task_progress(self, player_id, task_id):
        return self.task_progress.get(self._account(player_id), {}).get(task_id, 0)

    def can_claim(self, player_id, level):
        # fix5: 严格按等级领取，未达到不能领，已领不能重复领
        if level not in self.levels:
            return False
        if level > self.get_level(player_id):
            return False
        account = self._account(player_id)
        return level not in self.claimed.setdefault(account, set())

    def claim(self, player_id, level):
        if not self.can_claim(player_id, level):
            return None
        account = self._account(player_id)
        self.claimed[account].add(level)
        return self.get_reward(player_id, level)

    def season_end(self):
        # fix6: 赛季结束经验清零，新赛季重新开始
        self.player_exp.clear()
        self.claimed.clear()
        self.task_progress.clear()
        self.paid.clear()
        self.potions_used_today.clear()
        self.active_potions.clear()
        self.overflow_rewards.clear()
        self.season += 1

    def can_buy_paid(self, days_left):
        # fix7: 赛季结束前7天停止售卖付费通行证
        return days_left >= PURCHASE_CUTOFF_DAYS

    def use_exp_potion(self, player_id, count):
        # fix8: 经验药水有每日使用上限和叠加上限
        account = self._account(player_id)
        used_today = self.potions_used_today.get(account, 0)
        active = self.active_potions.get(account, 0)
        applied = 0
        for _ in range(count):
            if used_today >= POTION_DAILY_LIMIT:
                break
            if active >= POTION_STACK_LIMIT:
                break
            used_today += 1
            active += 1
            applied += 1
        if applied:
            self.potions_used_today[account] = used_today
            self.active_potions[account] = active
            self.add_exp(player_id, applied * POTION_EXP, "daily")
        return applied
