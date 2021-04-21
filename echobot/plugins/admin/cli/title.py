"""群头衔申请 (CLI)"""
from typing import Union

from echobot.utils.segment_parser import AtSegmentParser
from nonebot.adapters.cqhttp import GROUP, Bot, Event
from nonebot.rule import ArgumentParser
from nonebot.typing import T_State

from ..title import set_title, should_continue
from .glob import admin, str_parser


# CLI 指令解析
parser = ArgumentParser(add_help=False)
subparsers = parser.add_subparsers(dest='subcommand')

parser_apply = subparsers.add_parser('apply')
parser_apply.add_argument('contents', type=str, nargs='?')
parser_apply.add_argument('--user', '-u', type=str, nargs='?', const='self')

parser_remove = subparsers.add_parser('remove')
parser_remove.add_argument('--user', '-u', type=str, nargs='?', const='self')


title = admin.shell_command('title', permission=GROUP, parser=parser)


@title.handle()
async def handle(bot: Bot, event: Event, state: T_State) -> None:
    args = state.get('args')

    user_id = event.user_id
    if args.user:
        if isinstance(args.user, str):
            user_id = (AtSegmentParser(args.user).get_data('qq')
                       if args.user != 'self' else event.self_id)
        else:
            user_id = args.user

    if not await should_continue(bot, event):
        await title.finish()
    elif user_id != event.user_id and event.sender.role != 'admin':
        await title.finish(str_parser.parse('admin.title.permission_denied'))
    elif args.subcommand == 'apply':
        if not args.contents:
            await title.finish(str_parser.parse(
                'admin.title.apply_invalid_failed'))
        else:
            await set_title(bot, event, args.contents, user_id)
            await title.finish(str_parser.parse('admin.title.apply_success'))
    elif args.subcommand == 'remove':
        await set_title(bot, event, '', user_id)
        await title.finish(str_parser.parse('admin.title.remove_success'))
