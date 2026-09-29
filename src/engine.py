"""赛季通行证 - 修复8个运营事故"""
from dataclasses import dataclass, field

EXP_PER_LEVEL = 1000
MAX_LEVEL = 100
POTION_EXP = 1000
DAILY_POTION_LIMIT = 3
MAX_POTION_STACK = 5
PURCHASE_CUTOFF_DAYS = 7
VALID_EXP_SOURCES = {"daily", "weekly", "season", "purchase", "potion"}

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
        self.claimed = set()
        self.season = 1
        self.character_account = {}
        self.task_progress = {}
        self.overflow_exp = {}
        self.overflow_rewards = {}
        self.potion_used_today = {}
        self.potion_stack = {}

    def _account(self, player_id):
        return self.character_account.get(player_id, player_id)

    def bind_character(self, account_id, player_id):
        self.character_account[player_id] = account_id

    def _level_of(self, account):
        exp = self.player_exp.get(account, 0)
        return min(exp // EXP_PER_LEVEL + 1, MAX_LEVEL)

    def _add_exp_capped(self, account, amount):
        # bug3: 等级上限，溢出经验转为其他奖励
        cap = (MAX_LEVEL - 1) * EXP_PER_LEVEL
        exp = self.player_exp.get(account, 0) + amount
        if exp > cap:
            self.overflow_exp[account] = self.overflow_exp.get(account, 0) + exp - cap
            exp = cap
            boxes = self.overflow_exp[account] // EXP_PER_LEVEL
            if boxes:
                self.overflow_exp[account] %= EXP_PER_LEVEL
                self.overflow_rewards[account] = self.overflow_rewards.get(account, 0) + boxes
        self.player_exp[account] = exp

    def add_exp(self, player_id, amount, source):
        # bug1: 每日/每周/赛季任务/购买等级多渠道经验
        if source not in VALID_EXP_SOURCES:
            raise ValueError(f"未知经验来源: {source}")
        if amount < 0:
            raise ValueError("经验不能为负")
        self._add_exp_capped(self._account(player_id), amount)

    def buy_levels(self, player_id, count):
        self.add_exp(player_id, count * EXP_PER_LEVEL, "purchase")

    def get_reward(self, player_id, level):
        # bug2: 免费线与付费线奖励不同
        lv = self.levels[level]
        if self.paid.get(player_id) or self.paid.get(self._account(player_id)):
            return dict(lv.paid_reward)
        return dict(lv.free_reward)

    def get_max_level(self):
        # bug3: 通行证等级上限
        return MAX_LEVEL

    def add_task_progress(self, player_id, task_id, amount):
        # bug4: 任务进度按账号统一，同账号多角色共享
        account = self._account(player_id)
        key = (account, task_id)
        self.task_progress[key] = self.task_progress.get(key, 0) + amount
        return self.task_progress[key]

    def get_task_progress(self, player_id, task_id):
        return self.task_progress.get((self._account(player_id), task_id), 0)

    def can_claim(self, player_id, level):
        # bug5: 严格按等级领取，未达等级/已领取/无此级均不可领
        if level not in self.levels:
            return False
        account = self._account(player_id)
        if (account, level) in self.claimed:
            return False
        return level <= self._level_of(account)

    def claim(self, player_id, level):
        if not self.can_claim(player_id, level):
            return None
        account = self._account(player_id)
        self.claimed.add((account, level))
        return self.get_reward(player_id, level)

    def season_end(self):
        # bug6: 赛季结束经验清零，新赛季重新开始
        self.season += 1
        self.player_exp.clear()
        self.claimed.clear()
        self.task_progress.clear()
        self.overflow_exp.clear()
        self.overflow_rewards.clear()
        self.potion_used_today.clear()
        self.potion_stack.clear()
        self.paid.clear()

    def can_buy_paid(self, days_left):
        # bug7: 赛季结束前7天停止售卖付费通行证
        return days_left is not None and days_left > PURCHASE_CUTOFF_DAYS

    def use_exp_potion(self, player_id, count):
        # bug8: 经验药水每日使用上限 + 叠加上限
        if count <= 0:
            return False
        account = self._account(player_id)
        if self.potion_used_today.get(account, 0) + count > DAILY_POTION_LIMIT:
            return False
        if self.potion_stack.get(account, 0) + count > MAX_POTION_STACK:
            return False
        self.potion_used_today[account] = self.potion_used_today.get(account, 0) + count
        self.potion_stack[account] = self.potion_stack.get(account, 0) + count
        self._add_exp_capped(account, count * POTION_EXP)
        return True

    def new_day(self):
        self.potion_used_today.clear()
