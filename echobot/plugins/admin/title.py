'''
申请群头衔
'''
import argparse

from echobot.permission import owner
from echobot.utils import argv_parse, confirm_intent
from nonebot import on_keyword
from nonebot.adapters.cqhttp import GROUP, Bot, Event, exception
from nonebot.log import logger
from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot_plugin_cooldown import cooldown
from nonebot_plugin_cooldown.extra import time_format

from . import bot, str_parser


title = on_keyword({'头衔'}, rule=to_me(), priority=1, permission=GROUP)
title_cli = bot.command('title', permission=GROUP)


# 一般指令事件处理
@title.handle()
async def first_receive(bot: Bot, event: Event, state: T_State) -> None:
    message = str(event.message).split('头衔')
    action = message[0]
    contents = message[1].strip()

    if not await _should_continue(bot, event):
        await title.finish()
    elif action == '申请':
        if contents:
            state['contents'] = contents
    elif action == '移除':
        await _set_title('', bot, event)
        await title.finish(str_parser.parse('admin.title.remove_success'))


@title.got('contents', str_parser.parse('admin.title.prompt'))
async def handle(bot: Bot, event: Event, state: T_State) -> None:
    contents = state.get('contents').strip()

    if not contents:
        await title.reject(str_parser.parse('admin.title.invalid'))
    elif confirm_intent(contents) == 'decline':
        await title.reject(str_parser.parse('admin.title.cancel'))
    else:
        await _set_title(contents, bot, event)
        await title.finish(str_parser.parse('admin.title.apply_success'))


# CLI 指令事件处理
@title_cli.handle()
async def cli_first_receive(bot: Bot, event: Event) -> None:
    argv = argv_parse(str(event.message))

    parser = argparse.ArgumentParser(add_help=False)
    subparsers = parser.add_subparsers(dest='subcommand')

    parser_apply = subparsers.add_parser('apply')
    parser_apply.add_argument('contents', type=str, nargs='?')

    subparsers.add_parser('remove')

    args = parser.parse_args(argv)

    if not await _should_continue(bot, event):
        await title_cli.finish()
    elif args.subcommand == 'apply':
        if not args.contents:
            await title_cli.finish(str_parser.parse('admin.title.failed'))
        else:
            await _set_title(args.contents, bot, event)
            await title_cli.finish(str_parser.parse(
                'admin.title.apply_success'))
    elif args.subcommand == 'remove':
        await _set_title('', bot, event)
        await title_cli.finish(str_parser.parse('admin.title.remove_success'))


async def _should_continue(bot: Bot, event: Event) -> bool:
    info = cooldown.get_event('admin.title', group=event.group_id,
                              user=event.user_id)

    is_owner = await owner(bot, event)
    is_cooled_down = not info.get('status')

    if is_owner and is_cooled_down:
        return True
    elif is_owner:
        msg = str_parser.parse('admin.title.on_cooldown',
                               time=time_format(info.get('remaining'),
                                                format='zh'))
        await bot.send(event, msg)

    return False


async def _set_title(contents: str, bot: Bot, event: Event) -> None:
    try:
        group_id = event.group_id
        user_id = event.user_id
        await bot.set_group_special_title(group_id=group_id, user_id=user_id,
                                          special_title=contents)
        if contents:
            cooldown.set_event('admin.title', 86400, group=event.group_id,
                               user=event.user_id)
    except (exception.NetworkError, exception.ActionFailed) as err:
        logger.error(err)
        await bot.send(str_parser.parse('admin.title.on_err'))
