"""包全局变量"""
from nonebot import CommandGroup

from .. import glob


admin = CommandGroup('admin', priority=1)
str_parser = glob.str_parser
