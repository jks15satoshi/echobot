from nonebot import CommandGroup


bot = CommandGroup('bot', priority=1)

from . import feedback, reboot, title
