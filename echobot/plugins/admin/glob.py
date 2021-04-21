"""包全局变量"""
from nonebot import MatcherGroup, require
from nonebot.rule import to_me


admin = MatcherGroup(rule=to_me(), priority=1)
str_parser = require('nonebot_plugin_styledstr').parser
