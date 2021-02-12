"""群头衔申请"""
from echobot.permission import is_owner as owner
from echobot.utils import confirm_intent
from nonebot import require
from nonebot.adapters.cqhttp import GROUP, Bot, Event, exception
from nonebot.log import logger
from nonebot.typing import T_State

from .glob import admin, str_parser


title = admin.on_keyword({'头衔'}, permission=GROUP)

cd = require('nonebot_plugin_cooldown').cooldown


# 一般指令事件处理
@title.handle()
async def first_receive(bot: Bot, event: Event, state: T_State) -> None:
    message = str(event.message).split('头衔')
    action = message[0]
    contents = message[1].strip()

    if not await should_continue(bot, event):
        await title.finish()
    elif action == '申请':
        if contents:
            state['contents'] = contents
    elif action == '移除':
        await set_title(bot, event, '')
        await title.finish(str_parser.parse('admin.title.remove_success'))


@title.got('contents', str_parser.parse('admin.title.prompt'))
async def handle(bot: Bot, event: Event, state: T_State) -> None:
    contents = state.get('contents').strip()

    if not contents:
        await title.reject(str_parser.parse('admin.title.invalid'))
    elif confirm_intent(contents) == 'decline':
        await title.reject(str_parser.parse('admin.title.cancel'))
    else:
        await set_title(bot, event, contents)
        await title.finish(str_parser.parse('admin.title.apply_success'))


async def set_title(bot: Bot, event: Event, contents: str) -> None:
    group_id = event.group_id
    user_id = event.user_id
    try:
        await bot.set_group_special_title(group_id=group_id, user_id=user_id,
                                          special_title=contents)
        if contents:
            cd.set_event('admin.title', 86400, group=group_id, user=user_id)
    except (exception.NetworkError, exception.ActionFailed) as err:
        logger.error(err)
        await bot.send(event, str_parser.parse('admin.title.on_err'))


async def should_continue(bot: Bot, event: Event) -> bool:
    info = cd.get_event('admin.title', group=event.group_id,
                        user=event.user_id)

    is_owner = await owner(bot, event)
    is_cooled_down = not info.get('status')

    if is_owner and is_cooled_down:
        return True
    elif is_owner:
        msg = str_parser.parse('admin.title.on_cooldown',
                               time=cd.time_format(info.get('remaining'),
                                                   preset='zh'))
        await bot.send(event, msg)

    return False
