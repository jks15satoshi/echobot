"""用户反馈 (CLI)"""
from nonebot.adapters.cqhttp import Bot, Event
from nonebot.rule import ArgumentParser
from nonebot.typing import T_State

from .glob import bot, str_parser
from ..feedback import send_report


# CLI 指令解析
parser = ArgumentParser(add_help=False)
parser.add_argument('contents', type=str, nargs='?')

feedback = bot.shell_command('feedback', parser=parser)


@feedback.handle()
async def handle(bot: Bot, event: Event, state: T_State) -> None:
    if (args := state.get('args')):
        if not args.contents:
            await feedback.finish(str_parser.parse('bot.feedback.failed'))
        else:
            await send_report(bot, event, args.contents)
            await feedback.finish(str_parser.parse('bot.feedback.finish'))
