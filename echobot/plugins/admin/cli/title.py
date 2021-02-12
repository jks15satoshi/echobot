"""群头衔申请 (CLI)"""
from nonebot.adapters.cqhttp import Bot, Event, GROUP
from nonebot.rule import ArgumentParser
from nonebot.typing import T_State

from .glob import admin, str_parser
from ..title import set_title, should_continue


# CLI 指令解析
parser = ArgumentParser(add_help=False)
subparsers = parser.add_subparsers(dest='subcommand')

parser_apply = subparsers.add_parser('apply')
parser_apply.add_argument('contents', type=str, nargs='?')

parser_remove = subparsers.add_parser('remove')

title = admin.shell_command('title', permission=GROUP, parser=parser)


@title.got('args')
async def handle(bot: Bot, event: Event, state: T_State) -> None:
    args = state.get('args')

    if not await should_continue(bot, event):
        await title.finish()
    elif args.subcommand == 'apply':
        if not args.contents:
            await title.finish(str_parser.parse('admin.title.failed'))
        else:
            await set_title(bot, event, args.contents)
            await title.finish(str_parser.parse('admin.title.apply_success'))
    elif args.subcommand == 'remove':
        await set_title(bot, event, '')
        await title.finish(str_parser.parse('admin.title.remove_success'))
