"""通行证测试"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.engine import PassSystem, PassLevel

class TestReward:
    def test_paid_differs_from_free(self):
        ps = PassSystem()
        ps.levels = {1: PassLevel(1,{"gold":100},{"gold":1000,"skin":"rare"})}
        ps.paid = {"p1": True}
        r = ps.get_reward("p1", 1)
        assert r.get("skin") == "rare", "付费奖励与免费一样"

class TestClaim:
    def test_claim_requires_level(self):
        ps = PassSystem()
        ps.player_exp = {"p1": 0}
        ps.levels = {10: PassLevel(10,{},{})}
        assert not ps.can_claim("p1", 10), "未达等级可领奖励"
