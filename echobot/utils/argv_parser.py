from typing import List


def argv_parse(command: str) -> List[str]:
    '''
    将指令参数拆分为参数序列。

    参数:
    - `command: str`：指令字符串。

    返回:
    - `List[str]`：参数序列。
    '''
    argv = []
    stripped = command.strip()
    if stripped:
        argv = stripped.split(' ')

    return argv
