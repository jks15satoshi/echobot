"""包全局变量"""
from nonebot import CommandGroup

from .. import glob


bot = CommandGroup('bot', priority=1)
str_parser = glob.str_parser
