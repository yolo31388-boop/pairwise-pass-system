"""赛季通行证 - 带8个bug"""
from dataclasses import dataclass, field

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

    def add_exp(self, player_id, amount, source):
        # bug1: 只看每日
        self.player_exp[player_id] = self.player_exp.get(player_id, 0) + amount

    def get_reward(self, player_id, level):
        # bug2: 免费付费一样
        return self.levels[level].free_reward

    def get_max_level(self):
        # bug3: 无上限
        return 9999

    def add_task_progress(self, player_id, task_id, amount):
        # bug4: 按角色
        if player_id not in self.player_exp:
            self.player_exp[player_id] = 0
        self.player_exp[player_id] += amount

    def can_claim(self, player_id, level):
        # bug5: 不校验等级
        return True

    def season_end(self):
        # bug6: 不结算
        pass

    def can_buy_paid(self, days_left):
        # bug7: 无购买截止
        return True

    def use_exp_potion(self, player_id, count):
        # bug8: 可叠加
        self.player_exp[player_id] = self.player_exp.get(player_id, 0) + count * 1000
        return True
