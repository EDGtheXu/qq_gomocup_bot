import ctypes
from ctypes import c_int

from PIL import Image

from gomocupbot.config import cfg as cfg

root = cfg.project_root
logDir = root + r'\logs'
imgLib = root + r'\imgs'
boardDir = imgLib + r"\board.png"
tempDir = imgLib + r"\temp.png"
blackDir = imgLib + r"\black.png"
whiteDir = imgLib + r"\white.png"


lib = ctypes.CDLL(root + r'\lib\bot.so', winmode=0)
offsetX = -3
offsetY = -3
internal = 13.25
class Chess:
    def __init__(self, token: str = '\\log'):
        self.record = []
        self.start = False
        self.difficult = 1
        self.outDir = logDir + token + '.txt'
        self.recordDir = logDir + token + '.save.txt'
        self.token = token

    def get_next(self)->str:
        if len(self.record) % 2 == 0:
            return  '黑'
        else:
            return  '白'

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
        board.paste(chess, (int(offsetX + x * internal), int(offsetY + y * internal)), mask=chess.split()[3])

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
        res = lib.compute(data, c, int(self.difficult * 1000), self.outDir.encode('utf-8'))
        return [res >> 5, res & 31]

    def saveImg(self):
        img = Image.open(boardDir)
        b = Image.open(blackDir)
        w = Image.open(whiteDir)
        t = 0
        for i in self.record:
            t += 1
            if t % 2 == 1:
                self.pasteChess(img, b, i[0] + 1, i[1] + 1)
            else:
                self.pasteChess(img, w, i[0] + 1, i[1] + 1)
        dir = imgLib + r"\temp.png"
        img.save(dir)

    def checkPosValid(self, x, y):
        if x < 0 or x > 14 or y < 0 or y > 14:
            return False
        for i in self.record:
            if i[0] == x and i[1] == y:
                return False
        return True

    def saveRecord(self):
        with open(self.recordDir, 'w', encoding='utf-8') as f:
            for i in self.record:
                f.write(str(i[0]) + " " + str(i[1]) + "\n")

    def loadRecord(self):
        with open(self.recordDir, 'r', encoding='utf-8') as f:
            for line in f:
                x, y = line.strip().split()
                self.record.append([int(x), int(y)])

    def logmessage(self):
        with open(self.outDir, 'r', encoding='utf-8') as f:
            l = f.read().split('\n')[0:-17]
            return "\n".join(l)

class Command:
    def __init__(self,func,description: str):
        self.func = func
        self.description = description
    async def call(self,chess: Chess, args: []=None):
        await self.func(chess, args)