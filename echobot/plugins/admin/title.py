"""群头衔申请"""
from typing import Optional

import jieba.posseg as posseg
from echobot.permission import is_owner as owner
from echobot.utils import confirm_intent
from echobot.utils.segment_parser import AtSegmentParser
from nonebot import require
from nonebot.adapters.cqhttp import GROUP, Bot, Event, exception
from nonebot.log import logger
from nonebot.typing import T_State

from .glob import admin, str_parser


title = admin.on_keyword({'头衔'}, permission=GROUP)
cd = require('nonebot_plugin_cooldown').cooldown


@title.handle()
async def first_receive(bot: Bot, event: Event, state: T_State) -> None:
    if not await should_continue(bot, event):
        await title.finish()
    else:
        segment = AtSegmentParser(str(event.message))

        # 解析 at 消息段
        if (user_id := segment.get_data('qq')) and user_id.isdigit():
            state['at_userid'] = int(user_id)

        # 解析指令
        message = segment.filter_segment(any_segments=True).split('头衔')
        words = posseg.cut(message[0])

        for word, flag in words:
            if flag == 'v':
                action = word

        if action in ('申请', '设置', '设定', '应用', '修改', '更改', '变更'):
            state['action'] = 'apply'
            if (contents := message[1].strip()):
                state['contents'] = contents
        elif action in ('移除', '删除', '撤销', '取消'):
            state['action'] = 'remove'
            state['contents'] = ''
        else:
            await title.reject(str_parser.parse('admin.title.action_rejected'))


async def contents_parse(bot: Bot, event: Event, state: T_State) -> None:
    state[state['_current_key']] = str(event.raw_message)


@title.got('contents', str_parser.parse('admin.title.contents_prompt'),
           args_parser=contents_parse)
async def handle(bot: Bot, event: Event, state: T_State) -> None:
    segment = AtSegmentParser(state.get('contents').strip())

    action = state.get('action')
    contents = segment.filter_segment(any_segments=True)
    userid = (int(segment.get_data('qq')) if segment.get_data('qq')
              else state.get('at_userid'))

    # 检查用户权限验证 at 成员有效性
    if (userid and userid != event.user_id
            and event.sender.role != 'admin'):
        await title.reject(str_parser.parse('admin.title.permission_rejected'))
    # 申请群头衔
    elif action == 'apply':
        if not contents:
            await title.reject(str_parser.parse(
                'admin.title.apply_invalid_rejected'))
        elif confirm_intent(contents) == 'decline':
            await title.finish(str_parser.parse('admin.title.apply_cancel'))
        elif (length := len(bytes(contents, encoding='utf-8'))) > 18:
            await title.reject(str_parser.parse(
                'admin.title.apply_length_rejected', length=length))
        else:
            await set_title(bot, event, contents, user=userid)
            await title.finish(str_parser.parse('admin.title.apply_success'))
    # 移除群头衔
    elif action == 'remove':
        await set_title(bot, event, '', user=userid)
        await title.finish(str_parser.parse('admin.title.remove_success'))


async def set_title(bot: Bot, event: Event, contents: str, /,
                    user: Optional[int] = None) -> None:
    group_id = event.group_id
    user_id = user if user else event.user_id

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
        if event.sender.role == 'admin':
            return True
        else:
            msg = str_parser.parse('admin.title.on_cooldown',
                                   time=cd.time_format(info.get('remaining'),
                                                       preset='zh'))
            await bot.send(event, msg)

    return False
