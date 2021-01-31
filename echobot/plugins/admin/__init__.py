from nonebot import CommandGroup, require


bot = CommandGroup('bot', priority=1)
str_parser = require('nonebot_plugin_styledstr').parser

from . import feedback, reboot, title
