import json
import time

from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import (
    Alconna,
    Args,
    At,
    Image,
    Match,
    UniMessage,
    on_alconna,
)
from nonebot_plugin_htmlrender import text_to_pic
from nonebot_plugin_uninfo import Uninfo

from zhenxun.configs.utils.models import PluginExtraData
from zhenxun.models.user_console import UserConsole
from zhenxun.utils.enum import GoldHandle
from zhenxun.utils.rules import ensure_group

from .cons import MATCH_LIST, NICKNAME, Card, MatchDetail, Player, get_username

__plugin_meta__ = PluginMetadata(
    name="21点",
    description="21点青春版，让金币再次焕发光辉",
    usage=f"""
    21点帮助 : 获取帮助
    21点 [赌注金额] : 第一位玩家发起活动
    入场 [赌注金额] : 接受21点赌局
    开局 : 人齐后开局
    拿牌 : 拿牌指令
    停牌 :  宣布停止
    结束 : 所有人停牌，或者超时90s后，结算指令

    **说明**

    {NICKNAME}入场费为玩家平均值，必要点数17
    起手2牌合计21点为黑杰克，比其他21点大
    获胜奖励为胜者按各自入场费，均分其他人金币
    """,
    extra=PluginExtraData(
        author="冥乐",
        version="2.0",
        menu_type=f"{NICKNAME}赌场",
        superuser_help="数据显示: 查看全部群聊21点数据\n数据清空: 清理本群",
    ).dict(),
)

help = on_alconna(Alconna("21点帮助"), priority=5, block=True)
opendian = on_alconna(
    Alconna("21点", Args["dz?", int | str]), rule=ensure_group, priority=5, block=True
)
ruchang = on_alconna(
    Alconna("入场", Args["dz?", int | str]), rule=ensure_group, priority=5, block=True
)
kaiju = on_alconna(Alconna("开局"), rule=ensure_group, priority=5, block=True)
napai = on_alconna(Alconna("拿牌"), rule=ensure_group, priority=5, block=True)
tingpai = on_alconna(Alconna("停牌"), rule=ensure_group, priority=5, block=True)
jiesuan = on_alconna(Alconna("结束"), rule=ensure_group, priority=5, block=True)
tttt = on_alconna(Alconna("数据显示"), priority=5, permission=SUPERUSER, block=True)
xxxx = on_alconna(Alconna("数据清空"), priority=5, permission=SUPERUSER, block=True)

msga = "输入指令“21点帮助”获取详细信息"


@help.handle()
async def _():
    await UniMessage(
        "21点帮助 : 获取帮助\n"
        "21点 [赌注金额] : 第一位玩家发起活动\n"
        "入场 [赌注金额] : 接受21点赌局\n"
        "开局 : 人齐后开局\n"
        "拿牌 : 拿牌指令\n"
        "停牌 :  宣布停止\n"
        "结束 : 所有人停牌，或者超时90s后，结算指令\n\n"
        "**说明**\n\n"
        f"{NICKNAME}入场费为玩家平均值，必要点数17\n"
        "起手2牌合计21点为黑杰克，比其他21点大\n"
        "获胜奖励为胜者按各自入场费，均分其他人金币"
    ).finish(
        reply_to=True,
    )


@opendian.handle()
async def _(session: Uninfo, dz: Match[int | str]):
    msg = str(dz.result) if dz.available else None
    uid = session.user.id
    group = session.scene.id
    if group in MATCH_LIST:
        await UniMessage("请勿重复发起对局").finish(reply_to=True)
    player_name = await get_username(uid, session)
    if group in MATCH_LIST:
        await UniMessage(f"上一场21点还未结束，请输入'入场'.{msga}").finish(
            reply_to=True
        )
    if msg:
        if msg.isdigit() and int(msg) > 0:
            cost = int(msg)
            if cost > 10000000:
                await UniMessage(f"{NICKNAME}不接受10，000，000以上的赌注哦").finish(
                    reply_to=True
                )
            if cost < 20:
                await UniMessage(f"{NICKNAME}觉得20以下的赌注不得劲哎").finish(
                    reply_to=True
                )
        else:
            await UniMessage("赌注是数字啊喂").finish(reply_to=True)
    else:
        await UniMessage("请输入你的赌注").finish(reply_to=True)
    user = await UserConsole.get_user(uid)
    assert user
    if user.gold < cost:
        await UniMessage(f"金币不够还想来21点？\n你的金币余额为{user.gold}").finish(
            reply_to=True,
        )
    MATCH_LIST[group] = MatchDetail()
    await ruchangx(group, uid, player_name, cost)
    await UniMessage([At("user", uid), f" 发起了一场21点挑战\n{msga}"]).send()


@ruchang.handle()
async def _(session: Uninfo, dz: Match[int | str]):
    msg = str(dz.result) if dz.available else None
    uid = session.user.id
    group = session.scene.id
    player_name = await get_username(uid, session)
    if group not in MATCH_LIST:
        await UniMessage(f"21点未开场，请输入'21点'开场\n{msga}").finish(reply_to=True)
    match_obj = MATCH_LIST[group]
    if match_obj.start:
        await UniMessage("21点已开场，不能再入场!").finish(reply_to=True)
    if match_obj.playnum >= 12:
        await UniMessage(f"人太多啦，{NICKNAME}受不住啦").finish()
    if match_obj.get_player(uid):
        await UniMessage(f"你已入场，请勿重复操作\n{msga}").finish(reply_to=True)
    if msg:
        if msg.isdigit() and int(msg) > 0:
            cost = int(msg)
            if cost > 10000000:
                await UniMessage(f"{NICKNAME}不接受10，000，000以上的赌注哦").finish(
                    reply_to=True
                )
            if cost < 20:
                await UniMessage(f"{NICKNAME}觉得20以下的赌注不得劲哎").finish(
                    reply_to=True
                )
        else:
            await UniMessage("赌注是数字啊喂").finish(reply_to=True)
    else:
        await UniMessage("请输入你的赌注").finish(reply_to=True)
    if cost < (match_obj.players[0].cost / 2):
        await UniMessage("赌注不得小于开局玩家的1/2").finish(reply_to=True)
    user = await UserConsole.get_user(uid)
    assert user
    if user.gold < cost:
        await UniMessage(f"金币不够还想来21点？\n你的金币余额为{user.gold}").finish(
            reply_to=True,
        )
    await ruchangx(group, uid, player_name, cost)
    await UniMessage(f"你已入场，赌注为 {msg} 金币").finish(reply_to=True)


@kaiju.handle()
async def _(session: Uninfo):
    group = session.scene.id
    if group not in MATCH_LIST:
        await UniMessage("请先发起对局").finish(reply_to=True)
    match_obj = MATCH_LIST[group]
    if match_obj.start:
        await UniMessage("请勿重复开启对局").finish(reply_to=True)
    else:
        match_obj.start = True
        match_obj.time = time.time()
    cost = int(match_obj.costall / match_obj.playnum)
    match_obj.costall += cost
    match_obj.players.insert(
        0,
        Player(
            cost=cost,
            player=NICKNAME,
        ),
    )
    for _ in range(2):
        i = 0
        while i <= match_obj.playnum:
            x = match_obj.cardnum
            nextcard = match_obj.cardlist[x]
            match_obj.cardnum += 1
            if nextcard == Card.A:
                match_obj.players[i].sum += 11
                match_obj.players[i].keyA += 1
            else:
                match_obj.players[i].sum += nextcard.value
            match_obj.players[i].cardall.append(nextcard)
            if match_obj.players[i].keyA > 0 and match_obj.players[i].sum > 21:
                match_obj.players[i].keyA -= 1
                match_obj.players[i].sum -= 10
            i += 1
    i = 0
    while i <= match_obj.playnum:
        if match_obj.players[i].sum == 21:
            match_obj.players[i].cardall.append("已BlackJack")
            match_obj.BJ = True
        i += 1
    i = 1
    if match_obj.BJ:
        await end(group)
    else:
        msgsend = msgout(group)
        img = await text_to_pic(msgsend, width=300)
        await UniMessage(Image(raw=img)).finish()


@napai.handle()
async def _(session: Uninfo):
    uid = session.user.id
    group = session.scene.id
    if group not in MATCH_LIST:
        await UniMessage("没有正在进行的对局").finish(reply_to=True)
    match_obj = MATCH_LIST[group]
    if not match_obj.start:
        await UniMessage("对局尚未开始").finish(reply_to=True)
    player = match_obj.get_player(uid)
    if not player:
        await UniMessage("你没有入场！").finish(reply_to=True)
    if player.end:
        await UniMessage(f"你已经停牌!抽到的卡为{player.dump()}").finish(reply_to=True)
    x = match_obj.cardnum
    nextcard = match_obj.cardlist[x]
    match_obj.cardnum += 1
    if nextcard == Card.A:
        player.sum += 11
        player.keyA += 1
    else:
        player.sum += nextcard.value
    player.cardall.append(nextcard)
    if player.keyA > 0 and player.sum > 21:
        player.keyA -= 1
        player.sum -= 10
    if player.sum > 21:
        player.end = True
        match_obj.endnum += 1
        player.cardall.append("炸了")
        await UniMessage(
            [
                At("user", player.playeruid),
                f" 抽到的卡为 {player.dump()}.总点数为{player.sum}，停牌处理",
            ]
        ).finish()
    if player.sum == 21:
        player.end = True
        player.cardall.append("已21点，停牌")
        match_obj.endnum += 1
        await UniMessage(
            [
                At("user", player.playeruid),
                f" 抽到的卡为 {player.dump()}",
            ]
        ).finish()
    await UniMessage(
        [
            At("user", player.playeruid),
            f" 抽到的卡为 {player.dump()},总点数为 {player.sum}",
        ]
    ).finish()


@tingpai.handle()
async def _(session: Uninfo):
    uid = session.user.id
    group = session.scene.id
    if group not in MATCH_LIST:
        await UniMessage("没有正在进行的对局").finish(reply_to=True)
    match_obj = MATCH_LIST[group]
    if not match_obj.start:
        await UniMessage("对局尚未开始").finish(reply_to=True)
    player = match_obj.get_player(uid)
    if not player:
        await UniMessage("你没有入场！").finish(reply_to=True)
    if not player.end:
        player.end = True
        match_obj.endnum += 1
        player.cardall.append("已停牌")
    await UniMessage([At("user", player.playeruid), " 已停牌"]).finish()


@jiesuan.handle()
async def _(session: Uninfo):
    uid = session.user.id
    group = session.scene.id
    if group not in MATCH_LIST:
        await UniMessage("没有进行中牌局！").finish(reply_to=True)
    match_obj = MATCH_LIST[group]
    if not match_obj.start:
        await UniMessage("没有正在进行的对局!").finish(reply_to=True)
    player = match_obj.get_player(uid)
    if not player:
        await UniMessage("你没有入场，不能进行此操作!").finish(reply_to=True)
    if time.time() - match_obj.time  < 90:
        await UniMessage("对局没有进行 90s , 不能结束!").finish(reply_to=True)
    if not player.end:
        player.end = True
        match_obj.endnum += 1
        player.cardall.append("已停牌")
    if match_obj.endnum == match_obj.playnum:
        await end(group)
    else:
        out = msgout(group) + "\n有人没停牌"
        img = await text_to_pic(out, "", 400)
        await UniMessage(Image(raw=img)).finish()


async def ruchangx(group: str, uid: str, player_name: str, cost: int):
    match_obj = MATCH_LIST[group]
    match_obj.playnum += 1
    match_obj.players.append(Player(cost=cost, playeruid=uid, player=player_name))
    match_obj.costall += cost
    await UserConsole.reduce_gold(uid, cost, GoldHandle.PLUGIN, "21_points")


async def end(group: str):
    match_obj = MATCH_LIST[group]
    while match_obj.players[0].sum < 17 and not match_obj.BJ:
        x = match_obj.cardnum
        nextcard = match_obj.cardlist[x]
        match_obj.cardnum += 1
        if nextcard == Card.A:
            match_obj.players[0].sum += 11
            match_obj.players[0].keyA += 1
        else:
            match_obj.players[0].sum += nextcard.value
        match_obj.players[0].cardall.append(nextcard)
        if match_obj.players[0].keyA > 0 and match_obj.players[0].sum > 21:
            match_obj.players[0].keyA -= 1
            match_obj.players[0].sum -= 10
    if match_obj.players[0].sum > 21:
        match_obj.players[0].cardall.append("炸了")
    out = msgout(group)
    winer = 0
    key = 0
    winall = 0
    max_player = match_obj.playnum
    i = 0
    while i <= max_player:
        if match_obj.players[i].sum > key and match_obj.players[i].sum < 22:
            key = match_obj.players[i].sum
        i += 1
    i = 0
    while i <= max_player:
        if match_obj.players[i].sum == key:
            winall += match_obj.players[i].cost
            winer += 1
        i += 1
    if winer == 0:
        out += "无人生还，金币返还\n"
        i = 1
        while i <= max_player:
            gold = match_obj.players[i].cost
            await wingold(group, i, gold)
            i += 1
    i = 0
    while i <= max_player:
        if match_obj.players[i].sum == key:
            gold = int(match_obj.players[i].cost / winall * match_obj.costall)
            await wingold(group, i, gold)
            out += f"{match_obj.players[i].player}赢得了{gold}金币\n"
        i += 1
    img = await text_to_pic(out, "", 400)
    await UniMessage(Image(raw=img)).send()
    MATCH_LIST.pop(group)


async def wingold(group: str, i: int, gold: int):
    if i > 0:
        uid = MATCH_LIST[group].players[i].playeruid
        await UserConsole.add_gold(uid, gold, "21_points")


def msgout(group: str) -> str:
    match_obj = MATCH_LIST[group]
    msg = ""
    i = 0
    while i <= match_obj.playnum:
        player = match_obj.players[i]
        msg += f"{player.player} 抽到的卡为{player.dump()}.总点数为{player.sum}\n"
        i += 1
    return msg


@tttt.handle()
async def _():
    await UniMessage(
        Image(
            raw=await text_to_pic(json.dumps(MATCH_LIST, indent=4, ensure_ascii=False))
        )
    ).send()


@xxxx.handle()
async def _(session: Uninfo):
    try:
        MATCH_LIST.pop(session.scene.id)
        await UniMessage("已强制结束本群牌局").send()
    except KeyError:
        await UniMessage("该群没有牌局").send()
