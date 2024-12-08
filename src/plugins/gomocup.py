import ctypes
from ctypes import c_int
import re

from nonebot import *
from PIL import Image
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment, MessageEvent
from nonebot.adapters.onebot.v11 import NoticeEvent

Gomocup = on_regex(pattern=r'^/wzq', priority=1, block=False)
root = r'D:\programingFiles\qqplugin\gomocup\src\plugins'
imglib = root + r'\imgs'
logdir = root + r'\log'
tempdir = imglib + r"\temp.png"
lib = ctypes.CDLL(root + r'\lib\bot.so', winmode=0)
offsetx = -3
offsety = -3
internal = 13.25
ChessRecoder = dict()
CommandDict = dict()

class Chess:
    def __init__(self, token: str = '\\log'):
        self.record = []
        self.start = False
        self.difficult = 1
        self.outdir = logdir + token + '.txt'
        self.recorddir = logdir + token + '.save.txt'
        self.token = token

    def check_win(self) -> bool:
        board = [[-1 for _ in range(15)] for _ in range(15)]
        for i in range(len(self.record)):
            if i % 2 == 0:
                board[self.record[i][0]][self.record[i][1]] = 0  # 玩家0（黑子）
            else:
                board[self.record[i][0]][self.record[i][1]] = 1  # 玩家1（白子）

        for i in range(15):
            for j in range(15):
                if board[i][j] != -1:  # 确保该位置有棋子
                    # 检查横向
                    if j <= 10 and all(board[i][j + k] == board[i][j] for k in range(5)):
                        return True
                    # 检查纵向
                    if i <= 10 and all(board[i + k][j] == board[i][j] for k in range(5)):
                        return True
                    # 检查斜向（左上到右下）
                    if i <= 10 and j <= 10 and all(board[i + k][j + k] == board[i][j] for k in range(5)):
                        return True
                    # 检查斜向（右上到左下）
                    if i <= 10 and j >= 4 and all(board[i + k][j - k] == board[i][j] for k in range(5)):
                        return True

        return False  # 如果没有胜利者

    def pasteChess(self, board, chess, x, y):
        board.paste(chess, (int(offsetx + x * internal), int(offsety + y * internal)), mask=chess.split()[3])

    def turnMove(self) -> []:
        c = len(self.record)
        line = c_int * 2
        data_type = line * c
        data = data_type()
        print(len(self.record))
        for i in range(len(self.record)):
            data[i][0] = c_int(self.record[i][0])
            data[i][1] = c_int(self.record[i][1])
        lib.restype = c_int
        res = lib.compute(data, c, int(self.difficult * 1000), self.outdir.encode('utf-8'))
        return [res >> 5, res & 31]

    def saveImg(self):
        # global record
        img = Image.open(imglib + r"\board.png")
        b = Image.open(imglib + r"\black.png")
        w = Image.open(imglib + r"\white.png")
        t = 0
        for i in self.record:
            t += 1
            if t % 2 == 1:
                self.pasteChess(img, b, i[0] + 1, i[1] + 1)
            else:
                self.pasteChess(img, w, i[0] + 1, i[1] + 1)
        dir = imglib + r"\temp.png"
        img.save(dir)

    def checkPosValid(self, x, y):
        if x < 0 or x > 14 or y < 0 or y > 14:
            return False
        for i in self.record:
            if i[0] == x and i[1] == y:
                return False
        return True

    def saveRecord(self):
        with open(self.recorddir, 'w', encoding='utf-8') as f:
            for i in self.record:
                f.write(str(i[0]) + " " + str(i[1]) + "\n")

    def loadRecord(self):
        with open(self.recorddir, 'r', encoding='utf-8') as f:
            for line in f:
                x, y = line.strip().split()
                self.record.append([int(x), int(y)])

    def logmessage(self):
        with open(self.outdir, 'r', encoding='utf-8') as f:
            l = f.read().split('\n')[0:-17]
            return "\n".join(l)

    async def logic(self, message: str):
        message = message.strip()
        message = re.sub(',', ' ', message)
        message = re.sub(r'\s+', ' ', message)
        args = message.split()
        patten = message.split(" ", 1)
        if len(patten) == 1:
            await help(self, args)
            return
        print(args[1:])
        for i in CommandDict:
            if re.match(i, patten[1]):
                await CommandDict[i].call(self, args[1:])
                return
        await help(self, args)
        return

class Command:
    def __init__(self,func,description: str):
        self.func = func
        self.description = description
    async def call(self,chess: Chess, args: []=None):
        await self.func(chess, args)

async def show(chess: Chess, args: []=None):
    if not chess.start:
        await Gomocup.send("游戏未开始")
        return
    chess.saveImg()
    await Gomocup.send(Message(MessageSegment.image(tempdir)))
    return

async def log(chess: Chess, args: []=None):
    dir = ""
    for i in chess.record:
        dir += str(i[0]+1) + " " + str(i[1]+1) + " "
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
        await Gomocup.send(Message(MessageSegment.image(tempdir)))
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

    await Gomocup.send("{0},{1}".format(p[0] + 1, p[1] + 1) + Message(MessageSegment.image(tempdir)))
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
    await Gomocup.send("{0},{1}".format(p[0] + 1, p[1] + 1) + Message(MessageSegment.image(tempdir)))
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
    await Gomocup.send( "悔棋成功\n" + Message(MessageSegment.image(tempdir)))

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
    await Gomocup.send("棋谱加载成功\n"+Message(MessageSegment.image(tempdir)))
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


@Gomocup.handle()
async def GomocupHandle(bot: Bot, event: MessageEvent, state: T_State):
    if event.message_type == "group":
        if ChessRecoder.get(event.group_id) is None:
            ChessRecoder[event.group_id] = Chess("\\" + str(event.group_id))
        chess = ChessRecoder[event.group_id]
        await chess.logic(event.get_message().extract_plain_text())

    elif event.message_type == "private":
        if ChessRecoder.get(event.user_id) is None:
            ChessRecoder[event.user_id] = Chess("\\" + str(event.user_id))
        chess = ChessRecoder[event.user_id]
        await chess.logic(event.get_message().extract_plain_text())
