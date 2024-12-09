import re


def pre_command(message)->str:
    message = message.strip() # 去除前后空格
    message = message.lower()  # 全部转为小写
    message = re.sub(',', ' ', message)  # 去除逗号
    message = re.sub(r'\s+', ' ', message)  # 合并多个空格
    return message
