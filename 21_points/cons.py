from enum import Enum
import random
import re
import time
from typing import Any

from nonebot import get_bot
from nonebot_plugin_uninfo import Uninfo
from pydantic import BaseModel

from zhenxun.configs.config import BotConfig
from zhenxun.utils.platform import PlatformUtils
from zhenxun.utils.rules import ensure_group

NICKNAME = BotConfig.self_nickname


class Card(Enum):
    A = 11
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    J = 10
    Q = 10
    K = 10


DECK = [card for card in Card for _ in range(4)]


class Player(BaseModel):
    """玩家信息"""

    cost: int
    """赌注金额"""
    playeruid: str = ""
    """玩家uid"""
    player: str
    """玩家名称"""
    cardall: list[Card | str] = []
    """玩家牌组"""
    sum: int = 0
    """玩家牌组和"""
    keyA: int = 0
    """玩家当前手牌中A的数量"""
    end: bool = False
    """是否已停牌"""

    def dump(self) -> str:
        """格式化牌组"""
        result = []
        for card in self.cardall:
            if isinstance(card, Card):
                result.append(card.name)
            else:
                result.append(card)
        return ", ".join(result)


class MatchDetail(BaseModel):
    """对局信息"""

    last_update: float = time.time()
    """最后一次更新时间"""
    time: float = time.time()
    """对局开始时间"""
    start: bool = False
    """对局是否开始"""
    playnum: int = 0
    """当前玩家数"""
    endnum: int = 0
    """已出局的玩家数"""
    costall: int = 0
    """总赌注金额"""
    BJ: bool = False
    """是否BlackJack黑杰克(即开局21点)"""
    cardnum: int = 0
    """已拿牌组数量"""
    cardlist: list[Card] = random.sample(DECK, k=len(DECK))
    """当前牌组"""
    players: list[Player] = []
    """玩家列表"""

    def __setattr__(self, name: str, value: Any):
        super().__setattr__(name, value)
        # 每次属性被设置时更新 last_update
        super().__setattr__("last_update", time.time())

    def get_player(self, uid: str) -> Player | None:
        """获取玩家"""
        for player in self.players:
            if player.playeruid == uid:
                return player


MATCH_LIST: dict[str, MatchDetail] = {}
"""对局列表 key:群号 value:MatchDetail"""


async def get_username(uid: str, session: Uninfo) -> str:
    bot = get_bot(session.self_id)
    info = await PlatformUtils.get_user(
        bot, uid, session.scene.id if ensure_group(session) else None
    )
    if info is None:
        return "未知用户"
    name = info.card or info.name
    return re.sub(r"[\x00-\x09\x0b-\x1f\x7f-\x9f]", "", name)
