import re

from nonebot import *
from nonebot.adapters.onebot.v11 import Message, MessageSegment, MessageEvent

from ..api.chess import Chess, tempDir, Command
from ..config import cfg
from ..utils.util import pre_command

Gomocup = on_regex(pattern=r'^/wzq', priority=cfg.command_priority, block=cfg.command_block)
ChessRecoder = dict()
CommandDict = dict()


async def show(chess: Chess, args: [] = None):
    if not chess.start:
        await Gomocup.send("游戏未开始")
        return
    chess.saveImg()
    await Gomocup.send(Message(MessageSegment.image(tempDir)))
    return


async def log(chess: Chess, args: [] = None):
    dir = ""
    for i in chess.record:
        dir += str(i[0] + 1) + " " + str(i[1] + 1) + " "
    await Gomocup.send(dir + "\n" + chess.logmessage())
    return


async def choose_difficulty(chess: Chess, args: []):
    if args[0] == 'easy':
        chess.difficult = 0.2
        await Gomocup.send("你选择了简单难度，步时{0}s".format(chess.difficult))
        return
    elif args[0] == 'normal':
        chess.difficult = 1
        await Gomocup.send("你选择了普通难度，步时{0}s".format(chess.difficult))
        return
    elif args[0] == 'hard':
        chess.difficult = 3
        await Gomocup.send("你选择了困难难度，步时{0}s".format(chess.difficult))
        return


async def choose_side(chess: Chess, args: []):
    if chess.start:
        await Gomocup.send("游戏已经开始")
        return
    if args[0] == 'black':
        await Gomocup.send("你选择了黑棋，\n/wzq [x] [y] -> 选择落点")
        chess.start = True
        return
    elif args[0] == 'white':
        p = chess.turnMove()
        chess.record.append(p)
        chess.saveImg()
        await Gomocup.send(Message(MessageSegment.image(tempDir)))
        await Gomocup.send("你选择了白棋，\n/wzq [x] [y] -> 选择落点")
        chess.start = True
        return


async def player_move(chess: Chess, args: []):
    if not chess.start:
        await Gomocup.send("游戏未开始,\n/wzq black -> 黑棋起手\n/wzq white -> 白棋起手")
        return
    x = int(args[0]) - 1
    y = int(args[1]) - 1
    chess.record.append([x, y])
    if chess.check_win():
        await Gomocup.send("你赢了")
        chess.start = False
        chess.record = []
        return

    p = chess.turnMove()
    chess.record.append(p)
    chess.saveImg()
    next = chess.get_next()
    await Gomocup.send("{0},{1} -> {2}".format(p[0] + 1, p[1] + 1, next) + Message(MessageSegment.image(tempDir)))
    if chess.check_win():
        await Gomocup.send(message="你输了")
        chess.start = False
        chess.record = []
        return
    chess.saveRecord()


async def bot_move(chess: Chess, args: []):
    if not chess.start:
        await Gomocup.send("游戏未开始,\n/wzq black -> 黑棋起手\n/wzq white -> 白棋起手")
        return
    p = chess.turnMove()
    chess.record.append(p)
    chess.saveImg()
    next = chess.get_next()
    await Gomocup.send("{0},{1} -> {2}".format(p[0] + 1, p[1] + 1, next) + Message(MessageSegment.image(tempDir)))
    if chess.check_win():
        await Gomocup.send(message="你输了")
        chess.start = False
        chess.record = []
        return
    chess.saveRecord()


async def back(chess: Chess, args: []):
    if not chess.start:
        await Gomocup.send("游戏未开始,\n/wzq black -> 黑棋起手\n/wzq white -> 白棋起手")
        return
    if len(chess.record) < 2:
        await Gomocup.send("至少需要两步棋才能悔棋")
        return
    chess.record.remove(chess.record[-1])
    chess.record.remove(chess.record[-1])
    chess.saveImg()
    await Gomocup.send("悔棋成功\n" + Message(MessageSegment.image(tempDir)))


async def help(chess: Chess, args: []):
    cmd = "/wzq \n\t"
    for i in CommandDict:
        cmd += i + " -> " + CommandDict[i].description + "\n\t"
    cmd = cmd[:-2]
    await Gomocup.send(cmd)
    return


async def load(chess: Chess, args: []):
    if len(args) == 1:
        try:
            chess.loadRecord()
        except:
            await Gomocup.send("棋谱加载失败，未找到棋谱文件")
            return
    else:
        chess.record = []
        flag = False
        x = 0
        y = 0
        args = args[1:]
        try:
            for i in args:
                print(i)
                flag = not flag
                if flag:
                    x = int(i) - 1
                else:
                    y = int(i) - 1
                    chess.record.append([x, y])
        except:
            await Gomocup.send("棋谱加载失败，棋谱格式错误")
            return

    chess.saveImg()
    chess.start = True
    next = chess.get_next()
    await Gomocup.send("棋谱加载成功 -> {0}\n".format(next) + Message(MessageSegment.image(tempDir)))
    return


async def save(chess: Chess, args: []):
    chess.saveRecord()
    await Gomocup.send("棋谱保存成功")
    return


CommandDict['^show'] = Command(show, "显示棋盘")
CommandDict['^log'] = Command(log, "显示棋谱")
CommandDict['^easy|^normal|^hard'] = Command(choose_difficulty, "选择难度")
CommandDict['^black|^white'] = Command(choose_side, "选择黑白方")
CommandDict[r'^\d+(\s|,)\d+'] = Command(player_move, "下棋")
CommandDict['^move'] = Command(bot_move, "机器人帮我下棋")
CommandDict['^back'] = Command(back, "悔棋")
CommandDict['^help'] = Command(help, "帮助")
CommandDict['^load'] = Command(load, "加载棋谱")
CommandDict['^save'] = Command(save, "保存棋谱")


async def logic(chess: Chess, message: str):
    message = pre_command(message)
    args = message.split()
    patten = message.split(" ", 1)
    if len(patten) == 1:
        await help(chess, args)
        return
    print(args[1:])
    for i in CommandDict:
        if re.match(i, patten[1]):
            await CommandDict[i].call(chess, args[1:])
            return
    await help(chess, args)
    return


@Gomocup.handle()
async def gomocup_handle(event: MessageEvent):
    if event.message_type == "group":
        if ChessRecoder.get(event.group_id) is None:
            ChessRecoder[event.group_id] = Chess("\\" + str(event.group_id))
        chess = ChessRecoder[event.group_id]
        await logic(chess, event.get_message().extract_plain_text())

    elif event.message_type == "private":
        if ChessRecoder.get(event.user_id) is None:
            ChessRecoder[event.user_id] = Chess("\\" + str(event.user_id))
        chess = ChessRecoder[event.user_id]
        await logic(chess, event.get_message().extract_plain_text())
